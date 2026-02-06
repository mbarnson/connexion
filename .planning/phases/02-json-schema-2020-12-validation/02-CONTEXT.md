# Phase 2: JSON Schema 2020-12 Validation - Context

**Gathered:** 2026-02-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Upgrade connexion's validation engine so that OpenAPI 3.1 specs validate request bodies, response bodies, parameters, and form data using JSON Schema 2020-12 semantics (`Draft202012Validator`) instead of Draft 4. All 3.0/2.0 specs continue using their existing validators with zero regression.

</domain>

<decisions>
## Implementation Decisions

### Nullable handling
- **Strict rejection**: `nullable: true` in a 3.1 spec is an error, NOT auto-converted to type arrays
- Rejection happens at **spec load time** (meta-schema validation), not at request/response validation time
- Error message must be **actionable**: tell the author exactly what to write instead (e.g. "Use `type: [\"string\", \"null\"]` instead of `nullable: true`")
- SongViber spec will be updated to proper 3.1 patterns (`type: ["string", "null"]`) as part of this phase
- This overrides the original roadmap success criterion #4 (backwards-compatible nullable)

### $ref sibling handling
- **Full schema siblings**: any JSON Schema keyword alongside `$ref` is preserved, not just `summary`/`description`
- Conflict resolution: Claude's discretion, following JSON Schema 2020-12 semantics (`$ref` as applicator)
- $ref resolution timing (eager vs lazy): Claude's discretion based on existing connexion behavior
- SongViber only uses basic `$ref` — full sibling support is for spec correctness

### Form data composition
- **Implement now** for spec completeness, even though SongViber doesn't use form data content types
- allOf/anyOf/oneOf in `multipart/form-data` and `application/x-www-form-urlencoded` schemas must validate correctly
- Strictness on extra fields and `oneOf` matching: Claude's discretion, following existing connexion patterns and JSON Schema 2020-12 semantics

### Error message style
- Follow existing connexion error patterns for all 3.1-specific keywords (`const`, `unevaluatedProperties`, type arrays, exclusive bounds)
- Whether to include JSON Schema draft info in errors: Claude's discretion
- Whether to expand type arrays in error messages: Claude's discretion

### Claude's Discretion
- Error message formatting details (draft info, type expansion, bound values)
- $ref resolution timing and conflict resolution approach
- Form data strictness on extra fields and oneOf matching
- How to integrate Draft202012Validator into existing validator classes

</decisions>

<specifics>
## Specific Ideas

- Nullable rejection error should be developer-friendly: show the exact fix, not just "invalid keyword"
- SongViber spec update from `nullable: true` to `type: ["type", "null"]` is in scope for this phase
- Form data composition included for "full 3.1 spec coverage" principle — if it's valid in the spec, it should be valid here

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-json-schema-2020-12-validation*
*Context gathered: 2026-02-05*
