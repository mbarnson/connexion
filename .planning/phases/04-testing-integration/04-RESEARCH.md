# Phase 4: Testing & Integration - Research

**Researched:** 2026-02-06
**Domain:** Python testing with pytest, integration testing, code quality validation
**Confidence:** HIGH

## Summary

Phase 4 validates all OpenAPI 3.1 work through comprehensive test coverage, zero-regression verification, and code quality cleanup. Research confirms connexion uses pytest 8.4.2 with pytest-asyncio and pytest-cov, organized in a flat test directory structure with fixture-based integration tests. The existing test suite has 877 passing tests across 50 test files. Linting uses flake8 7.1.1, isort 6.0.1 (black profile), and mypy 1.14.1 via pre-commit hooks. The codebase follows a fixture-per-API pattern where test fixtures (YAML specs + Python handlers in fakeapi/) are loaded via `build_app_from_fixture()` helper and tested through HTTP round-trips using `app.test_client()`.

Current Phase 1-3 tests total 1233 lines across 3 files (test_spec_31.py, test_validation_31.py, test_oas31_features.py) with 75 passing tests. One lint issue found: F401 unused import in openapi31.py. No debug prints found. All 877 existing tests pass with zero regressions.

**Primary recommendation:** Consolidate Phase 1-3 tests into tests/openapi31/ directory structure, create a comprehensive OAS 3.1 kitchen-sink fixture (YAML + fakeapi handlers), write integration test exercising all features through HTTP, clean the one F841 issue and isort formatting in spec.py, verify with full test suite + lint runs across Python 3.11/3.12/3.13 using tox.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**SongViber Integration Scope:**
- No cross-repo dependency from connexion to SongViber — connexion tests must be fully self-contained
- Integration test uses a generic OAS 3.1 "kitchen-sink" YAML spec that exercises every 3.1 feature connexion supports (type arrays, const, webhooks, pathItems, nullable rejection, $ref siblings, numeric exclusive bounds, minimal docs, mutualTLS, jsonSchemaDialect, allOf/anyOf/oneOf composition)
- The kitchen-sink spec is a YAML file in connexion's test fixtures (not inline dict)
- Full mock request/response testing through the connexion app — not just load+validate, but actual HTTP round-trips
- Cover all endpoints in the kitchen-sink spec with mock requests
- SongViber-specific validation (proving songviber-api.yaml works) happens in the SongViber repo, not here

**Test Organization Strategy:**
- Consolidate all 3.1 tests from Phases 1-3 into a consistent structure (e.g., tests/openapi31/ directory)
- Test file organization: Claude's discretion based on connexion's existing patterns
- Kitchen-sink integration spec: YAML file in test fixtures
- Fakeapi handlers for the kitchen-sink spec go in the existing fakeapi module (no new module)

**Regression Verification Approach:**
- Zero regression = existing test suite passes unchanged
- No new cross-version isolation tests needed — existing suite passing is sufficient proof
- Any existing test failure is a blocker — fix immediately before continuing, zero tolerance
- Full test suite runs after each plan execution (not just 3.1 tests), to catch regressions early
- Test against Python 3.11, 3.12, and 3.13 locally (multi-version via tox or similar)

**CI & Lint Cleanup:**
- Manual validation only — no GitHub Actions CI pipeline for this fork
- flake8/isort: zero warnings in new/modified files; don't touch files we didn't modify
- mypy: match existing connexion annotation style (function signatures, not every local var)
- Clean sweep: scan all Phase 1-3 code for debug prints, unused imports, unused variables (F841) and remove them (avoiding PR #2043 reviewer issues)

### Claude's Discretion

- Test file organization within the consolidation structure
- Kitchen-sink spec endpoint design (as long as it covers all 3.1 features)
- tox configuration for multi-version testing
- Order of plans within the phase

### Deferred Ideas (OUT OF SCOPE)

- SongViber-specific integration test (validating songviber-api.yaml) — belongs in SongViber repo
- GitHub Actions CI pipeline — may add later if fork becomes long-lived
- Upstream PR to connexion — potential future work after fork is proven
</user_constraints>

## Standard Stack

### Core Testing Libraries
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 8.4.2 | Test runner | Industry standard, async support, fixture system |
| pytest-asyncio | 0.18.3 | Async test support | Required for testing async operations |
| pytest-cov | 2.12.1 | Coverage reporting | Standard pytest coverage plugin |

### Code Quality Tools
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| flake8 | 7.1.1 | Linting (PEP 8) | Standard Python linter, RST docstring support |
| isort | 6.0.1 | Import sorting | Standard with black profile |
| black | 22.3.0 | Code formatting | Opinionated formatter (via pre-commit) |
| mypy | 1.14.1 | Type checking | Static type validation |
| pre-commit | 2.21.0 | Git hook management | Ensures consistency |

### Multi-Version Testing
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tox | (via pyproject) | Multi-Python testing | Testing across Python 3.11, 3.12, 3.13 |
| poetry | (build backend) | Dependency management | Required for installing test deps |

**Installation:**
```bash
poetry install --all-extras --with tests
```

**Configuration locations:**
- pytest: `pyproject.toml` [tool.pytest.ini_options]
- flake8: `tox.ini` [flake8]
- isort: `pyproject.toml` [tool.isort] (profile = "black")
- mypy: `.pre-commit-config.yaml` (targets connexion/ only)
- coverage: `pyproject.toml` [tool.coverage.report]

## Architecture Patterns

### Recommended Test Organization (Consolidation)

Current state: Phase 1-3 tests are in flat structure (tests/*.py)
Target state: Organized by feature domain

```
tests/
├── openapi31/                    # NEW: Consolidated 3.1 tests
│   ├── __init__.py
│   ├── test_spec_detection.py    # SPEC-01, SPEC-02, SPEC-04, SPEC-05 (from test_spec_31.py)
│   ├── test_validation.py        # VALID-01 through VALID-10 (from test_validation_31.py)
│   ├── test_features.py          # FEAT-01 through FEAT-06, SPEC-03 (from test_oas31_features.py)
│   └── test_integration.py       # TEST-07: Kitchen-sink integration test (NEW)
├── fixtures/
│   └── openapi31_kitchen_sink/   # NEW: Kitchen-sink fixture
│       └── openapi.yaml          # 3.1.0 spec with ALL features
├── fakeapi/
│   └── openapi31_handlers.py     # NEW: Handlers for kitchen-sink spec
├── conftest.py                   # Existing shared fixtures
└── [existing test files unchanged]
```

**Rationale:** Connexion uses flat test directory for legacy tests but groups related API tests in tests/api/. Consolidating 3.1 tests into tests/openapi31/ follows the "group by feature" pattern while keeping legacy tests unchanged (zero regression).

### Pattern 1: Fixture-Based Integration Testing
**What:** Load OpenAPI spec from YAML fixture, wire to Python handlers in fakeapi/, test via HTTP round-trips
**When to use:** Integration tests validating spec loading, routing, validation, and response handling
**Example:**
```python
# Source: tests/api/conftest.py (existing pattern)
from conftest import build_app_from_fixture

@pytest.fixture(scope="session")
def openapi31_kitchen_sink_app(app_class):
    return build_app_from_fixture(
        "openapi31_kitchen_sink",
        app_class=app_class,
        spec_file="openapi.yaml",
        validate_responses=True
    )

def test_kitchen_sink_type_array_endpoint(openapi31_kitchen_sink_app):
    client = openapi31_kitchen_sink_app.test_client()
    # Test endpoint with type: ["string", "null"]
    response = client.post("/type-array", json={"value": None})
    assert response.status_code == 200
```

### Pattern 2: Unit Tests with In-Memory Specs
**What:** Create spec dicts in-memory, test Specification class behavior directly
**When to use:** Testing spec detection, routing, validation without HTTP overhead
**Example:**
```python
# Source: tests/test_spec_31.py (Phase 1)
def test_31_spec_routes_to_openapi31_specification():
    spec_dict = {
        "openapi": "3.1.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {}
    }
    spec = Specification.from_dict(spec_dict)
    assert isinstance(spec, OpenAPI31Specification)
```

### Pattern 3: Parametrized Cross-Version Testing
**What:** Use pytest.mark.parametrize to test same behavior across spec versions
**When to use:** Regression tests ensuring 3.1 doesn't break 3.0/2.0 behavior
**Example:**
```python
# Source: tests/conftest.py
SPECS = ["swagger.yaml", "openapi.yaml"]

@pytest.fixture(scope="session", params=SPECS)
def spec(request):
    return request.param

def test_feature_works_on_all_versions(spec):
    # Test runs twice: once with swagger.yaml, once with openapi.yaml
    pass
```

### Pattern 4: Test Class Organization for Feature Groups
**What:** Group related tests in classes with shared setup/teardown
**When to use:** Testing cohesive feature sets (webhooks, pathItems, etc.)
**Example:**
```python
# Source: tests/test_oas31_features.py (Phase 3)
class TestWebhooks:
    """Tests for OAS 3.1 webhooks property."""

    def test_webhooks_parsed_and_accessible(self):
        # Test webhook parsing
        pass

    def test_webhooks_empty_when_not_defined(self):
        # Test default behavior
        pass
```

### Anti-Patterns to Avoid

- **Don't: Inline large spec dicts in test functions** — Use fixtures or YAML files for readability
- **Don't: Test only load/validate without HTTP round-trips** — Integration tests must exercise full request/response cycle
- **Don't: Create new fakeapi modules** — Extend existing tests/fakeapi/ with handlers
- **Don't: Touch unmodified files during lint cleanup** — Only fix files we changed in Phases 1-3
- **Don't: Skip full test suite runs** — Always run all 877 tests to catch regressions early

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-Python testing | Custom shell scripts | tox with envlist | Handles dependency isolation, version matrix |
| Test fixtures | Manual file loading | pytest fixtures + conftest.py | Automatic cleanup, scope control |
| HTTP test clients | Raw socket/urllib | app.test_client() | Built-in to FlaskApp/AsyncApp |
| Coverage reporting | Manual line tracking | pytest-cov | Integrated with pytest, standard format |
| Import sorting | Manual reordering | isort with black profile | Already configured in pyproject.toml |

**Key insight:** Connexion's test infrastructure is mature and comprehensive. Extend existing patterns rather than inventing new ones. The `build_app_from_fixture()` helper in conftest.py is the standard way to wire specs to handlers.

## Common Pitfalls

### Pitfall 1: Breaking Existing Tests During Consolidation
**What goes wrong:** Moving test files can break imports, change test discovery, or lose fixtures
**Why it happens:** pytest uses directory structure for namespacing and fixture discovery
**How to avoid:**
1. Copy tests to new location first (don't move)
2. Run full suite: `poetry run pytest tests/ -v`
3. If all pass, remove old files
4. Never touch tests outside of openapi31/ directory
**Warning signs:** Import errors, fixture not found errors, test count changes

### Pitfall 2: Incomplete Kitchen-Sink Spec Coverage
**What goes wrong:** Integration test passes but doesn't actually exercise all 3.1 features
**Why it happens:** YAML spec declares features but no endpoints actually use them
**How to avoid:**
1. Create explicit endpoint for EACH feature (type arrays, const, webhooks, pathItems ref, etc.)
2. Write test function for EACH endpoint
3. Verify request/response round-trip, not just load success
**Warning signs:** Kitchen-sink spec has webhooks key but no test calls webhook endpoints

### Pitfall 3: Lint Cleanup Causing Regressions
**What goes wrong:** Fixing lint issues in existing files breaks functionality
**Why it happens:** isort/flake8/mypy changes can alter import order, remove "unused" code that's actually used dynamically
**How to avoid:**
1. Only fix files modified in Phases 1-3: connexion/spec.py, connexion/operations/openapi31.py, connexion/json_schema.py, connexion/security.py
2. Run full test suite IMMEDIATELY after each lint fix
3. If tests fail, revert lint fix and investigate
4. Use `# noqa: F401` for genuinely required "unused" imports (e.g., re-exports)
**Warning signs:** Tests fail after running isort/flake8 fix, "name not defined" errors

### Pitfall 4: Tox Environment Confusion
**What goes wrong:** Tests pass in one Python version but fail in another
**Why it happens:** Different Python versions have different stdlib behavior (datetime parsing, type hints)
**How to avoid:**
1. Test fork requires Python 3.11+ (user decision from Phase 1)
2. Run tox targeting only: `py311-pypi`, `py312-pypi`, `py313-pypi`
3. Don't test 3.9/3.10 (out of scope per .planning/PROJECT.md)
4. If tox.ini envlist includes py39/py310, that's upstream config — ignore for fork validation
**Warning signs:** Test passes locally (Python 3.13) but would fail on older versions

### Pitfall 5: Fixture Scope Issues (pytest-asyncio)
**What goes wrong:** "Event loop already running" or "Event object bound to different event loop" errors
**Why it happens:** Session-scoped async fixtures combined with function-scoped async tests create event loop conflicts
**How to avoid:**
1. Use session-scoped fixtures for fixture-based integration tests (existing pattern)
2. Keep tests synchronous when using session-scoped fixtures (use app.test_client() synchronously)
3. Only use async tests for unit tests with function-scoped fixtures
4. Follow existing conftest.py patterns exactly
**Warning signs:** RuntimeError about event loops, pytest-asyncio deprecation warnings

### Pitfall 6: Debug Code Left in Handlers
**What goes wrong:** Fakeapi handlers have print() statements or unused imports, fail flake8
**Why it happens:** Quick debugging during test writing
**How to avoid:**
1. Run `flake8 tests/fakeapi/` before committing
2. Search for `print(` in all modified files
3. Remove unused imports flagged by F401
**Warning signs:** Flake8 reports F401, stdout pollution during test runs

## Code Examples

Verified patterns from existing codebase:

### Kitchen-Sink Fixture Structure
```yaml
# tests/fixtures/openapi31_kitchen_sink/openapi.yaml
openapi: 3.1.0
info:
  title: OpenAPI 3.1 Kitchen Sink API
  version: 1.0.0

# Minimal document (no paths required in 3.1)
paths: {}

# Webhooks
webhooks:
  newOrder:
    post:
      summary: New order webhook
      operationId: fakeapi.openapi31_handlers.new_order_webhook
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                orderId: {type: string}
      responses:
        '200': {description: OK}

# pathItems in components
components:
  pathItems:
    HealthCheck:
      get:
        summary: Health check
        operationId: fakeapi.openapi31_handlers.health_check
        responses:
          '200':
            description: Healthy
            content:
              application/json:
                schema: {type: object}

  securitySchemes:
    mutualTLS:
      type: mutualTLS
      description: mTLS authentication

  schemas:
    # Type array (3.1 feature)
    NullableString:
      type: ["string", "null"]

    # const keyword
    ApiVersion:
      const: "v1.0.0"

    # $ref with siblings (3.1 feature)
    PetWithDescription:
      $ref: '#/components/schemas/Pet'
      description: A pet with description sibling to $ref
      summary: Pet summary

    Pet:
      type: object
      required: [name]
      properties:
        name: {type: string}
        age: {type: integer, exclusiveMinimum: 0}  # numeric exclusive bounds

    # allOf/anyOf/oneOf composition for form data
    AnimalForm:
      anyOf:
        - properties:
            type: {const: "dog"}
            breed: {type: string}
        - properties:
            type: {const: "cat"}
            indoor: {type: boolean}

# Top-level jsonSchemaDialect
jsonSchemaDialect: https://json-schema.org/draft/2020-12/schema
```

### Kitchen-Sink Handlers
```python
# tests/fakeapi/openapi31_handlers.py
"""Handlers for OpenAPI 3.1 kitchen-sink integration test."""

def new_order_webhook(body):
    """Handle new order webhook."""
    return {"status": "received", "orderId": body.get("orderId")}

def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}

def create_pet(body):
    """Create pet with type array validation."""
    return {"id": "123", "name": body["name"]}

def get_api_version():
    """Return API version (const validation)."""
    return {"version": "v1.0.0"}
```

### Integration Test Pattern
```python
# tests/openapi31/test_integration.py
"""TEST-07: Kitchen-sink integration test with all 3.1 features combined."""
import pytest
from conftest import build_app_from_fixture

@pytest.fixture(scope="session")
def kitchen_sink_app(app_class):
    """App with kitchen-sink 3.1 spec."""
    return build_app_from_fixture(
        "openapi31_kitchen_sink",
        app_class=app_class,
        spec_file="openapi.yaml",
        validate_responses=True
    )

class TestKitchenSinkIntegration:
    """Integration test exercising all OAS 3.1 features through HTTP."""

    def test_spec_loads_successfully(self, kitchen_sink_app):
        """TEST-07: Kitchen-sink spec with all features loads."""
        # Spec loaded if fixture created successfully
        assert kitchen_sink_app is not None

    def test_type_array_validation(self, kitchen_sink_app):
        """Type array ["string", "null"] validates null and string."""
        client = kitchen_sink_app.test_client()
        # Test with null
        resp = client.post("/pets", json={"name": "Fluffy", "tag": None})
        assert resp.status_code == 200
        # Test with string
        resp = client.post("/pets", json={"name": "Fluffy", "tag": "cute"})
        assert resp.status_code == 200

    def test_const_keyword_validation(self, kitchen_sink_app):
        """const keyword validates exact value match."""
        client = kitchen_sink_app.test_client()
        # Valid const value
        resp = client.get("/version")
        assert resp.json()["version"] == "v1.0.0"

    def test_webhooks_accessible(self, kitchen_sink_app):
        """Webhooks are parsed and accessible (not routed)."""
        spec = kitchen_sink_app.apis[0].specification
        assert "newOrder" in spec.webhooks
        assert "post" in spec.webhooks["newOrder"]

    def test_path_items_reference(self, kitchen_sink_app):
        """pathItems in components can be referenced."""
        # pathItems referenced via $ref in paths work
        client = kitchen_sink_app.test_client()
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_mutual_tls_recognized(self, kitchen_sink_app):
        """mutualTLS security scheme is recognized."""
        spec = kitchen_sink_app.apis[0].specification
        assert "mutualTLS" in spec.components.get("securitySchemes", {})

    def test_ref_siblings_preserved(self, kitchen_sink_app):
        """$ref with sibling description/summary preserved."""
        spec = kitchen_sink_app.apis[0].specification
        pet_with_desc = spec.components["schemas"]["PetWithDescription"]
        assert "$ref" in pet_with_desc
        assert "description" in pet_with_desc
        assert "summary" in pet_with_desc

    def test_exclusive_minimum_numeric(self, kitchen_sink_app):
        """exclusiveMinimum as numeric value (not boolean)."""
        client = kitchen_sink_app.test_client()
        # age: 0 should fail (exclusive)
        resp = client.post("/pets", json={"name": "Fluffy", "age": 0})
        assert resp.status_code == 400
        # age: 1 should pass
        resp = client.post("/pets", json={"name": "Fluffy", "age": 1})
        assert resp.status_code == 200

    def test_json_schema_dialect_present(self, kitchen_sink_app):
        """jsonSchemaDialect top-level key is present."""
        spec = kitchen_sink_app.apis[0].specification
        assert spec.json_schema_dialect == "https://json-schema.org/draft/2020-12/schema"

    def test_minimal_document_valid(self, kitchen_sink_app):
        """Spec without paths key is valid in 3.1 (minimal document)."""
        # If fixture loads, minimal document is valid
        assert kitchen_sink_app is not None
```

### Multi-Version Testing with Tox
```bash
# Run tests on Python 3.11, 3.12, 3.13
tox -e py311-pypi,py312-pypi,py313-pypi

# Run just one version for quick validation
tox -e py313-pypi

# Run lint checks
tox -e pre-commit
```

### Lint Cleanup Commands
```bash
# Check for issues in modified files
poetry run flake8 connexion/spec.py connexion/operations/openapi31.py connexion/json_schema.py connexion/security.py

# Fix isort issues
poetry run isort connexion/spec.py connexion/operations/openapi31.py connexion/json_schema.py connexion/security.py

# Check mypy (runs on entire connexion/ directory per config)
poetry run mypy connexion

# Run all pre-commit hooks manually
poetry run pre-commit run --all-files
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Inline spec dicts in tests | YAML fixtures + build_app_from_fixture() | Existing pattern | More readable, reusable |
| Manual HTTP clients | app.test_client() | Existing pattern | Framework-agnostic |
| F841 ignored | F841 cleaned | Phase 4 (now) | Matches upstream quality standards |
| Flat test structure | tests/openapi31/ grouping | Phase 4 (now) | Better organization for 3.1 features |

**Deprecated/outdated:**
- pytest-asyncio 0.18.3: Current version is 1.3.0, but connexion pins to 0.18.3 to avoid event loop issues. Don't upgrade.
- jsonschema RefResolver: Deprecated in jsonschema 4.18+, but connexion still uses it. Out of scope for this fork.

## Open Questions

1. **Should we test Python 3.9/3.10?**
   - What we know: Fork was decided as Python 3.11+ only per .planning/PROJECT.md
   - What's unclear: tox.ini still lists py39-min, py39-pypi, py310-pypi
   - Recommendation: Ignore py39/py310 envs in tox. Test only py311-pypi, py312-pypi, py313-pypi. If tox.ini cleanup is desired, that's a separate task.

2. **Should kitchen-sink spec have paths or only webhooks/components?**
   - What we know: Minimal documents (no paths) are valid in 3.1, but existing integration tests all use paths
   - What's unclear: Whether integration test should exercise both "minimal + paths added later" and "paths from start"
   - Recommendation: Include paths with endpoints. Minimal document validation is already tested in test_oas31_features.py. Kitchen-sink is for HTTP round-trip testing.

3. **Should we consolidate tests by moving or copying?**
   - What we know: Zero regression policy requires existing tests unchanged
   - What's unclear: Whether test_spec_31.py should be removed after copying to tests/openapi31/test_spec_detection.py
   - Recommendation: Copy first, verify all pass, then remove originals. This is safest for zero regression.

## Sources

### Primary (HIGH confidence)
- Connexion codebase: tests/ directory structure, conftest.py patterns, existing test files
- pyproject.toml: Tool configurations for pytest, isort, coverage
- tox.ini: flake8 config, tox environments, test commands
- .pre-commit-config.yaml: Hook configurations for all lint tools
- .planning/codebase/: ARCHITECTURE.md, STACK.md (codebase analysis from 2026-02-05)

### Secondary (MEDIUM confidence)
- pytest documentation: Fixture scopes, parametrization, asyncio mode
- flake8 documentation: Error codes (F401, F841, E402)
- isort documentation: Black profile compatibility

### Tertiary (LOW confidence)
- None (all findings verified against codebase)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Verified from pyproject.toml, tox.ini, actual installed versions
- Architecture: HIGH - Analyzed existing test files, conftest.py, fixture patterns
- Pitfalls: HIGH - Identified from CLAUDE.md "Pitfalls to Avoid" section and PR #2043 reviewer comments

**Research date:** 2026-02-06
**Valid until:** 30 days (stable testing infrastructure, unlikely to change)

**Test suite status at research time:**
- Total tests: 877 passing, 23 warnings, 0 failures
- Phase 1-3 tests: 75 passing (test_spec_31.py: 22, test_validation_31.py: 28, test_oas31_features.py: 25)
- Lint issues found: 1 (F401 in openapi31.py), isort formatting in spec.py
- Python version used: 3.13.5
- Poetry lock status: Updated with all extras and test dependencies
