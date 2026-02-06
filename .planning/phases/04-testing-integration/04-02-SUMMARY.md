---
phase: 04-testing-integration
plan: 02
subsystem: testing
tags: [integration-tests, kitchen-sink, http-round-trips, oas31, pytest]
requires:
  - 04-01
  - Phase 1 (spec detection)
  - Phase 2 (JSON Schema 2020-12 validation)
  - Phase 3 (OAS 3.1 features)
provides:
  - Comprehensive OAS 3.1 integration test suite
  - Kitchen-sink YAML fixture with all features
  - HTTP round-trip tests for every 3.1 feature
  - Form data composition validation
affects:
  - Future test additions (use kitchen-sink pattern)
  - SongViber API integration testing
tech-stack:
  added: []
  patterns:
    - Kitchen-sink fixture pattern for comprehensive testing
    - HTTP round-trip validation via test_client()
    - Raw spec inspection for $ref sibling verification
key-files:
  created:
    - tests/fixtures/openapi31_kitchen_sink/openapi.yaml
    - tests/fakeapi/openapi31_handlers.py
    - tests/openapi31/conftest.py
    - tests/openapi31/test_integration.py
  modified: []
decisions:
  form-data-array-handling:
    choice: Use type: array with items in form data schemas
    rationale: Form-encoded data parses values as arrays by default in connexion
    alternatives: [encoding object with explode/style, custom validator]
  ref-sibling-verification:
    choice: Check _raw_spec instead of resolved spec
    rationale: resolve_refs merges siblings into resolved schema, but preserves them in _raw_spec
    alternatives: [check resolved spec only, add property to track sibling preservation]
metrics:
  duration: 6 minutes
  completed: 2026-02-06
---

# Phase 04 Plan 02: Kitchen-Sink Integration Tests Summary

**Comprehensive OAS 3.1 integration test suite with HTTP round-trips for every feature**

## Performance

- Duration: 6 minutes
- Tests added: 35 (17 test functions × 2 app types + 1 standalone)
- Total test count: 912 (877 existing + 35 new)
- Zero regression: All existing tests pass

## Accomplishments

### Task 1: Kitchen-Sink Fixture and Handlers (Commit 1112741)

Created comprehensive OAS 3.1 test fixture exercising every supported feature:

**YAML Fixture** (`tests/fixtures/openapi31_kitchen_sink/openapi.yaml`):
- `openapi: 3.1.0` with `jsonSchemaDialect` declaration
- Type arrays: `["string", "null"]` for nullable fields
- `const` keyword validation
- `exclusiveMinimum` as numeric (3.1 behavior)
- `$ref` with sibling keywords (description, summary)
- `allOf`/`anyOf`/`oneOf` composition schemas
- Form data with `anyOf` composition
- `webhooks` section with POST operation
- `pathItems` in components for path reuse
- `mutualTLS` security scheme (3.1 addition)
- Multiple endpoints for boundary testing

**Python Handlers** (`tests/fakeapi/openapi31_handlers.py`):
- 10 handler functions matching all operationIds
- Simple echo/validation pattern for testing
- Webhook handler (for spec documentation)
- Zero flake8 warnings

### Task 2: Integration Tests (Commit 2b09b09)

Created comprehensive HTTP round-trip test suite:

**Test Coverage** (18 test methods in `TestKitchenSinkIntegration` class):

1. **Spec loading**: Verifies OpenAPI31Specification instance
2. **Type arrays (3 tests)**:
   - Accepts `null` value
   - Accepts string value
   - Rejects invalid integer
3. **Const keyword (2 tests)**:
   - Validates exact match
   - Rejects wrong value
4. **ExclusiveMinimum (2 tests)**:
   - Rejects boundary value (0)
   - Accepts above boundary (1)
5. **Webhooks**: Verifies webhook structure in spec
6. **PathItems**: Tests $ref from paths to components/pathItems
7. **MutualTLS**: Verifies security scheme recognition
8. **$ref siblings**: Checks preservation in raw spec
9. **JSON Schema dialect**: Verifies property returns correct URI
10. **AllOf**: Tests composition with required fields from both schemas
11. **AnyOf**: Tests alternatives (email or phone)
12. **OneOf**: Tests exclusive choice (individual or organization)
13. **Form data anyOf**: Tests composition with form-encoded data
14. **Nullable rejection**: Standalone test verifying helpful error message

**Test Pattern**:
- Uses `build_app_from_fixture()` for consistent setup
- Tests both FlaskApp and AsyncApp (parametrized)
- HTTP round-trips via `kitchen_sink_app.test_client()`
- Validates status codes and response bodies
- Direct spec inspection for structural features

## Task Commits

| Task | Commit  | Description | Files |
|------|---------|-------------|-------|
| 1 | 1112741 | Kitchen-sink fixture and handlers | openapi.yaml (320 lines), handlers.py (45 lines) |
| 2 | 2b09b09 | Integration tests | conftest.py (14 lines), test_integration.py (241 lines) |

## Files Created

```
tests/fixtures/openapi31_kitchen_sink/
  openapi.yaml                          # Comprehensive 3.1 spec (320 lines)
tests/fakeapi/
  openapi31_handlers.py                  # Handler functions (45 lines)
tests/openapi31/
  conftest.py                            # Fixture for kitchen_sink_app (14 lines)
  test_integration.py                    # 35 integration tests (241 lines)
```

## Decisions Made

### Form Data Array Handling

**Context**: Form-encoded data in connexion wraps values in arrays by default (`{"field": ["value"]}` instead of `{"field": "value"}`).

**Decision**: Use `type: array` with `items: {type: string}` in form data schemas.

**Rationale**:
- Matches connexion's internal form data parsing behavior
- Simpler than encoding object configuration
- Consistent with existing test patterns in codebase

**Alternatives considered**:
- Use `encoding` object with `explode: false` and `style: form`
- Custom validator to unwrap arrays
- Modify form data parser (rejected - too invasive)

### $ref Sibling Verification

**Context**: `resolve_refs()` merges $ref with sibling keywords into the resolved schema, so the resolved spec doesn't show the $ref itself.

**Decision**: Check `spec._raw_spec` for $ref siblings instead of resolved `spec.components`.

**Rationale**:
- Raw spec preserves the original structure before resolution
- Tests the actual spec parsing behavior (siblings preserved during load)
- Resolved spec still benefits from siblings (description/summary merged in)

**Alternatives considered**:
- Only check resolved spec (rejected - doesn't verify preservation)
- Add property to track sibling preservation (rejected - unnecessary complexity)

## Deviations from Plan

### Form Data Schema Types

**Deviation**: Changed form data schema from `type: string` to `type: array` with `items: {type: string}`.

**Rule Applied**: Rule 1 (Auto-fix bugs) - Form data validation was failing because connexion parses form values as arrays.

**Justification**: This is not a "feature request" but a fix for incorrect schema that doesn't match connexion's actual behavior. The spec must match the framework's form data parsing semantics.

**Files Modified**: `tests/fixtures/openapi31_kitchen_sink/openapi.yaml`

**Commit**: Included in Task 2 commit (2b09b09)

## Issues Encountered

None - plan executed smoothly.

## Next Phase Readiness

**Blockers**: None

**Concerns**: None

**Recommendations**:
1. **For 04-03 (Full suite regression)**: Kitchen-sink tests exercise every feature through HTTP round-trips, providing strong confidence for final regression testing.
2. **For SongViber integration**: Kitchen-sink pattern can be adapted for SongViber API testing - comprehensive spec with all endpoints and edge cases in one fixture.

**Verification**:
- ✅ All 912 tests pass (877 existing + 35 new)
- ✅ Zero flake8 warnings
- ✅ TEST-04 complete: Every 3.1 feature has dedicated test coverage
- ✅ TEST-05 complete: Form data composition tested with anyOf
- ✅ TEST-07 complete: All features combined in one spec that loads and validates

## Self-Check: PASSED

**Files verified:**
- ✅ tests/fixtures/openapi31_kitchen_sink/openapi.yaml
- ✅ tests/fakeapi/openapi31_handlers.py
- ✅ tests/openapi31/conftest.py
- ✅ tests/openapi31/test_integration.py

**Commits verified:**
- ✅ 1112741 (feat: kitchen-sink fixture and handlers)
- ✅ 2b09b09 (test: integration tests)
