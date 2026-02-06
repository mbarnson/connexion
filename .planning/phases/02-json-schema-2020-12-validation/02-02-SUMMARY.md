---
phase: 02-json-schema-2020-12-validation
plan: 02
subsystem: validation
tags: [json-schema, draft-2020-12, openapi-3.1, validation, middleware]

# Dependency graph
requires:
  - phase: 02-01
    provides: Draft 2020-12 validators and spec_version plumbing in operations
provides:
  - spec_version flows from operation through middleware to all validators
  - 3.1 specs use Draft 2020-12 validators for all validation types
  - Comprehensive test coverage for all VALID-* requirements
affects: [02-03-songviber-spec-migration, phase-3-oas-31-features]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "spec_version passed from middleware to validators via constructor"
    - "Validators select Draft 2020-12 vs Draft 4 based on spec_version >= (3,1,0)"
    - "ParameterValidator.validate_parameter() maintains @staticmethod compatibility"

key-files:
  created:
    - tests/test_validation_31.py
  modified:
    - connexion/middleware/request_validation.py
    - connexion/middleware/response_validation.py
    - connexion/validators/json.py
    - connexion/validators/parameter.py
    - connexion/validators/form_data.py

key-decisions:
  - "ParameterValidator.validate_parameter() kept as @staticmethod with optional spec_version parameter for backward compatibility"
  - "All validators default to spec_version=(3,0,0) to prevent regression"
  - "JSONResponseBodyValidator.__init__() signature updated to accept spec_version"

patterns-established:
  - "spec_version extraction: `spec_version = getattr(self._operation, 'spec_version', (3, 0, 0))`"
  - "Validator selection: `if self._spec_version >= (3, 1, 0): use Draft202012* else: use Draft4*`"

# Metrics
duration: 5min 14sec
completed: 2026-02-06
---

# Phase 02 Plan 02: JSON Schema Validation Wiring Summary

**All validators now use Draft 2020-12 for OpenAPI 3.1 specs; complete VALID-01 through VALID-10 test coverage with zero regression**

## Performance

- **Duration:** 5 minutes 14 seconds
- **Started:** 2026-02-06T04:31:19Z
- **Completed:** 2026-02-06T04:36:33Z
- **Tasks:** 2
- **Files modified:** 6 (5 source files + 1 test file)

## Accomplishments
- Wired spec_version from operations through middleware to all validators (request, response, parameter, form data)
- All validators now use Draft 2020-12 validation for OpenAPI 3.1 specs
- Comprehensive test suite covering all 10 VALID-* requirements (28 tests)
- Zero regression in existing test suite (70 related tests pass)

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire spec_version through middleware to all validators** - `93496a6` (feat)
2. **Task 2: Add Phase 2 validation tests covering all VALID-* requirements** - `a3b3a09` (test)

## Files Created/Modified

### Created
- `tests/test_validation_31.py` - Comprehensive tests for all VALID-01 through VALID-10 requirements (28 tests)

### Modified
- `connexion/middleware/request_validation.py` - Extracts spec_version from operation and passes to parameter and body validators
- `connexion/middleware/response_validation.py` - Extracts spec_version from operation and passes to response body validator
- `connexion/validators/json.py` - JSONRequestBodyValidator and JSONResponseBodyValidator use Draft202012* validators for 3.1 specs
- `connexion/validators/parameter.py` - ParameterValidator uses Draft202012Validator for 3.1 specs, maintains @staticmethod compatibility
- `connexion/validators/form_data.py` - FormDataValidator uses Draft202012RequestValidator for 3.1 specs

## Decisions Made

**1. ParameterValidator.validate_parameter() @staticmethod compatibility**
- **Decision:** Keep validate_parameter() as @staticmethod with optional spec_version parameter
- **Rationale:** Existing tests call it as a class method without an instance. Adding spec_version as optional parameter with default (3,0,0) maintains backward compatibility while enabling 3.1 support
- **Alternative considered:** Making it an instance method would break existing test code

**2. Default spec_version=(3,0,0) everywhere**
- **Decision:** All validators default to spec_version=(3,0,0) when not provided
- **Rationale:** Ensures zero regression for existing code that doesn't pass spec_version. 3.0 is the most common version in existing codebases
- **Impact:** New 3.1 specs must explicitly pass spec_version, but all existing 3.0/2.0 specs work unchanged

**3. JSONResponseBodyValidator constructor signature change**
- **Decision:** Added spec_version parameter to __init__() to match request validator pattern
- **Rationale:** Response validator wasn't storing spec_version, needed to be consistent with request validator
- **Impact:** No breaking change since parameter has default value

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All tests passed on first run after fixing backward compatibility for ParameterValidator.validate_parameter() static method usage.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Phase 2 (JSON Schema 2020-12 Validation) is now complete.** All VALID-* requirements satisfied:

- ✅ VALID-01: Draft 2020-12 request validators implemented and wired
- ✅ VALID-02: Draft 2020-12 response validators implemented and wired
- ✅ VALID-03: Type arrays validated correctly
- ✅ VALID-04: Strict nullable rejection enforced
- ✅ VALID-05: Numeric exclusive bounds work
- ✅ VALID-06: const keyword validates
- ✅ VALID-07: $ref sibling preservation works
- ✅ VALID-08: Parameter validation uses Draft 2020-12
- ✅ VALID-09: Form data composition validates
- ✅ VALID-10: unevaluatedProperties validates

**Ready for Phase 3 (OAS 3.1 Features).** The validation engine is now fully 3.1-capable. Next phase can implement webhooks, pathItems, discriminator enhancements, and JSON Schema vocabulary knowing validation will work correctly.

**Note for SongViber:** Plan 02-03 (SongViber spec migration) can now proceed. The validation engine is ready to handle 3.1 specs with type arrays, const, and other 2020-12 features.

---
*Phase: 02-json-schema-2020-12-validation*
*Completed: 2026-02-06*

## Self-Check: PASSED

All files and commits verified:
- ✅ All 6 files exist (5 modified + 1 created)
- ✅ Both task commits present (93496a6, a3b3a09)
