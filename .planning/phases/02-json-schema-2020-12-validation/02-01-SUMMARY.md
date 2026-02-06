---
phase: 02-json-schema-2020-12-validation
plan: "01"
subsystem: validation
tags:
  - json-schema
  - draft-2020-12
  - validators
  - spec-version
  - nullable
  - ref-resolution
dependency-graph:
  requires:
    - "01-01-PLAN (OpenAPI31Specification class)"
    - "01-02-PLAN (Test infrastructure)"
  provides:
    - Draft202012RequestValidator
    - Draft202012ResponseValidator
    - Version-aware resolve_refs
    - Nullable rejection with actionable errors
    - spec_version on operations
  affects:
    - "02-02-PLAN (Validator wiring)"
    - "Phase 3 (Will use spec_version for feature detection)"
tech-stack:
  added:
    - jsonschema.Draft202012Validator
  patterns:
    - Version-aware reference resolution
    - Explicit nullable detection
    - Operation-level version tracking
key-files:
  created: []
  modified:
    - connexion/json_schema.py
    - connexion/spec.py
    - connexion/operations/abstract.py
    - connexion/operations/openapi.py
key-decisions:
  - id: nullable-strict-rejection
    choice: Explicit detection before meta-schema validation
    rationale: OAS 3.1 meta-schema doesn't prohibit nullable, so we detect and reject explicitly with actionable guidance
  - id: ref-sibling-preservation
    choice: Version-aware resolve_refs with spec_version parameter
    rationale: 3.1 requires preserving siblings alongside $ref, 3.0/2.0 need legacy behavior
  - id: spec-version-plumbing
    choice: Pass spec_version through operation hierarchy
    rationale: Operations need version awareness for validator selection in Plan 02-02
metrics:
  duration: 227s
  completed: 2026-02-06
---

# Phase 02 Plan 01: Validator Infrastructure Foundation Summary

**One-liner:** Draft 2020-12 validators with writeOnly enforcement, version-aware $ref sibling preservation, strict nullable rejection, and spec_version plumbing through operations

## Performance

- **Duration:** 3 minutes 47 seconds
- **Started:** 2026-02-06T04:23:14Z
- **Completed:** 2026-02-06T04:27:04Z
- **Tasks:** 2/2 (100%)
- **Files modified:** 4

## Accomplishments

1. **Created Draft 2020-12 validators** in `connexion/json_schema.py`:
   - `Draft202012RequestValidator` uses native type array support (no NullableTypeValidator needed)
   - `Draft202012ResponseValidator` extends Draft202012Validator with writeOnly validation
   - Both validators ready for Plan 02-02 wiring

2. **Made resolve_refs() version-aware**:
   - Added `spec_version` parameter (default `(3, 0, 0)` for backward compatibility)
   - For `spec_version >= (3, 1, 0)`: preserves $ref sibling keywords per JSON Schema 2020-12
   - For `spec_version < (3, 1, 0)`: legacy behavior (strip $ref, merge content)
   - Zero regression on existing code paths

3. **Enhanced nullable rejection** in `OpenAPI31Specification`:
   - Explicit detection before meta-schema validation (meta-schema doesn't prohibit nullable)
   - Provides actionable error message suggesting type arrays: `type: [string, 'null']`
   - Strict rejection at spec load time per user decision

4. **Added spec_version plumbing**:
   - `OpenAPI31Specification.__init__()` passes `spec_version=(3, 1, 0)` to resolve_refs
   - `AbstractOperation` accepts and stores `spec_version` parameter
   - `AbstractOperation.spec_version` property exposes version tuple
   - `OpenAPIOperation.from_spec()` extracts `spec.version` and passes to constructor
   - Enables version-aware validator selection in Plan 02-02

## Task Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create Draft 2020-12 validators and version-aware resolve_refs | a29281b | connexion/json_schema.py |
| 2 | Enhance nullable rejection and add spec_version to operations | db8bbe6 | connexion/spec.py, connexion/operations/abstract.py, connexion/operations/openapi.py |

## Files Created

None (infrastructure additions to existing files)

## Files Modified

1. **connexion/json_schema.py**
   - Added `Draft202012Validator` import
   - Created `Draft202012RequestValidator` and `Draft202012ResponseValidator`
   - Made `resolve_refs()` version-aware with sibling preservation logic

2. **connexion/spec.py**
   - `OpenAPI31Specification.__init__()` passes spec_version to resolve_refs
   - `_validate_spec()` explicitly detects nullable before meta-schema validation
   - Nullable detection provides actionable migration guidance

3. **connexion/operations/abstract.py**
   - Added `spec_version` parameter to `__init__` (default `(3, 0, 0)`)
   - Added `spec_version` property

4. **connexion/operations/openapi.py**
   - Added `spec_version` parameter to `__init__`
   - `from_spec()` extracts and passes `spec.version`

## Decisions Made

### nullable-strict-rejection
**Choice:** Explicit detection before meta-schema validation

**Context:** OAS 3.1 meta-schema doesn't prohibit `nullable` keyword (it just doesn't define it), so validation passes even though it's not part of the spec.

**Alternatives considered:**
- Let meta-schema validation handle it → doesn't work, schema allows unknown properties
- Patch the meta-schema → fragile, breaks on schema updates

**Outcome:** Explicit recursive detection in `_validate_spec()` before meta-schema validation. Provides clear error message with migration guidance.

### ref-sibling-preservation
**Choice:** Version-aware `resolve_refs()` with `spec_version` parameter

**Context:** JSON Schema 2020-12 (used in OAS 3.1) treats `$ref` as an applicator, allowing sibling keywords. Earlier versions required $ref to be standalone.

**Alternatives considered:**
- Always preserve siblings → breaks 3.0/2.0 compatibility
- Two separate functions → code duplication
- Auto-detect from spec structure → fragile, implicit

**Outcome:** Single function with explicit `spec_version` parameter. Default `(3, 0, 0)` ensures zero regression. Clear version branch in `_do_resolve()`.

### spec-version-plumbing
**Choice:** Pass `spec_version` through operation hierarchy

**Context:** Validators (Plan 02-02) need to know spec version to choose Draft4 vs Draft202012. Operations instantiate validators.

**Alternatives considered:**
- Global config → not thread-safe, breaks multi-spec apps
- Validator auto-detection → requires parsing schema, expensive
- Operation subclasses → unnecessary complexity

**Outcome:** `spec_version` flows from `Specification.version` → `Operation.spec_version` → validator constructors. Simple, explicit, testable.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

### Issue 1: OAS 3.1 meta-schema doesn't prohibit nullable
**Symptom:** Specs with `nullable: true` passed meta-schema validation

**Root cause:** OAS 3.1 meta-schema allows additional properties in schema objects, so `nullable` isn't rejected

**Resolution:** Added explicit recursive `_check_nullable()` function in `_validate_spec()` that runs before meta-schema validation. Provides actionable error message with migration guidance. (Rule 2: Auto-add missing critical functionality)

**Impact:** Strict 3.1 validation achieved per user decision. SongViber spec will be updated to use type arrays.

## Next Phase Readiness

**Blockers:** None

**Readiness for Plan 02-02:** ✅ Ready
- Draft202012 validators exist and are importable
- resolve_refs() is version-aware
- Operations carry spec_version tuple
- All infrastructure in place for validator wiring

**Future phase notes:**
- Phase 3 will use `spec_version` for feature detection (webhooks, discriminator, etc.)
- Phase 4 will validate version-aware validator selection with parametrized tests

## Self-Check: PASSED

**Files exist:**
- ✅ connexion/json_schema.py (modified, not created)
- ✅ connexion/spec.py (modified, not created)
- ✅ connexion/operations/abstract.py (modified, not created)
- ✅ connexion/operations/openapi.py (modified, not created)

**Commits exist:**
- ✅ a29281b (Task 1: Draft 2020-12 validators and version-aware resolve_refs)
- ✅ db8bbe6 (Task 2: Enhanced nullable rejection and spec_version)

**Verification results:**
- ✅ Draft202012RequestValidator and Draft202012ResponseValidator importable
- ✅ resolve_refs() has spec_version parameter
- ✅ Nullable rejection produces actionable error message
- ✅ OpenAPIOperation.spec_version property exists
- ✅ All Phase 1 tests pass (22 passed in tests/test_spec_31.py, 10 passed in tests/test_utils.py)
- ✅ Flake8 clean (E402 errors pre-existing, not introduced by this plan)
