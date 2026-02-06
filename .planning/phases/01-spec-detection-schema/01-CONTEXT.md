# Phase 1: Spec Detection & Schema - Context

**Gathered:** 2026-02-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Connexion correctly detects OpenAPI 3.1.x specs and routes them to dedicated handling with proper meta-schema validation. Swagger 2.0 and OpenAPI 3.0 specs continue routing correctly with zero regression. This phase does NOT include request/response validation (Phase 2) or 3.1-specific structural features (Phase 3).

</domain>

<decisions>
## Implementation Decisions

### Version matching strategy
- Accept any 3.1.x patch version (3.1.0, 3.1.1, etc.) — treat all 3.1 patches the same, mirroring how connexion handles 3.0.x
- Future unsupported versions (3.2.0, 4.0.0) fail with clear error: "OpenAPI X.Y.Z is not supported. Supported versions: 2.0, 3.0.x, 3.1.x"
- Detection is based solely on the `openapi` field value — no content heuristics

### Error messaging & diagnostics
- Philosophy: "Explicit is better than implicit" — fail with clear messages, no silent behavior
- Every validation error includes the detected OAS version (e.g., "OpenAPI 3.1.0 spec validation failed: ...")
- Info-level log on spec load: "Detected OpenAPI 3.1.0 spec, using OpenAPI31Specification handler"

### Meta-schema sourcing
- Bundled in repo at `connexion/resources/schemas/v3.1/schema.json` — same pattern as v2.0 and v3.0
- Pin to the official OAS 3.1.0 release schema (not tracking revisions)

### Backwards-compat behavior
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

</decisions>

<specifics>
## Specific Ideas

- "Explicit is better than implicit" (Zen of Python) — the guiding principle for all error handling in this phase
- SongViber's spec uses `nullable: true` (3.0 pattern) and will need migration to `type: ["string", "null"]` before it validates as 3.1
- Error messages should teach: when rejecting 3.0 patterns, include the 3.1 equivalent

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-spec-detection-schema*
*Context gathered: 2026-02-05*
