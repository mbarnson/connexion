---
phase: 01-spec-detection-schema
plan: 01
subsystem: spec-validation
tags: [openapi, json-schema, draft-2020-12, version-routing, spec-detection]

# Dependency graph
requires:
  - phase: 00-project-init
    provides: Project structure, planning framework, codebase mapping
provides:
  - OpenAPI 3.1 version detection and routing via from_dict()
  - Draft 2020-12 validator for OAS 3.1 meta-schema validation
  - OpenAPI31Specification class as sibling to OpenAPISpecification
  - Bundled OAS 3.1 meta-schema at connexion/resources/schemas/v3.1/schema.json
affects: [02-json-schema-validation, 03-oas-31-features, 04-testing-integration]

# Tech tracking
tech-stack:
  added: [Draft202012Validator, OAS 3.1 meta-schema]
  patterns: [Version-based spec class routing, sibling spec classes over inheritance]

key-files:
  created:
    - connexion/resources/schemas/v3.1/schema.json
  modified:
    - connexion/spec.py

key-decisions:
  - "OpenAPI31Specification as sibling class to OpenAPISpecification, not subclass"
  - "Reuse OpenAPIOperation class for 3.1 (Phase 3 may introduce OpenAPI31Operation if needed)"
  - "Unsupported versions (4.0+) raise InvalidSpecification with helpful message listing supported versions"
  - "Version-aware error messages include detected OAS version"

patterns-established:
  - "Version routing via tuple comparison in from_dict(): < (3,0,0), < (3,1,0), < (4,0,0)"
  - "Sibling spec classes sharing common Specification base, differentiated by validator"
  - "Info-level logging on spec load for version awareness"

# Metrics
duration: 3min
completed: 2026-02-05
---

# Phase 01 Plan 01: Spec Detection & Schema Summary

**OAS 3.1 meta-schema bundled, OpenAPI31Specification class routes version >= 3.1.0 using Draft 2020-12 validator**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-05T19:25:50Z
- **Completed:** 2026-02-05T19:28:40Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Bundled official OpenAPI 3.1 meta-schema from spec.openapis.org (Draft 2020-12 based)
- Created OpenAPI31Specification class with three-way version routing
- All OpenAPI versions (2.0, 3.0.x, 3.1.x) route correctly to respective spec classes
- Unsupported versions (4.0+) fail with helpful error message
- Zero regression - existing 2.0 and 3.0 specs continue routing identically

## Task Commits

Each task was committed atomically:

1. **Task 1: Bundle OAS 3.1 meta-schema** - `9612f7d` (chore)
2. **Task 2: Create OpenAPI31Specification class and update version routing** - `7ba1e87` (feat)

## Files Created/Modified

- `connexion/resources/schemas/v3.1/schema.json` - Official OAS 3.1 meta-schema for spec validation (1411 lines, JSON Schema Draft 2020-12)
- `connexion/spec.py` - Added OpenAPI31Specification class, create_spec_validator_31(), three-way version routing, version-aware error messages

## Decisions Made

**1. OpenAPI31Specification as sibling, not subclass**
- Rationale: 3.0 and 3.1 differ primarily in validator (Draft4 vs Draft202012), not behavior. Sibling classes avoid inheritance complexity while sharing common base.
- Outcome: Both inherit from Specification, override _validate_spec with appropriate validator.

**2. Reuse OpenAPIOperation class for 3.1**
- Rationale: Operation structure is identical between 3.0 and 3.1. No divergence needed yet.
- Outcome: `operation_cls = OpenAPIOperation`. Phase 3 will introduce OpenAPI31Operation if operation-level 3.1 features require it.

**3. Unsupported versions raise InvalidSpecification**
- Rationale: Clear failure for future versions with helpful message listing what IS supported.
- Outcome: Version >= 4.0.0 raises: "OpenAPI 4.0.0 is not supported. Supported versions: 2.0, 3.0.x, 3.1.x"

**4. Version-aware error messages**
- Rationale: User decision - every validation error should include detected OAS version for clarity.
- Outcome: Validation errors formatted as: "OpenAPI 3.1.0 spec validation failed at 'path.to.field': message"

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - both tasks completed successfully without issues.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 2 (JSON Schema 2020-12 Validation):**
- ✓ OAS 3.1 specs route to OpenAPI31Specification
- ✓ Draft 2020-12 validator imported and used for spec-level validation
- ✓ Meta-schema validates spec structure correctly
- ✓ Zero regression on existing 2.0/3.0 specs

**Foundation complete for:**
- JSON Schema 2020-12 request/response validation (Phase 2)
- OAS 3.1 feature implementation (webhooks, pathItems, etc.) (Phase 3)
- Comprehensive 3.1 test coverage (Phase 4)

**No blockers.** Phase 2 can begin immediately.

---
*Phase: 01-spec-detection-schema*
*Completed: 2026-02-05*

## Self-Check: PASSED
