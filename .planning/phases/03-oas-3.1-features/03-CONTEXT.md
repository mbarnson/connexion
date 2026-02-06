# Phase 3: OAS 3.1 Features - Context

**Gathered:** 2026-02-05
**Status:** Ready for planning

<domain>
## Phase Boundary

All OpenAPI 3.1 structural features (webhooks, pathItems, minimal docs, mutualTLS, jsonSchemaDialect, $ref siblings) are recognized, parsed, and accessible through connexion. An `OpenAPI31Operation` class handles 3.1-specific operation contexts. Full support where feasible — not just "don't crash."

</domain>

<decisions>
## Implementation Decisions

### OpenAPI31Operation scope
- Claude's discretion on class scope — pick what the codebase needs
- Options range from minimal ($ref sibling preservation only) to full 3.1 context carrier (jsonSchemaDialect, webhook origin, pathItem refs)
- Decision should be driven by what downstream code actually needs, not theoretical completeness

### Feature depth — full support where feasible
- All 3.1 structural features should be fully supported, not just parsed-without-error
- Webhooks: parsed, validated, exposed via API (e.g., `spec.webhooks`)
- pathItems: `components/pathItems` resolvable via `$ref` in paths
- Minimal docs: specs without `paths` key load without error
- jsonSchemaDialect: recognized and respected during validation
- mutualTLS: recognized by `SecurityHandlerFactory`
- $ref siblings: `summary`/`description` alongside `$ref` preserved (not stripped)

### mutualTLS handling
- Claude's discretion — pick approach that avoids the known security/middleware conflict
- Known pitfall: connexion security handlers run BEFORE middleware; SongViber uses custom AuthMiddleware for mTLS
- Must not break the pattern where `security: []` at root level lets middleware handle auth

### Webhook dispatch
- Claude's discretion — pick what's feasible within connexion's architecture
- Connexion has no webhook receiver infrastructure today
- Parse + API exposure is minimum; full operationId dispatch is stretch goal
- Don't overengineer — if dispatch requires major new routing infrastructure, defer it

### Claude's Discretion
- OpenAPI31Operation class design (inheritance, scope, what it carries)
- mutualTLS implementation approach (recognize-only vs handler)
- Webhook dispatch depth (parse+API vs full routing)
- pathItem $ref resolution implementation strategy
- jsonSchemaDialect enforcement depth

</decisions>

<specifics>
## Specific Ideas

- "Full support where feasible" — user wants maximum spec compliance, not minimum viable
- User explicitly chose "you decide" for operation scope, mTLS approach, and webhook dispatch — trusts Claude to pick the right level based on architecture
- SongViber doesn't currently use webhooks or pathItems, but the fork should support them properly for spec compliance

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-oas-3.1-features*
*Context gathered: 2026-02-05*
