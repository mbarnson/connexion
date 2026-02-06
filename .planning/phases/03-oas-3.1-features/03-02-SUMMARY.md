---
phase: 03-oas-3.1-features
plan: 02
subsystem: api
tags: [openapi, oas-3.1, operations, security, mutualtls]

# Dependency graph
requires:
  - phase: 03-01
    provides: Spec-level properties (webhooks, json_schema_dialect)
provides:
  - OpenAPI31Operation class with json_schema_dialect context
  - mutualTLS security scheme recognition
  - Operation-level 3.1 context propagation
affects: [03-03, testing, songviber-server]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Operation class carries spec-level context via instance variables"
    - "Security passthrough for infrastructure-level validation"

key-files:
  created:
    - connexion/operations/openapi31.py
  modified:
    - connexion/operations/__init__.py
    - connexion/spec.py
    - connexion/security.py

key-decisions:
  - "OpenAPI31Operation carries json_schema_dialect from spec to operation"
  - "mutualTLS returns security_passthrough to avoid middleware ordering conflicts"
  - "Certificate validation delegated to TLS infrastructure/custom middleware"

patterns-established:
  - "Operation.from_spec uses getattr for optional spec properties"
  - "Security scheme recognition returns passthrough for infrastructure-handled schemes"

# Metrics
duration: 3min
completed: 2026-02-06
---

# Phase 03 Plan 02: Operation-Level Features Summary

**OpenAPI31Operation with json_schema_dialect context and mutualTLS security scheme recognition via passthrough**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-06T05:11:17Z
- **Completed:** 2026-02-06T05:14:24Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- OpenAPI31Operation class extends OpenAPIOperation with json_schema_dialect property
- json_schema_dialect flows from spec → operation for downstream validator context
- mutualTLS security scheme recognized as valid OAS 3.1 type
- Certificate validation delegated to infrastructure, avoiding middleware ordering conflicts

## Task Commits

Each task was committed atomically:

1. **Task 1: Create OpenAPI31Operation and wire into spec** - `09ca980` (feat)
2. **Task 2: Add mutualTLS recognition to SecurityHandlerFactory** - `9d728ba` (feat)

## Files Created/Modified
- `connexion/operations/openapi31.py` - OpenAPI31Operation class with json_schema_dialect support
- `connexion/operations/__init__.py` - Export OpenAPI31Operation
- `connexion/spec.py` - Wire OpenAPI31Specification.operation_cls to OpenAPI31Operation
- `connexion/security.py` - Recognize mutualTLS type, return security_passthrough

## Decisions Made

**OpenAPI31Operation design:**
- Inherit from OpenAPIOperation, adding only 3.1-specific context
- Use getattr in from_spec for forward compatibility with optional spec properties
- Store json_schema_dialect as instance variable for downstream access
- Rationale: Minimal change, clean inheritance, future-proof for additional 3.1 context

**mutualTLS handling:**
- Return security_passthrough instead of None or raising warning
- Log at debug level, not warning level
- Rationale: Avoids "unsupported security scheme" warnings for valid 3.1 specs while documenting that actual cert validation is infrastructure's responsibility. Prevents known pitfall where SecurityMiddleware runs BEFORE custom middleware (documented in SongViber CLAUDE.md).

**Delegation pattern:**
- mutualTLS cert validation happens at TLS infrastructure layer (nginx, load balancer, OS)
- Custom middleware can inspect certs if needed (e.g., SongViber's AuthMiddleware)
- Connexion's SecurityHandlerFactory only recognizes the scheme type, doesn't validate
- Rationale: Matches real-world deployment patterns where mTLS is handled by reverse proxy or API gateway

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - straightforward implementation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 03-03 (remaining OAS 3.1 features):**
- Operation class infrastructure complete
- json_schema_dialect accessible from operations for validator selection
- Security scheme recognition extensible for additional 3.1 types

**Ready for SongViber integration:**
- mutualTLS recognized without warnings
- AuthMiddleware can handle certificate validation without conflict
- Security passthrough pattern documented

**No blockers or concerns.**

## Self-Check: PASSED

---
*Phase: 03-oas-3.1-features*
*Completed: 2026-02-06*
