---
phase: 04-testing-integration
plan: 01
subsystem: testing
tags: [flake8, isort, pytest, test-organization]

# Dependency graph
requires:
  - phase: 03-oas-3.1-features
    provides: "OpenAPI31Operation class, spec-level features, comprehensive feature tests"
provides:
  - "Lint-clean Phase 1-3 source files (flake8, isort compliant)"
  - "Organized test structure: tests/openapi31/ directory with 75 consolidated tests"
affects: [04-testing-integration, code-quality, ci-cd]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Feature-based test organization in tests/openapi31/ directory"
    - "Descriptive test file names (test_spec_detection.py, test_validation.py, test_features.py)"

key-files:
  created:
    - "tests/openapi31/__init__.py"
    - "tests/openapi31/test_spec_detection.py"
    - "tests/openapi31/test_validation.py"
    - "tests/openapi31/test_features.py"
  modified:
    - "connexion/operations/openapi31.py"
    - "connexion/spec.py"

key-decisions:
  - "Follow connexion's existing test organization pattern (feature-based directories like tests/api/)"
  - "Rename test files to be descriptive (spec_detection, validation, features) rather than versioned (31)"
  - "F401 and isort are the only lint issues; E402 errors in spec.py are pre-existing"

patterns-established:
  - "All OpenAPI 3.1 tests live in tests/openapi31/ for clear separation and discoverability"
  - "Copy-verify-remove pattern for safe file consolidation"

# Metrics
duration: 2.4min
completed: 2026-02-06
---

# Phase 4 Plan 1: Test Organization & Lint Cleanup Summary

**Lint-clean Phase 1-3 source files and consolidated 75 tests into tests/openapi31/ directory with descriptive names**

## Performance

- **Duration:** 2.4 min
- **Started:** 2026-02-06T06:30:59Z
- **Completed:** 2026-02-06T06:33:22Z
- **Tasks:** 2
- **Files modified:** 2 source files, 3 test files moved, 1 __init__.py created

## Accomplishments
- Fixed F401 unused import in connexion/operations/openapi31.py
- Fixed isort formatting in connexion/spec.py (multi-line operations import)
- Consolidated all 75 Phase 1-3 tests into tests/openapi31/ directory
- Renamed test files to descriptive names (test_spec_detection.py, test_validation.py, test_features.py)
- Zero test regression - 877 tests pass, no double-counting

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix lint issues in Phase 1-3 source files** - `f58700b` (style)
2. **Task 2: Consolidate Phase 1-3 tests into tests/openapi31/ directory** - `2301b7e` (refactor)

## Files Created/Modified
- `connexion/operations/openapi31.py` - Removed unused `import typing as t` (F401 fix)
- `connexion/spec.py` - Formatted operations import to multi-line style (isort fix)
- `tests/openapi31/__init__.py` - Python package marker for openapi31 test directory
- `tests/openapi31/test_spec_detection.py` - Consolidated spec detection tests (moved from test_spec_31.py)
- `tests/openapi31/test_validation.py` - Consolidated validation tests (moved from test_validation_31.py)
- `tests/openapi31/test_features.py` - Consolidated feature tests (moved from test_oas31_features.py)

## Decisions Made

**1. Only fix lint issues introduced in Phases 1-3**
- Rationale: E402 errors in spec.py are pre-existing (from logger placement between imports). Our changes only introduced F401 (unused import) and isort (multi-line import formatting). Both fixed.

**2. Follow connexion's existing test organization pattern**
- Rationale: Connexion already uses feature-based test directories (tests/api/, tests/decorators/). Creating tests/openapi31/ follows this established pattern.

**3. Rename test files to be descriptive**
- Rationale: test_spec_detection.py is more descriptive than test_spec_31.py. Makes it clear what each file tests without needing to read the content.

**4. Copy-verify-remove pattern for test consolidation**
- Rationale: Safety first. Verify copied tests pass in new location BEFORE removing originals. Prevents accidental test loss.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all steps completed without issues.

## Next Phase Readiness

**Ready for Plan 04-02 (kitchen-sink integration test):**
- All source files are lint-clean (flake8, isort)
- All 75 Phase 1-3 tests organized in tests/openapi31/ directory
- Test structure follows connexion patterns (feature-based organization)
- Zero test regression verified (877 core tests + 75 OAS 3.1 tests)

**Blockers:** None

**Foundation for Phase 4 completion:**
- TEST-06 partial: flake8 and isort clean on all Phase 1-3 modified files ✅
- TEST-04 partial: All 75 existing 3.1 tests organized in consistent structure ✅
- TEST-02/TEST-03: Zero regression in existing Swagger 2.0 and OpenAPI 3.0 tests ✅

---
*Phase: 04-testing-integration*
*Completed: 2026-02-06*

## Self-Check: PASSED

All created files verified present:
- tests/openapi31/__init__.py
- tests/openapi31/test_spec_detection.py
- tests/openapi31/test_validation.py
- tests/openapi31/test_features.py

All commits verified present:
- f58700b (Task 1)
- 2301b7e (Task 2)
