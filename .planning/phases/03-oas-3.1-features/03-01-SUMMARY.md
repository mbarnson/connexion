---
phase: 03-oas-3.1-features
plan: 01
subsystem: api
tags: [openapi, oas-3.1, spec-parsing, webhooks, json-schema]

# Dependency graph
requires:
  - phase: 02-json-schema-validation
    provides: Draft 2020-12 validator infrastructure
provides:
  - webhooks property on OpenAPI31Specification
  - json_schema_dialect property on OpenAPI31Specification
  - components/pathItems initialization for reusable path items
  - minimal document support (no paths key required)
affects: [03-02, 03-03, testing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Spec-level OAS 3.1 field exposure via properties"
    - "Extended _set_defaults for all component types"

key-files:
  created: []
  modified:
    - connexion/spec.py

key-decisions:
  - "webhooks return empty dict when not present (not None)"
  - "json_schema_dialect returns None when not present (dialect defaults to OAS 3.1)"
  - "paths defaults to empty dict for minimal document support"

patterns-established:
  - "OAS 3.1 top-level fields exposed as properties on OpenAPI31Specification"
  - "All standard component types initialized in _set_defaults (schemas, responses, parameters, etc.)"

# Metrics
duration: 3min
completed: 2026-02-05
---

# Phase 03 Plan 01: Spec-Level Features Summary

**OpenAPI 3.1 webhooks, jsonSchemaDialect, pathItems, and minimal document support exposed via OpenAPI31Specification properties**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-05T21:45:32Z
- **Completed:** 2026-02-05T21:48:44Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- webhooks property exposes OAS 3.1 webhook definitions (API-initiated outbound requests)
- json_schema_dialect property exposes custom JSON Schema dialect URI
- components/pathItems initialized for reusable path items (OAS 3.1 feature)
- paths defaults to empty dict, enabling minimal documents (specs with only webhooks/components)

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend _set_defaults for OAS 3.1 components and paths** - `633bb2d` (feat)
2. **Task 2: Add webhooks and json_schema_dialect properties** - `d600006` (feat)

## Files Created/Modified
- `connexion/spec.py` - Extended OpenAPI31Specification with OAS 3.1 spec-level features

## Decisions Made

**webhooks default value:**
- Return empty dict `{}` when webhooks not present (not None)
- Rationale: Consistent with other collection properties, safe for iteration

**json_schema_dialect default value:**
- Return None when jsonSchemaDialect not present
- Rationale: None signals "use OAS 3.1 default" (Draft 2020-12), distinct from custom dialect

**paths initialization:**
- Ensure paths exists as empty dict in _set_defaults
- Rationale: Prevents KeyError in get_path_params/get_operation for minimal documents (valid 3.1 specs with only webhooks/components)

**Component types initialization:**
- Initialize all standard OAS 3.0 component types plus pathItems
- Rationale: Comprehensive defaults prevent KeyError on component access, matches pattern from OpenAPISpecification

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**Dependency chain during testing:**
- Module import required installing full dependency chain (starlette, httpx, asgiref, werkzeug, etc.)
- Resolution: Installed dependencies via uv pip install
- Impact: Testing workflow verified, no code changes needed

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 03-02 (mutualTLS security scheme):**
- Spec-level infrastructure complete
- webhooks and pathItems exposed for tooling/documentation
- Minimal documents supported (no paths required)

**Ready for Phase 03-03 (OpenAPI31Operation class):**
- json_schema_dialect accessible from spec for passing to operation context
- webhooks dict structure available for potential webhook operation creation

**No blockers or concerns.**

## Self-Check: PASSED

---
*Phase: 03-oas-3.1-features*
*Completed: 2026-02-05*
