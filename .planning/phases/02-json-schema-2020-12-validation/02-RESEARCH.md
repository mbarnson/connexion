# Phase 2: JSON Schema 2020-12 Validation - Research

**Researched:** 2026-02-05
**Domain:** JSON Schema Draft 2020-12 validation for OpenAPI 3.1 request/response/parameter/form data
**Confidence:** HIGH

## Summary

Phase 2 requires upgrading connexion's validation engine from JSON Schema Draft 4 to Draft 2020-12 for OpenAPI 3.1 specs. The research reveals that while Phase 1 introduced `Draft202012Validator` for meta-schema validation, the entire request/response validation pipeline still uses Draft 4 validators hardcoded throughout json_schema.py, validators/json.py, validators/parameter.py, and validators/form_data.py.

**Key findings:**
- Draft202012Validator already imported and used for spec validation (Phase 1 work)
- Five validator classes need upgrading: Draft4RequestValidator, Draft4ResponseValidator, parameter validation, form data validation
- Type arrays (`type: ["string", "null"]`) replace nullable keyword in JSON Schema 2020-12
- Numeric exclusiveMinimum/Maximum replace boolean modifiers from Draft 4
- unevaluatedProperties, const, and $ref siblings all require Draft 2020-12 semantics
- Nullable rejection must happen at spec load time via meta-schema validation
- Form data composition (allOf/anyOf/oneOf) is valid in JSON Schema but has known UI/parser pitfalls

**Primary recommendation:** Create parallel Draft202012RequestValidator and Draft202012ResponseValidator in json_schema.py following the existing pattern. Conditionally select validators based on spec version in validator classes. Reject nullable keyword via OAS 3.1 meta-schema validation with actionable error messages. Support full JSON Schema 2020-12 keywords (const, unevaluatedProperties, type arrays, numeric exclusive bounds, $ref siblings) through the base Draft202012Validator without custom extensions.

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Nullable handling:**
- **Strict rejection**: `nullable: true` in a 3.1 spec is an error, NOT auto-converted to type arrays
- Rejection happens at **spec load time** (meta-schema validation), not at request/response validation time
- Error message must be **actionable**: tell the author exactly what to write instead (e.g. "Use `type: ["string", "null"]` instead of `nullable: true`")
- SongViber spec will be updated to proper 3.1 patterns (`type: ["string", "null"]`) as part of this phase
- This overrides the original roadmap success criterion #4 (backwards-compatible nullable)

**$ref sibling handling:**
- **Full schema siblings**: any JSON Schema keyword alongside `$ref` is preserved, not just `summary`/`description`
- Conflict resolution: Claude's discretion, following JSON Schema 2020-12 semantics (`$ref` as applicator)
- $ref resolution timing (eager vs lazy): Claude's discretion based on existing connexion behavior
- SongViber only uses basic `$ref` — full sibling support is for spec correctness

**Form data composition:**
- **Implement now** for spec completeness, even though SongViber doesn't use form data content types
- allOf/anyOf/oneOf in `multipart/form-data` and `application/x-www-form-urlencoded` schemas must validate correctly
- Strictness on extra fields and `oneOf` matching: Claude's discretion, following existing connexion patterns and JSON Schema 2020-12 semantics

**Error message style:**
- Follow existing connexion error patterns for all 3.1-specific keywords (`const`, `unevaluatedProperties`, type arrays, exclusive bounds)
- Whether to include JSON Schema draft info in errors: Claude's discretion
- Whether to expand type arrays in error messages: Claude's discretion

### Claude's Discretion

- Error message formatting details (draft info, type expansion, bound values)
- $ref resolution timing and conflict resolution approach
- Form data strictness on extra fields and oneOf matching
- How to integrate Draft202012Validator into existing validator classes

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

## Standard Stack

The established libraries for JSON Schema 2020-12 validation in Python.

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| jsonschema | 4.26.0+ | JSON Schema validation with Draft 2020-12 support | De facto Python standard, already in connexion dependencies, provides Draft202012Validator |
| referencing | 0.35.0+ | Modern JSON Schema ref resolution | Replaces deprecated RefResolver, required for $ref siblings in 2020-12 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| jsonschema.validators.extend | stdlib | Extending validators with custom keyword handlers | Already used for Draft4RequestValidator/ResponseValidator |
| jsonschema.FORMAT_CHECKER | stdlib | Format validation (email, uri, date-time, etc.) | Already used in existing validators |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Draft202012Validator | Draft7Validator | Draft 7 lacks 2020-12 features (unevaluatedProperties, prefixItems), incomplete |
| referencing.Registry | Continue with RefResolver | RefResolver deprecated in jsonschema 4.18+, doesn't handle $ref siblings correctly per 2020-12 spec |
| Custom type array handler | Native Draft202012Validator | Reinventing validator logic, error-prone, loses upstream fixes |

**Installation:**

No new dependencies required. The `jsonschema` library version ~=4.17 already in connexion's pyproject.toml includes full Draft 2020-12 support. The `referencing` library is already in dependencies (mypy overrides exist in pyproject.toml lines 111-116).

## Architecture Patterns

### Recommended Code Structure

```
connexion/
├── json_schema.py                  # Add Draft202012RequestValidator, Draft202012ResponseValidator
├── validators/
│   ├── json.py                     # Conditionally use Draft202012*Validator for 3.1 specs
│   ├── parameter.py                # Conditionally use Draft202012Validator for 3.1 specs
│   └── form_data.py                # Conditionally use Draft202012RequestValidator for 3.1 specs
└── spec.py                         # Already has create_spec_validator_31 with Draft202012Validator (Phase 1)
```

### Pattern 1: Version-Conditional Validator Selection

**What:** Validator classes detect spec version and select Draft4 or Draft202012 validator base accordingly.

**When to use:** In validator property methods (`_validator` property in JSONRequestBodyValidator, etc.)

**Example:**

```python
# Source: Existing pattern in connexion/validators/json.py:44-48, extended for 3.1
class JSONRequestBodyValidator(AbstractRequestBodyValidator):
    def __init__(
        self,
        *,
        schema: dict,
        required=False,
        nullable=False,
        encoding: str,
        strict_validation: bool,
        spec_version: tuple = (3, 0, 0),  # NEW: pass spec version
        **kwargs,
    ) -> None:
        super().__init__(
            schema=schema,
            required=required,
            nullable=nullable,
            encoding=encoding,
            strict_validation=strict_validation,
        )
        self._spec_version = spec_version  # NEW: store version

    @property
    def _validator(self):
        # Version-conditional validator selection
        if self._spec_version >= (3, 1, 0):
            return Draft202012RequestValidator(
                self._schema, format_checker=Draft202012Validator.FORMAT_CHECKER
            )
        else:
            return Draft4RequestValidator(
                self._schema, format_checker=Draft4Validator.FORMAT_CHECKER
            )
```

**Rationale:** Maintains backward compatibility while enabling 3.1 features. Single validator class handles both Draft 4 and 2020-12 by branching on version.

### Pattern 2: Parallel Extended Validators for Draft 2020-12

**What:** Create Draft202012RequestValidator and Draft202012ResponseValidator following the same extension pattern as Draft4 versions.

**When to use:** In json_schema.py when setting up 3.1 validation.

**Example:**

```python
# Source: Existing pattern in connexion/json_schema.py:135-154, adapted for Draft 2020-12
from jsonschema import Draft202012Validator
from jsonschema.validators import extend

# For 3.1 specs, type arrays handle nullability natively
# No custom NullableTypeValidator needed for Draft 2020-12
Draft202012RequestValidator = Draft202012Validator
# No extensions needed - Draft 2020-12 handles type arrays natively

Draft202012ResponseValidator = extend(
    Draft202012Validator,
    {
        "writeOnly": validate_writeOnly,
        "x-writeOnly": validate_writeOnly,
    },
)
```

**Rationale:** Type arrays (`type: ["string", "null"]`) are native to Draft 2020-12, no custom nullable handling needed. Response validator still needs writeOnly check for OAS semantics.

### Pattern 3: Nullable Rejection via Meta-Schema

**What:** The OAS 3.1 meta-schema itself rejects `nullable` keyword, producing error at spec load time.

**When to use:** During OpenAPI31Specification._validate_spec() in spec.py

**Example:**

```python
# Source: OAS 3.1 meta-schema pattern (spec.openapis.org/oas/3.1/schema)
# The bundled v3.1/schema.json prohibits nullable in schema definitions

# In OpenAPI31Specification._validate_spec() (already implemented in Phase 1)
def _validate_spec(cls, spec):
    """Validate spec against OAS 3.1 meta-schema."""
    spec_validator_cls = create_spec_validator_31(spec)
    spec_validator = spec_validator_cls(cls.openapi_schema)

    try:
        spec_validator.validate(spec)
    except ValidationError as e:
        # Detect nullable keyword rejection
        if "nullable" in str(e.message).lower():
            # Enhance error with migration guidance
            raise InvalidSpecification(
                f"OpenAPI 3.1 spec validation failed: {e.message}\n\n"
                "Hint: OpenAPI 3.1 removed 'nullable'. Use type arrays instead:\n"
                "  # Instead of:\n"
                "  type: string\n"
                "  nullable: true\n"
                "  # Use:\n"
                "  type: [string, 'null']"
            )
        raise InvalidSpecification(f"OpenAPI 3.1 spec validation failed: {e.message}")
```

**Rationale:** Meta-schema validation is the canonical enforcement point. Spec never loads if invalid, preventing runtime confusion.

### Pattern 4: Type Array Validation in Draft 2020-12

**What:** Draft202012Validator natively handles type as array or string, validating null correctly.

**When to use:** Everywhere Draft202012Validator is used for 3.1 schemas.

**Example:**

```python
# Source: JSON Schema 2020-12 spec, native type array support
# No custom code needed - Draft202012Validator handles this automatically

# Schema examples:
schema_nullable_string = {
    "type": ["string", "null"]  # Accepts "hello" or null
}

schema_nullable_array = {
    "type": ["array", "null"],  # Accepts [] or null
    "items": {"type": "string"}
}

# Draft202012Validator validates these correctly without extensions
validator = Draft202012Validator(schema_nullable_string)
validator.validate(None)  # Passes
validator.validate("hello")  # Passes
validator.validate(42)  # Fails: not string or null
```

**Rationale:** Type arrays are a core JSON Schema 2020-12 feature. No custom logic needed.

### Pattern 5: unevaluatedProperties Validation

**What:** Draft202012Validator tracks "evaluated" properties through allOf/anyOf/oneOf and validates remaining properties.

**When to use:** When 3.1 schemas use unevaluatedProperties to enforce strict property sets after composition.

**Example:**

```python
# Source: JSON Schema 2020-12 unevaluatedProperties semantics
schema_with_composition = {
    "allOf": [
        {"properties": {"name": {"type": "string"}}}
    ],
    "properties": {"age": {"type": "integer"}},
    "unevaluatedProperties": False  # Rejects any property not in name/age
}

# Draft202012Validator handles this automatically
validator = Draft202012Validator(schema_with_composition)
validator.validate({"name": "Alice", "age": 30})  # Passes
validator.validate({"name": "Bob", "extra": "bad"})  # Fails: extra is unevaluated
```

**Rationale:** unevaluatedProperties moved to its own vocabulary in 2020-12. Draft202012Validator implements full semantics including interaction with applicators (allOf, anyOf, oneOf, if/then/else).

### Pattern 6: $ref Sibling Preservation

**What:** In JSON Schema 2020-12, keywords alongside $ref are preserved and applied as if wrapped in allOf.

**When to use:** When 3.1 schemas use $ref with description, title, or other schema keywords.

**Example:**

```python
# Source: JSON Schema 2020-12 spec, $ref as applicator
schema_with_ref_siblings = {
    "$ref": "#/$defs/User",
    "description": "The authenticated user",  # Sibling preserved
    "examples": [{"name": "Alice"}]  # Sibling preserved
}

# Draft202012Validator handles siblings automatically
# Equivalent to:
# {
#   "allOf": [
#     {"$ref": "#/$defs/User"},
#     {"description": "...", "examples": [...]}
#   ]
# }
```

**Rationale:** $ref changed from replacement to applicator in Draft 2019-09/2020-12. Draft202012Validator implements correct semantics. Connexion's resolve_refs() in json_schema.py may need adjustment to NOT strip siblings when processing 3.1 specs.

### Anti-Patterns to Avoid

**DON'T: Use allow_nullable wrapper for Draft 2020-12 validators**
- Why it's bad: Type arrays are native, nullable doesn't exist in 3.1, wrapper introduces incorrect semantics
- Do instead: Use Draft202012Validator directly, let type arrays handle nullability

**DON'T: Strip $ref siblings during resolution**
- Why it's bad: Violates JSON Schema 2020-12 spec, loses schema annotations, breaks composition
- Do instead: For 3.1 specs, preserve sibling keywords when resolving $ref

**DON'T: Manually validate const keyword**
- Why it's bad: Draft202012Validator already validates const correctly
- Do instead: Trust the base validator

**DON'T: Convert nullable to type arrays at load time**
- Why it's bad: Hides spec errors, violates "explicit is better than implicit" principle
- Do instead: Reject nullable at meta-schema validation with helpful error message

## Don't Hand-Roll

Problems that look simple but have existing solutions.

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Type array validation | Custom type checker | Draft202012Validator native support | Type arrays are core JSON Schema 2020-12, validator handles all edge cases (order independence, duplicate types, etc.) |
| unevaluatedProperties logic | Custom property tracking | Draft202012Validator native support | Extremely complex: must track evaluation through allOf, anyOf, oneOf, if/then/else, patternProperties, additionalProperties. Validator implements full spec. |
| $ref with siblings | Custom merge logic | Draft202012Validator + referencing.Registry | $ref as applicator has subtle semantics (keyword precedence, conflict resolution). Spec-compliant implementation exists. |
| Nullable to type array conversion | String replacement or AST transform | Meta-schema rejection + user fix | Conversion is lossy (loses type information), error-prone (nested schemas, conditionals), violates explicit-over-implicit principle. |
| exclusiveMinimum/Maximum numeric validation | Boolean flag interpretation | Draft202012Validator native support | Draft 2020-12 changed semantics: `exclusiveMinimum: 5` means `x > 5`, not `minimum: 5, exclusive: true`. Validator handles correctly. |

**Key insight:** JSON Schema 2020-12 is a mature, complex specification. Draft202012Validator in jsonschema library is battle-tested, spec-compliant, and actively maintained. Custom validation logic for 2020-12 keywords will be incomplete and buggy.

## Common Pitfalls

### Pitfall 1: Forgetting to Pass Spec Version to Validators

**What goes wrong:** Validators always use Draft4, ignoring that they're validating a 3.1 spec. Type arrays fail validation, unevaluatedProperties ignored, const keyword unrecognized.

**Why it happens:** Validator instantiation happens in middleware/decorators far from the Specification object. Spec version context is lost.

**How to avoid:**
- Store spec version tuple in Operation objects
- Pass spec_version parameter to validator constructors
- Default to (3, 0, 0) for backward compatibility with existing call sites

**Warning signs:**
- 3.1 specs with `type: ["string", "null"]` fail validation with "not of type 'array'" error
- unevaluatedProperties keyword ignored, extra properties accepted
- const validation doesn't work

### Pitfall 2: Mixing Draft 4 and Draft 2020-12 Semantics

**What goes wrong:** Using Draft4RequestValidator with a schema containing type arrays or unevaluatedProperties. Validation passes when it should fail, or fails with confusing errors.

**Why it happens:** Copy-paste code reuse, incomplete validator migration, test fixtures using mixed drafts.

**How to avoid:**
- Always pair spec version with appropriate validator draft
- Test that Draft4Validator rejects 2020-12 keywords (negative testing)
- Grep for Draft4Validator usage, ensure all callsites check version

**Warning signs:**
- Type arrays like `["string", "null"]` treated as enum values
- unevaluatedProperties has no effect on validation
- Numeric exclusiveMinimum interpreted as enum value

### Pitfall 3: Not Stripping Nullable in 3.0 Specs

**What goes wrong:** Keeping `nullable` handling for 3.0 specs while removing it for 3.1 breaks backward compatibility.

**Why it happens:** Overzealous cleanup when implementing 3.1 support, assuming nullable is dead.

**How to avoid:**
- Keep allow_nullable and is_nullable utils for 3.0 and 2.0 specs
- Only disable nullable checking for 3.1 specs
- Test that 3.0 specs with `nullable: true` still validate correctly

**Warning signs:**
- Existing 3.0 tests fail with "null not allowed" errors
- Swagger 2.0 `x-nullable` doesn't work anymore

### Pitfall 4: resolve_refs() Stripping $ref Siblings in 3.1 Specs

**What goes wrong:** The current resolve_refs() function in json_schema.py does `node.update(retrieved)` then `node.pop("$ref")`, which removes the $ref and any sibling keywords. In 3.1, siblings must be preserved.

**Why it happens:** Draft 4 semantics where $ref was replacement, not applicator. Code written for that assumption.

**How to avoid:**
- For 3.1 specs, don't call resolve_refs() or make it version-aware
- Use referencing.Registry which handles siblings correctly
- If keeping resolve_refs(), make it preserve siblings for 3.1

**Warning signs:**
- $ref with description loses the description after resolution
- Tests for $ref siblings fail in 3.1 but pass in 3.0

### Pitfall 5: oneOf in Form Data Causing Parser Confusion

**What goes wrong:** Form data with oneOf composition validates correctly but causes Swagger UI or other tools to send malformed requests (JSON payload instead of form encoding).

**Why it happens:** OpenAPI spec is valid, but UI/parser tools don't handle oneOf in form content types well. This is a tooling limitation, not a spec or validation issue.

**How to avoid:**
- Implement validation correctly per spec (allOf/anyOf/oneOf all valid)
- Document known UI limitations in comments
- For SongViber: not an issue since no form data endpoints used

**Warning signs:**
- Validation passes but clients send wrong content-type
- Swagger UI doesn't render form correctly

### Pitfall 6: unevaluatedProperties Evaluation Order

**What goes wrong:** unevaluatedProperties must evaluate AFTER all applicators (allOf, if/then, etc.). If validator doesn't follow spec order, properties incorrectly marked unevaluated.

**Why it happens:** Custom validator implementations that don't follow JSON Schema evaluation semantics.

**How to avoid:**
- Use Draft202012Validator directly, don't implement unevaluatedProperties logic
- Test interaction: allOf with properties, then unevaluatedProperties: false
- Known issue in jsonschema library (GitHub issue #1365) but mostly resolved in 4.26.0

**Warning signs:**
- Properties defined in allOf subschemas rejected as unevaluated
- Order of schema keywords affects validation results

## Code Examples

Verified patterns from official sources and connexion implementation.

### Creating Draft 2020-12 Request/Response Validators

```python
# Source: connexion/json_schema.py:135-154, adapted for Draft 2020-12
from jsonschema import Draft202012Validator
from jsonschema.validators import extend

def validate_writeOnly(validator, wo, instance, schema):
    """Reject writeOnly properties in responses (OAS semantic validation)."""
    yield ValidationError("Property is write-only")

# Request validator: No extensions needed for 3.1
# Type arrays and unevaluatedProperties work natively
Draft202012RequestValidator = Draft202012Validator

# Response validator: Still needs writeOnly enforcement
Draft202012ResponseValidator = extend(
    Draft202012Validator,
    {
        "writeOnly": validate_writeOnly,
        "x-writeOnly": validate_writeOnly,
    },
)
```

### Conditional Validator Selection in JSON Validator

```python
# Source: connexion/validators/json.py, extended for 3.1 support
from connexion.json_schema import (
    Draft4RequestValidator,
    Draft4ResponseValidator,
    Draft202012RequestValidator,
    Draft202012ResponseValidator,
)

class JSONRequestBodyValidator(AbstractRequestBodyValidator):
    def __init__(
        self,
        *,
        schema: dict,
        required=False,
        nullable=False,
        encoding: str,
        strict_validation: bool,
        spec_version: tuple = (3, 0, 0),  # NEW
        **kwargs,
    ) -> None:
        super().__init__(
            schema=schema,
            required=required,
            nullable=nullable,
            encoding=encoding,
            strict_validation=strict_validation,
        )
        self._spec_version = spec_version

    @property
    def _validator(self):
        if self._spec_version >= (3, 1, 0):
            return Draft202012RequestValidator(
                self._schema, format_checker=Draft202012Validator.FORMAT_CHECKER
            )
        else:
            return Draft4RequestValidator(
                self._schema, format_checker=Draft4Validator.FORMAT_CHECKER
            )
```

### Parameter Validator with Draft 2020-12

```python
# Source: connexion/validators/parameter.py:46-57, extended for 3.1
from jsonschema import Draft4Validator, Draft202012Validator

class ParameterValidator:
    def __init__(
        self,
        parameters,
        uri_parser,
        strict_validation=False,
        security_query_params=None,
        spec_version=(3, 0, 0),  # NEW
    ):
        self.parameters = collections.defaultdict(list)
        for p in parameters:
            self.parameters[p["in"]].append(p)

        self.uri_parser = uri_parser
        self.strict_validation = strict_validation
        self.security_query_params = set(security_query_params or [])
        self._spec_version = spec_version  # NEW

    def validate_parameter(self, parameter_type, value, param, param_name=None):
        if is_nullable(param) and is_null(value):
            return

        elif value is not None:
            param = copy.deepcopy(param)
            param = param.get("schema", param)

            # Select validator based on spec version
            if self._spec_version >= (3, 1, 0):
                validator_cls = Draft202012Validator
            else:
                validator_cls = Draft4Validator

            try:
                validator_cls(param, format_checker=draft4_format_checker).validate(
                    value
                )
            except ValidationError as exception:
                return str(exception)
```

### Nullable Rejection Error Message Enhancement

```python
# Source: connexion/spec.py OpenAPI31Specification._validate_spec()
class OpenAPI31Specification(Specification):
    @classmethod
    def _validate_spec(cls, spec):
        """Validate spec against OAS 3.1 meta-schema."""
        spec_validator_cls = create_spec_validator_31(spec)
        spec_validator = spec_validator_cls(cls.openapi_schema)

        try:
            spec_validator.validate(spec)
        except ValidationError as e:
            version = spec.get("openapi", "3.1.0")
            error_msg = f"OpenAPI {version} spec validation failed: {e.message}"

            # Detect and enhance nullable keyword errors
            if "nullable" in str(e.schema_path).lower() or \
               ("additional properties" in e.message.lower() and "nullable" in str(e.instance)):
                error_msg += (
                    "\n\nNote: OpenAPI 3.1 removed the 'nullable' keyword.\n"
                    "Use type arrays instead:\n\n"
                    "  # OpenAPI 3.0 style (invalid in 3.1):\n"
                    "  type: string\n"
                    "  nullable: true\n\n"
                    "  # OpenAPI 3.1 style (correct):\n"
                    "  type: [string, 'null']"
                )

            raise InvalidSpecification(error_msg)
```

### Type Array Schema Examples

```python
# Source: JSON Schema 2020-12 specification
# These schemas work natively with Draft202012Validator

# Nullable string
schema_nullable_string = {
    "type": ["string", "null"]
}

# Nullable array of strings
schema_nullable_array = {
    "type": ["array", "null"],
    "items": {"type": "string"}
}

# Multiple types (not just null)
schema_multi_type = {
    "type": ["string", "integer", "null"]
}

# Type array with additional constraints
schema_constrained = {
    "type": ["string", "null"],
    "minLength": 3,
    "maxLength": 50
}
```

### unevaluatedProperties Example

```python
# Source: JSON Schema 2020-12 unevaluatedProperties semantics
schema_strict_composition = {
    "type": "object",
    "allOf": [
        {
            "properties": {
                "name": {"type": "string"}
            }
        },
        {
            "properties": {
                "age": {"type": "integer"}
            }
        }
    ],
    "properties": {
        "email": {"type": "string", "format": "email"}
    },
    "unevaluatedProperties": False  # Only name, age, email allowed
}

# Valid instances
valid = {"name": "Alice", "age": 30, "email": "alice@example.com"}
# Invalid: extra property
invalid = {"name": "Bob", "age": 25, "extra": "not allowed"}
```

## State of the Art

Changes in JSON Schema 2020-12 that impact validation implementation.

| Old Approach (Draft 4) | Current Approach (2020-12) | When Changed | Impact |
|------------------------|---------------------------|--------------|--------|
| `nullable: true` (OAS 3.0) | `type: ["string", "null"]` | JSON Schema Draft 2019-09 (2019), adopted by OAS 3.1.0 (2021) | Must reject nullable in 3.1 specs, use native type arrays |
| `exclusiveMinimum: true` boolean | `exclusiveMinimum: 5` numeric | JSON Schema Draft 6 (2017), 2020-12 (2020) | Draft202012Validator handles numeric form correctly |
| `additionalProperties` for composition | `unevaluatedProperties` | JSON Schema Draft 2019-09 (2019) | Tracks evaluation through applicators (allOf, anyOf, oneOf) |
| `items` as array or object | `prefixItems` + `items` split | JSON Schema 2020-12 (2020) | prefixItems for tuple validation, items for array validation |
| `$ref` replaces siblings | `$ref` as applicator, siblings preserved | JSON Schema Draft 2019-09 (2019) | Must preserve sibling keywords when resolving $ref |
| RefResolver | referencing.Registry | jsonschema 4.18.0 (2023) | RefResolver deprecated, Registry required for $ref siblings |

**Deprecated/outdated:**

- **nullable keyword in OpenAPI 3.1**: Removed from OAS spec. Use `type: [T, "null"]` instead.
- **jsonschema.RefResolver**: Deprecated since jsonschema 4.18.0. Use `referencing.Registry` + `referencing.jsonschema.DRAFT202012` for 3.1 specs.
- **Boolean exclusiveMinimum/exclusiveMaximum**: Draft 4 semantics. Use numeric values in Draft 2020-12.
- **additionalItems keyword**: Replaced by `items` (with different semantics) in Draft 2020-12. Use `items: false` to reject extra array elements.

## Open Questions

Things that couldn't be fully resolved during research.

### 1. Should resolve_refs() be version-aware or replaced with referencing.Registry?

**What we know:**
- Current resolve_refs() in json_schema.py strips $ref and merges content (line 92: `node.pop("$ref", None)`)
- JSON Schema 2020-12 requires $ref siblings to be preserved
- referencing.Registry is the modern replacement for RefResolver
- referencing handles $ref siblings correctly per 2020-12 spec

**What's unclear:**
- Does connexion's validator pipeline call resolve_refs() before validation, or do validators resolve refs internally?
- If we make resolve_refs() version-aware (preserve siblings for 3.1), does that break existing code paths?
- Is Phase 2 the right time to migrate to referencing.Registry, or defer to Phase 3?

**Recommendation:** Make resolve_refs() version-aware for Phase 2: add `spec_version` parameter, preserve siblings for 3.1. Migration to referencing.Registry can be Phase 3 or technical debt cleanup. This minimizes blast radius while fixing the immediate issue.

### 2. How should we handle format_checker for Draft202012Validator?

**What we know:**
- Draft4Validator.FORMAT_CHECKER exists and is used everywhere
- Draft202012Validator also has FORMAT_CHECKER attribute
- Format validation is optional in JSON Schema, but OAS often relies on it (email, uri, date-time)

**What's unclear:**
- Are Draft4 and Draft202012 format checkers identical, or do they differ?
- Can we use Draft4Validator.FORMAT_CHECKER with Draft202012Validator safely?
- Do any formats change semantics between drafts?

**Recommendation:** Use `Draft202012Validator.FORMAT_CHECKER` for 3.1 specs to be spec-compliant. Test that common formats (email, uri, date-time, uuid) work correctly. If format checkers are identical (likely, since formats are defined externally), this is zero-risk.

### 3. Does nullable parameter need to stay in validator constructors for 3.1?

**What we know:**
- AbstractRequestBodyValidator takes `nullable` parameter
- For 3.1, nullability is expressed in schema via type arrays
- The `nullable` parameter is used to determine if empty body (None) is valid
- is_nullable() utility checks schema, not constructor parameter

**What's unclear:**
- Is the constructor `nullable` parameter actually used in 3.1 validation flow?
- Should we deprecate it for 3.1 and read from schema instead?
- Does removing it break existing call sites?

**Recommendation:** Keep `nullable` parameter for backward compatibility, but for 3.1 specs, validate nullability via type array in schema instead of constructor parameter. Add comment explaining 3.1 ignores this parameter.

## Sources

### Primary (HIGH confidence)

- [JSON Schema 2020-12 Release Notes](https://json-schema.org/draft/2020-12/release-notes) - Official specification changes
- [jsonschema Python Documentation - Schema Validation](https://python-jsonschema.readthedocs.io/en/latest/validate/) - Draft202012Validator usage and API
- [jsonschema Python Documentation - Creating or Extending Validator Classes](https://python-jsonschema.readthedocs.io/en/stable/creating/) - How to extend validators with custom keywords
- [JSON Schema 2020-12 Specification](https://json-schema.org/draft/2020-12) - Official spec for validation semantics
- [JSON Schema - Numeric types](https://json-schema.org/understanding-json-schema/reference/numeric) - exclusiveMinimum/Maximum numeric values
- [Learn JSON Schema - unevaluatedProperties (2020-12)](https://www.learnjsonschema.com/2020-12/unevaluated/unevaluatedproperties/) - unevaluatedProperties behavior and examples
- [Learn JSON Schema - const (2020-12)](https://www.learnjsonschema.com/2020-12/validation/const/) - const keyword validation
- [Learn JSON Schema - $ref (2020-12)](https://www.learnjsonschema.com/2020-12/core/ref/) - $ref with siblings behavior

### Secondary (MEDIUM confidence)

- [OpenAPI Specification Issue #2244 - Remove "nullable" in OAS 3.1?](https://github.com/OAI/OpenAPI-Specification/issues/2244) - Discussion of nullable removal in 3.1
- [OpenAPI Specification Issue #3148 - Clarification on nullable properties, OpenAPI 3.1](https://github.com/OAI/OpenAPI-Specification/issues/3148) - Nullable to type array migration
- [Speakeasy - Null in OpenAPI best practices](https://www.speakeasy.com/openapi/schemas/null) - Practical nullable handling in 3.1
- [JSON Schema - Boolean JSON Schema combination](https://json-schema.org/understanding-json-schema/reference/combining) - allOf, anyOf, oneOf semantics
- [Medium - Bulletproof Your Input Validation — Understanding unevaluatedProperties](https://medium.com/@smikulcik/bulletproof-your-input-validation-understanding-unevaluatedproperties-c6e7a0eb6ddd) - unevaluatedProperties practical use

### Tertiary (LOW confidence)

- [Swagger UI Issue #7640 - oneOf / anyOf usage with form-based content-type schema](https://github.com/swagger-api/swagger-ui/issues/7640) - Known UI limitation with oneOf in form data
- [jsonschema Issue #1365 - unevaluatedProperties do not treat "in-place applicators" per the spec](https://github.com/python-jsonschema/jsonschema/issues/1365) - Known library issue (partially resolved)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - jsonschema 4.26.0 is current stable, Draft202012Validator exists and is mature
- Architecture: HIGH - Existing connexion patterns (extend validator, version branching) map directly to 3.1 validation
- Pitfalls: HIGH - Based on official JSON Schema spec changes, known library issues, and OpenAPI migration guides

**Research date:** 2026-02-05
**Valid until:** 2026-04-05 (60 days - stable domain, JSON Schema 2020-12 finalized in 2020, jsonschema library mature)

**Research notes:**
- JSON Schema 2020-12 published December 2020, stable spec
- jsonschema 4.26.0 released January 2026, full Draft 2020-12 support since 3.0.0 (2019)
- OpenAPI 3.1.0 released February 2021, aligned with JSON Schema 2020-12
- Connexion already uses jsonschema ~=4.17, no version upgrade needed
- Phase 1 completed: Draft202012Validator already used for meta-schema validation in create_spec_validator_31()
- All 2020-12 keywords (type arrays, const, unevaluatedProperties, numeric exclusive bounds) work natively in Draft202012Validator with zero custom extensions
- Main implementation work: conditionally select Draft202012Validator in validator classes based on spec version
