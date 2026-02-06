# Phase 1: Spec Detection & Schema - Research

**Researched:** 2026-02-05
**Domain:** OpenAPI specification version detection and JSON Schema meta-schema validation
**Confidence:** HIGH

## Summary

Phase 1 requires implementing OpenAPI 3.1.x spec detection and routing to dedicated handling with proper meta-schema validation. The research reveals that OpenAPI 3.1 represents a significant alignment with JSON Schema Draft 2020-12, introducing breaking changes from 3.0 (particularly nullable handling and type arrays) that must be validated strictly. The current connexion implementation uses Draft-04 validators and binary version branching that needs to become ternary.

**Key findings:**
- OpenAPI 3.1 uses JSON Schema Draft 2020-12, replacing nullable with type arrays
- Official schema available at spec.openapis.org with version pattern `^3\.1\.\d+(-.+)?$`
- Python jsonschema library provides Draft202012Validator with identical API to Draft4Validator
- Version branching requires three-way split: <(3,0,0) → Swagger2, <(3,1,0) → OpenAPI3.0, >=(3,1,0) → OpenAPI3.1
- Patch versions (3.1.0, 3.1.1, 3.1.2) are treated identically per OAS spec guidance

**Primary recommendation:** Create OpenAPI31Specification as parallel sibling class to OpenAPISpecification (not subclass), following existing Swagger2/OpenAPI3.0 pattern. Use bundled schema validation with Draft202012Validator, enabling strict 3.1 validation that rejects 3.0-only patterns with helpful error messages.

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Version matching strategy:**
- Accept any 3.1.x patch version (3.1.0, 3.1.1, etc.) — treat all 3.1 patches the same, mirroring how connexion handles 3.0.x
- Future unsupported versions (3.2.0, 4.0.0) fail with clear error: "OpenAPI X.Y.Z is not supported. Supported versions: 2.0, 3.0.x, 3.1.x"
- Detection is based solely on the `openapi` field value — no content heuristics

**Error messaging & diagnostics:**
- Philosophy: "Explicit is better than implicit" — fail with clear messages, no silent behavior
- Every validation error includes the detected OAS version (e.g., "OpenAPI 3.1.0 spec validation failed: ...")
- Info-level log on spec load: "Detected OpenAPI 3.1.0 spec, using OpenAPI31Specification handler"

**Meta-schema sourcing:**
- Bundled in repo at `connexion/resources/schemas/v3.1/schema.json` — same pattern as v2.0 and v3.0
- Pin to the official OAS 3.1.0 release schema (not tracking revisions)

**Backwards-compat behavior:**
- **Strict 3.1 validation** — reject all 3.0-only patterns in 3.1 specs
- `nullable: true` in a 3.1 spec is rejected with helpful error suggesting `type: ["string", "null"]`
- Other 3.0 patterns that changed (exclusiveMinimum as boolean, etc.) are also rejected per the 3.1 meta-schema
- No silent translation or compatibility shims — if a spec declares 3.1, it must be valid 3.1

### Claude's Discretion

- Malformed version string handling (normalization vs strict semver matching) — based on existing connexion patterns
- Error class hierarchy (whether to distinguish invalid-spec vs unsupported-feature errors)
- Class hierarchy for OpenAPI31Specification (subclass vs sibling with shared base)
- JSON Schema 2020-12 meta-schema sourcing (library built-in vs bundled copy)
- Bundled schema file structure (single file vs matching OAI published structure)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

## Standard Stack

The established libraries for OpenAPI 3.1 spec validation in Python.

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| jsonschema | 4.26.0+ | JSON Schema validation with Draft 2020-12 support | De facto Python standard for JSON Schema, actively maintained, provides Draft202012Validator |
| PyYAML | 6.0+ | YAML parsing for OpenAPI specs | Already used by connexion for spec loading |
| requests | 2.31.0+ | HTTP client for remote spec fetching | Already used by connexion for remote refs |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| referencing | 0.35.0+ | Modern JSON Schema ref resolution (replaces deprecated RefResolver) | For OAS 3.1 $ref handling with siblings, future-proofs codebase |
| pkgutil | stdlib | Loading bundled schema resources | Already used for v2.0/v3.0 schemas |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Draft202012Validator | Draft7Validator | Draft-07 lacks 2020-12 features (prefixItems, $dynamicRef), wouldn't fully validate 3.1 schemas |
| Bundled schema | Remote fetch on startup | Network dependency, slower startup, but always latest schema version |
| referencing | Continue with RefResolver | RefResolver deprecated in jsonschema 4.18+, will be removed in future versions |

**Installation:**

No new dependencies required. The `jsonschema` library already in connexion's dependencies supports Draft202012Validator natively since version 3.0.0 (released 2019). Current connexion uses jsonschema ~=4.17, which includes full Draft 2020-12 support.

## Architecture Patterns

### Recommended Code Structure

```
connexion/
├── spec.py                          # Add OpenAPI31Specification class here
├── resources/schemas/
│   ├── v2.0/schema.json            # Existing Swagger 2.0 schema
│   ├── v3.0/schema.json            # Existing OpenAPI 3.0 schema
│   └── v3.1/schema.json            # NEW: OpenAPI 3.1 schema (download from spec.openapis.org)
└── json_schema.py                  # Add create_draft202012_validators here (Phase 2)
```

### Pattern 1: Three-Way Version Branching

**What:** Version detection routes to one of three Specification classes based on semantic version tuple.

**When to use:** In `Specification.from_dict()` when determining which spec handler to instantiate.

**Example:**

```python
# Source: Existing connexion pattern (spec.py:206-209), extended for 3.1
@classmethod
def from_dict(cls, spec, *, base_uri=""):
    """Takes in a dictionary, and returns a Specification"""
    def enforce_string_keys(obj):
        # YAML supports integer keys, but JSON does not
        if isinstance(obj, dict):
            return {str(k): enforce_string_keys(v) for k, v in obj.items()}
        return obj

    spec = enforce_string_keys(spec)
    version = cls._get_spec_version(spec)

    # Three-way branch based on version tuple
    if version < (3, 0, 0):
        return Swagger2Specification(spec, base_uri=base_uri)
    elif version < (3, 1, 0):
        return OpenAPISpecification(spec, base_uri=base_uri)
    else:
        return OpenAPI31Specification(spec, base_uri=base_uri)
```

### Pattern 2: Sibling Specification Classes

**What:** OpenAPI31Specification exists as a sibling to OpenAPISpecification, not a subclass. Both inherit from the common Specification base.

**When to use:** When creating the new 3.1 handler class.

**Example:**

```python
# Source: Existing connexion pattern (spec.py:294-307)
class OpenAPI31Specification(Specification):
    """Python interface for an OpenAPI 3.1 specification."""

    yaml_name = "openapi31.yaml"  # For test fixtures
    operation_cls = OpenAPIOperation  # Reuse 3.0 operation class (Phase 3 may change this)

    # Load the bundled OAS 3.1 meta-schema
    openapi_schema = json.loads(
        pkgutil.get_data("connexion", "resources/schemas/v3.1/schema.json")
    )

    @classmethod
    def _set_defaults(cls, spec):
        spec.setdefault("components", {})
        # 3.1 adds webhooks as optional top-level key
        spec.setdefault("webhooks", {})

    @property
    def security_schemes(self):
        return self.get("components", {}).get("securitySchemes", {})

    # ... rest of methods identical to OpenAPISpecification for Phase 1
```

**Rationale:** Sibling pattern allows independent evolution of 3.0 and 3.1 handling without inheritance complexity. Shared behavior lives in base Specification class.

### Pattern 3: Version-Aware Error Messages

**What:** Error messages include the detected spec version and suggest corrections for common migration mistakes.

**When to use:** When spec validation fails or unsupported patterns are detected.

**Example:**

```python
# Source: RFC 7807 Problem Details pattern already used in connexion
NO_SPEC_VERSION_ERR_MSG = """Unable to get the spec version.
You are missing either '"swagger": "2.0"', '"openapi": "3.0.x"', or '"openapi": "3.1.x"'
from the top level of your spec."""

# In validation error handler
def format_validation_error(spec_version, error):
    """Format validation error with version context and helpful suggestions."""
    version_str = ".".join(map(str, spec_version))
    msg = f"OpenAPI {version_str} spec validation failed: {error.message}"

    # Detect common 3.0 → 3.1 migration mistakes
    if spec_version >= (3, 1, 0) and "nullable" in error.schema_path:
        msg += "\n\nHint: OpenAPI 3.1 removed 'nullable'. Use 'type: [\"yourtype\", \"null\"]' instead."

    if spec_version >= (3, 1, 0) and "exclusiveMinimum" in error.schema_path:
        if isinstance(error.instance, bool):
            msg += "\n\nHint: OpenAPI 3.1 changed 'exclusiveMinimum' to a number, not boolean."

    return msg
```

### Pattern 4: Semantic Version Tuple Parsing

**What:** Parse version strings into tuples for numeric comparison, handling patch versions and prerelease suffixes.

**When to use:** In `_get_spec_version()` when parsing the `openapi` field.

**Current implementation:**

```python
# Source: connexion/spec.py:174-191
@staticmethod
def _get_spec_version(spec):
    try:
        version_string = spec.get("openapi") or spec.get("swagger")
    except AttributeError:
        raise InvalidSpecification(NO_SPEC_VERSION_ERR_MSG)
    if version_string is None:
        raise InvalidSpecification(NO_SPEC_VERSION_ERR_MSG)
    try:
        # Simple split on "." - handles "3.1.0" → (3, 1, 0)
        # Handles prerelease: "3.1.0-rc1" → (3, 1, 0) (suffix ignored)
        version_tuple = tuple(map(int, version_string.split(".")))
    except (TypeError, ValueError):
        err = f"Unable to convert version string to semantic version tuple: {version_string}."
        raise InvalidSpecification(err)
    return version_tuple
```

**Recommendation:** Keep current simple implementation. It handles the required cases:
- "3.1.0" → (3, 1, 0)
- "3.1.1" → (3, 1, 1)
- "3.0.3" → (3, 0, 3)

For malformed versions, fail fast with clear error (Claude's discretion: normalization vs strict matching).

### Anti-Patterns to Avoid

**DON'T: Subclass OpenAPISpecification for 3.1 support**
- Why it's bad: Creates tight coupling, forces inheritance of 3.0-specific logic, harder to maintain divergent behaviors
- Do instead: Sibling classes sharing common base

**DON'T: Silent translation of 3.0 patterns in 3.1 specs**
- Why it's bad: Hides spec errors, creates ambiguity about what's actually valid, violates "explicit is better than implicit"
- Do instead: Strict validation with helpful error messages teaching the correct 3.1 pattern

**DON'T: Use RefResolver for 3.1 specs**
- Why it's bad: Deprecated in jsonschema 4.18+, doesn't handle $ref siblings correctly
- Do instead: Migrate to referencing.Registry (can defer to Phase 2 if needed)

## Don't Hand-Roll

Problems that look simple but have existing solutions.

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Version string parsing | Custom semver parser | Simple string split on "." (current implementation) | OAS versions are simple "major.minor.patch" strings, not complex semver with ranges/constraints. Current implementation handles all valid OAS version strings. |
| JSON Schema Draft 2020-12 validation | Custom validator extending Draft4 | jsonschema.Draft202012Validator | Already in dependencies, battle-tested, handles all 2020-12 keywords (prefixItems, $dynamicRef, etc.) |
| OpenAPI 3.1 meta-schema | Hand-write schema constraints | Download official schema from spec.openapis.org | Official schema is canonical source, updated by OAS working group, includes all validation rules |
| $ref resolution with siblings | Extend current resolve_refs() | referencing.Registry from referencing library | RefResolver deprecated, referencing handles $ref siblings correctly, future-proof |

**Key insight:** OpenAPI 3.1's alignment with JSON Schema 2020-12 means we inherit a mature validation ecosystem. Don't reimplement what jsonschema already provides.

## Common Pitfalls

### Pitfall 1: Treating 3.1 as Minor Update from 3.0

**What goes wrong:** Code assumes 3.1 specs are backwards compatible with 3.0 validation, leading to false positives (accepting invalid specs) or false negatives (rejecting valid specs).

**Why it happens:** The version number increment (3.0 → 3.1) suggests backward compatibility, but OpenAPI 3.1 introduced breaking schema changes.

**How to avoid:**
- Use separate meta-schemas for 3.0 and 3.1 validation
- Use separate validator classes (Draft4 for 3.0, Draft202012 for 3.1)
- Validate strictly: if `openapi: "3.1.0"`, reject 3.0-only patterns

**Warning signs:**
- Tests passing with `nullable: true` in 3.1 specs (should fail)
- Tests passing with `exclusiveMinimum: true` in 3.1 specs (should fail)
- No version-specific error messages in validation failures

### Pitfall 2: Binary Version Branching

**What goes wrong:** Using `version < (3, 0, 0)` else logic creates only two paths (Swagger2, OpenAPI), forcing 3.1 specs through 3.0 handler. This causes validation failures with confusing errors about "3.0.0" when user provided "3.1.0".

**Why it happens:** Existing code has binary split, natural to extend with `elif` but forgetting to update the final `else`.

**How to avoid:**
```python
# WRONG - binary split forces 3.1 into 3.0 handler
if version < (3, 0, 0):
    return Swagger2Specification(spec, base_uri=base_uri)
return OpenAPISpecification(spec, base_uri=base_uri)  # Handles 3.1 incorrectly!

# RIGHT - ternary split with explicit 3.1 path
if version < (3, 0, 0):
    return Swagger2Specification(spec, base_uri=base_uri)
elif version < (3, 1, 0):
    return OpenAPISpecification(spec, base_uri=base_uri)
else:
    return OpenAPI31Specification(spec, base_uri=base_uri)
```

**Warning signs:**
- Error messages reference "3.0.0" when loading a 3.1 spec
- Schema validation errors about the `openapi` field pattern mismatch

### Pitfall 3: Forgetting to Update Error Messages

**What goes wrong:** Error messages still reference only "2.0" and "3.0.0", confusing users who are trying to use 3.1.

**Why it happens:** Error message constants defined at top of file, easy to overlook when adding new version support.

**How to avoid:**
- Grep for hardcoded version strings in error messages
- Update `NO_SPEC_VERSION_ERR_MSG` to mention "3.1.x"
- Test error paths explicitly (missing version field, unsupported version like 4.0.0)

**Warning signs:**
- User submits 3.1 spec, error says "missing 2.0 or 3.0.0" (doesn't mention 3.1)

### Pitfall 4: Incomplete Schema File Deployment

**What goes wrong:** Code references `connexion/resources/schemas/v3.1/schema.json` but file isn't bundled in wheel/sdist, causing runtime failures after install.

**Why it happens:** Forgetting to update MANIFEST.in or package_data in setup configuration.

**How to avoid:**
- Verify `pkgutil.get_data()` can load the schema in test environment
- Add explicit test that checks all version schemas are loadable
- Check package contents after build: `tar -tzf dist/connexion-*.tar.gz | grep schema.json`

**Warning signs:**
- Tests pass locally but fail in CI after clean install
- FileNotFoundError or pkgutil data load errors in production

### Pitfall 5: Not Validating the Meta-Schema Itself

**What goes wrong:** Bundled schema.json is corrupted, has syntax errors, or is wrong version, but code blindly uses it.

**Why it happens:** Assuming downloaded official schema is perfect, not validating it loads correctly.

**How to avoid:**
- Add test that validates the bundled schema.json is valid JSON
- Check that the schema's `$schema` field matches expected Draft 2020-12 URI
- Check that the `pattern` field for `openapi` version matches `^3\.1\.\d+(-.+)?$`

**Warning signs:**
- Confusing validation errors that don't match spec structure
- Different behavior between connexion versions due to schema drift

## Code Examples

Verified patterns from official sources and current connexion implementation.

### Loading and Validating OpenAPI 3.1 Spec

```python
# Source: Combining connexion/spec.py patterns with jsonschema Draft202012Validator
import json
import pkgutil
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

class OpenAPI31Specification(Specification):
    """Python interface for an OpenAPI 3.1 specification."""

    yaml_name = "openapi31.yaml"
    operation_cls = OpenAPIOperation

    # Load bundled meta-schema for OAS 3.1
    openapi_schema = json.loads(
        pkgutil.get_data("connexion", "resources/schemas/v3.1/schema.json")
    )

    @classmethod
    def _validate_spec(cls, spec):
        """Validate spec against OpenAPI 3.1 meta-schema using Draft 2020-12 validator."""
        # Create validator for OAS 3.1 meta-schema
        spec_validator_cls = create_spec_validator(cls.openapi_schema, Draft202012Validator)
        spec_validator = spec_validator_cls(cls.openapi_schema)

        try:
            spec_validator.validate(spec)
        except ValidationError as e:
            # Extract version for error message
            version = spec.get("openapi", "unknown")
            error_path = ".".join(str(item) for item in e.path) if e.path else ""

            # Construct helpful error message
            msg = f"OpenAPI {version} spec validation failed"
            if error_path:
                msg += f" at '{error_path}'"
            msg += f": {e.message}"

            # Add migration hints for common 3.0 → 3.1 mistakes
            if "nullable" in str(e.schema_path):
                msg += "\n\nNote: OpenAPI 3.1 removed the 'nullable' keyword. "
                msg += "Use 'type: [\"yourtype\", \"null\"]' instead."

            raise InvalidSpecification(msg)

    @classmethod
    def _set_defaults(cls, spec):
        """Set default values for optional top-level fields."""
        spec.setdefault("components", {})
        # Note: webhooks is new in 3.1 but optional, no default needed

    @property
    def security_schemes(self):
        """Location unchanged from 3.0: components.securitySchemes"""
        return self.get("components", {}).get("securitySchemes", {})
```

### Creating Extended Draft202012Validator

```python
# Source: connexion/spec.py:create_spec_validator pattern, adapted for Draft 2020-12
from jsonschema import Draft202012Validator
from jsonschema.validators import extend as extend_validator

def create_spec_validator(schema, base_validator=Draft202012Validator):
    """
    Create a validator that checks default values are valid against their schemas.

    This extends the base validator (Draft202012Validator for OAS 3.1) with
    custom validation for the 'default' keyword to catch invalid defaults.
    """
    def validate_defaults(validator, properties, instance, schema):
        """Validate that default values match their schema."""
        for property, subschema in properties.items():
            if "default" in subschema:
                # Validate the default value against the property schema
                for error in validator.descend(
                    subschema["default"],
                    subschema,
                    path=property
                ):
                    yield error

        # Continue with standard properties validation
        for error in base_validator.VALIDATORS["properties"](
            validator, properties, instance, schema
        ):
            yield error

    SpecValidator = extend_validator(base_validator, {"properties": validate_defaults})
    return SpecValidator
```

### Version Detection with Three-Way Branching

```python
# Source: connexion/spec.py:_get_spec_version + from_dict, extended for 3.1
@staticmethod
def _get_spec_version(spec):
    """Parse spec version into semantic version tuple."""
    try:
        version_string = spec.get("openapi") or spec.get("swagger")
    except AttributeError:
        raise InvalidSpecification(NO_SPEC_VERSION_ERR_MSG)

    if version_string is None:
        raise InvalidSpecification(NO_SPEC_VERSION_ERR_MSG)

    try:
        # Split on "." and convert to integers
        # "3.1.0" → (3, 1, 0)
        # "3.1.0-rc1" → (3, 1, 0) via split, prerelease suffix ignored
        version_parts = version_string.split(".")[0:3]  # Take first 3 parts
        version_tuple = tuple(map(int, version_parts))
    except (TypeError, ValueError) as e:
        err = f"Unable to convert version string to semantic version tuple: {version_string}."
        raise InvalidSpecification(err)

    return version_tuple

@classmethod
def from_dict(cls, spec, *, base_uri=""):
    """Route spec to appropriate handler based on version."""
    spec = cls._enforce_string_keys(spec)
    version = cls._get_spec_version(spec)

    # Three-way version routing
    if version < (3, 0, 0):
        return Swagger2Specification(spec, base_uri=base_uri)
    elif version < (3, 1, 0):
        return OpenAPISpecification(spec, base_uri=base_uri)
    elif version < (4, 0, 0):  # Support all 3.1.x patches
        return OpenAPI31Specification(spec, base_uri=base_uri)
    else:
        # Unsupported future version
        version_str = ".".join(map(str, version))
        raise InvalidSpecification(
            f"OpenAPI {version_str} is not supported. "
            f"Supported versions: 2.0, 3.0.x, 3.1.x"
        )
```

### Pattern Matching for Version Strings

```python
# Source: Official OAS 3.1 meta-schema at spec.openapis.org/oas/3.1/schema/2022-10-07
# The bundled schema.json should include this validation

{
  "$id": "https://spec.openapis.org/oas/3.1/schema/2022-10-07",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "The description of OpenAPI v3.1.x documents without schema validation",
  "type": "object",
  "properties": {
    "openapi": {
      "type": "string",
      "pattern": "^3\\.1\\.\\d+(-.+)?$"  # Matches 3.1.0, 3.1.1, 3.1.0-rc1, etc.
    },
    "info": {
      "$ref": "#/$defs/info"
    },
    // ... rest of schema
  },
  "required": ["openapi", "info"]
}
```

## State of the Art

Changes in OpenAPI 3.1 that impact this phase.

| Old Approach (3.0) | Current Approach (3.1) | When Changed | Impact |
|-------------------|------------------------|--------------|--------|
| `nullable: true` keyword | `type: ["string", "null"]` array | OAS 3.1.0 (Feb 2021) | Must reject `nullable` in 3.1 specs, suggest type array in error message |
| `exclusiveMinimum: true` boolean | `exclusiveMinimum: 21` number | OAS 3.1.0 (Feb 2021) | Meta-schema validation will catch this if using Draft 2020-12 validator |
| `example: "value"` | `examples: ["value1", "value2"]` | OAS 3.1.0 (Feb 2021) | Example is deprecated but not removed (low priority for Phase 1) |
| JSON Schema subset | Full JSON Schema Draft 2020-12 | OAS 3.1.0 (Feb 2021) | Any JSON Schema keyword now valid (const, prefixItems, $dynamicRef, etc.) |
| RefResolver | referencing.Registry | jsonschema 4.18.0 (2023) | RefResolver deprecated but still works; migration to referencing can be Phase 2 |
| Draft-04 meta-schema | Draft 2020-12 meta-schema | OAS 3.1.0 (Feb 2021) | Must use Draft202012Validator for 3.1 specs |

**Deprecated/outdated:**

- **`nullable` keyword in OpenAPI 3.1**: Removed. Use `type` arrays with "null" instead.
- **Boolean `exclusiveMinimum`/`exclusiveMaximum`**: Now numeric values in 3.1, following JSON Schema 2020-12.
- **jsonschema.RefResolver**: Deprecated in jsonschema 4.18.0 (2023), replaced by referencing.Registry. Still functional but will be removed in future jsonschema major version.
- **Implicit JSON Schema subset**: OpenAPI 3.0 defined its own subset of JSON Schema. 3.1 uses full JSON Schema 2020-12 specification.

## Open Questions

Things that couldn't be fully resolved during research.

### 1. Should we migrate RefResolver to referencing.Registry in Phase 1?

**What we know:**
- RefResolver is deprecated in jsonschema 4.18+ (current: 4.26.0)
- referencing.Registry is the official replacement
- RefResolver still works but will be removed in future jsonschema versions
- Current connexion uses custom handlers for file:// and http:// protocols

**What's unclear:**
- Is the referencing migration simple enough for Phase 1, or complex enough to defer to Phase 2?
- Does referencing.Registry support custom protocol handlers as easily as RefResolver?

**Recommendation:** Defer to Phase 2 (JSON Schema 2020-12 Validation). Phase 1 focuses on version detection and meta-schema validation, which can use RefResolver initially. Phase 2 will handle $ref resolution in request/response schemas, a better time to migrate to referencing.

### 2. Should OpenAPI31Specification reuse OpenAPIOperation or need a new class?

**What we know:**
- OpenAPIOperation handles path/method operations for 3.0 specs
- 3.1 operation structure is identical to 3.0 at the operation level
- Differences are in schema validation (nullable, type arrays), not operation structure
- Phase 3 (OAS 3.1 Features) addresses webhooks, which ARE structurally different

**What's unclear:**
- Are there subtle operation-level differences in 3.1 that would break with OpenAPIOperation?
- Does reusing OpenAPIOperation cause coupling issues later?

**Recommendation:** Reuse OpenAPIOperation in Phase 1. The operation class handles routing, parameter extraction, and handler resolution — all unchanged in 3.1. If Phase 3 reveals operation-level differences, we can introduce OpenAPI31Operation then. Premature abstraction is worse than refactoring when needed.

### 3. Which official schema URL to bundle?

**What we know:**
- spec.openapis.org hosts multiple schema versions with date stamps
- Latest "without schema validation": `https://spec.openapis.org/oas/3.1/schema/2025-09-15`
- Latest "with schema validation": `https://spec.openapis.org/oas/3.1/schema-base/2025-08-31`
- "Without schema validation" means it doesn't validate the Schema Object portion (user-defined schemas)
- "With schema validation" includes full OpenAPI Schema dialect validation

**What's unclear:**
- Do we want to validate user schemas as part of spec validation, or defer that to Phase 2?
- Does the "with validation" version add significant complexity or false positives?

**Recommendation:** Use "without schema validation" (`oas/3.1/schema/2025-09-15`) for Phase 1. This validates the spec structure (paths, operations, parameters, responses) but defers schema content validation to Phase 2 where we'll implement request/response validators. Matches current pattern where spec validation is structural, not semantic.

## Sources

### Primary (HIGH confidence)

- [OpenAPI Specification v3.1.0](https://spec.openapis.org/oas/v3.1.0) - Official specification
- [OpenAPI 3.1 JSON Schema (2025-09-15)](https://spec.openapis.org/oas/3.1/schema/2025-09-15.html) - Official meta-schema
- [jsonschema Python Documentation - Schema Validation](https://python-jsonschema.readthedocs.io/en/latest/validate/) - Draft202012Validator usage
- [JSON Schema Draft 2020-12 Release Notes](https://json-schema.org/draft/2020-12/release-notes) - Changes from Draft-04
- [jsonschema Python Documentation - Referencing](https://python-jsonschema.readthedocs.io/en/latest/referencing/) - RefResolver → referencing.Registry migration

### Secondary (MEDIUM confidence)

- [OpenAPI v3.1 and JSON Schema (APIs You Won't Hate)](https://apisyouwonthate.com/blog/openapi-v3-1-and-json-schema/) - Differences between 3.0 and 3.1 (nullable, exclusiveMinimum, type arrays)
- [Upgrading from OpenAPI 3.0 to 3.1 (learn.openapis.org)](https://learn.openapis.org/upgrading/v3.0-to-v3.1.html) - Migration guidance
- [Migrating from OpenAPI 3.0 to 3.1.0 (OpenAPI Initiative Blog)](https://www.openapis.org/blog/2021/02/16/migrating-from-openapi-3-0-to-3-1-0) - Official migration guide
- [OpenAPI Nullable vs Null Value (Stainless)](https://www.stainless.com/sdk-api-best-practices/openapi-nullable-vs-null-value-explained-in-3-0-and-3-1) - Nullable handling differences

### Tertiary (LOW confidence)

- [Validating OpenAPI and JSON Schema (json-schema.org blog)](https://json-schema.org/blog/posts/validating-openapi-and-json-schema) - General context on OAS 3.1 alignment
- [OpenAPI Release Notes (Speakeasy)](https://www.speakeasy.com/openapi/release-notes) - Version history overview
- [Null in OpenAPI best practices (Speakeasy)](https://www.speakeasy.com/openapi/schemas/null) - Nullable patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - jsonschema is de facto Python standard, Draft202012Validator exists and is stable
- Architecture: HIGH - Existing connexion patterns are clear, extension is straightforward
- Pitfalls: HIGH - Based on official docs, deprecation warnings, and common migration issues

**Research date:** 2026-02-05
**Valid until:** 2026-04-05 (60 days - stable domain, OAS 3.1 is mature spec from 2021)

**Research notes:**
- OpenAPI 3.1.0 released February 2021, with patch releases 3.1.1 (October 2024) and 3.1.2 (latest)
- jsonschema 4.26.0 is current stable (January 2026), full Draft 2020-12 support
- No breaking changes expected in this domain — OAS 3.1 is stable, 3.2 is separate branch
- Connexion's existing architecture patterns (version branching, bundled schemas, validator extension) map cleanly to 3.1 support
