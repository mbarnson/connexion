# Project: OpenAPI 3.1 Support for Connexion

## What This Is

Add comprehensive OpenAPI 3.1.0 support to Connexion, the Python framework that maps OpenAPI specifications to Python web framework endpoints. This is a clean rewrite (not a port of PR #2043) that covers the full OAS 3.1 specification idiomatically, with JSON Schema 2020-12 validation replacing Draft 4 for 3.1 specs.

## Why It Matters

Connexion currently only supports Swagger 2.0 and OpenAPI 3.0.x. OpenAPI 3.1, released in Feb 2021 and now the dominant version in production, introduces full JSON Schema alignment and features that 3.0 users already expect. Our immediate need: SongViber's `songviber-api.yaml` declares `openapi: 3.1.0` and cannot be loaded by connexion today.

## Core Value

**SongViber's 3.1 spec must load, validate, and generate working code through connexion without errors.** Extended goal: full OAS 3.1 specification compliance for other projects.

## Reference Material

- **PR #2043** (spec-first/connexion): AI-generated attempt at 3.1 support. Good feature inventory but has quality issues (unused vars, dead code, debug prints, reviewer concerns). Use as a reference for WHAT to implement, not HOW.
- **PR #2043 reviewer comments** (chrisinmtown): Identified unused variables, inconsistent refactoring, premature allOf/anyOf form data support, Python 3.9/3.10 datetime compat issues, missing test coverage, debug prints in handlers.
- **OpenAPI 3.1.0 spec**: https://github.com/oai/openapi-specification/blob/main/versions/3.1.0.md
- **JSON Schema 2020-12**: https://json-schema.org/draft/2020-12/schema
- **SongViber API spec**: `../songviber/server/openapi/songviber-api.yaml` — real-world 3.1 spec using allOf, nullable, $ref, enums, additionalProperties

## Constraints

- **Python 3.11+**: We can use modern typing, datetime parsing, and pattern matching
- **Zero existing test breakage**: All Swagger 2.0 and OpenAPI 3.0 tests must continue to pass
- **Backwards compatible**: 3.0 specs must work identically to before. Version detection routes to correct validator/spec class
- **Fork for our use**: Optimized for our needs (SongViber + other projects), not upstream contribution
- **Clean code**: Pass flake8, isort, existing CI checks. No dead code, no debug prints, no unused variables

## SongViber Spec Analysis

The SongViber spec (`openapi: 3.1.0`) uses these features that must work:
- `allOf` composition (JobWithTracks, VibePresetDetails)
- `nullable: true` (3.0-style, must work in 3.1 context for backwards compat)
- `$ref` with component references (parameters, responses, schemas)
- `additionalProperties: true` (ace_step_params)
- Enum types (QualityTier, JobStatus, etc.)
- `format: uuid`, `format: date-time`, `format: uri`, `format: int64`, `format: binary`
- `text/event-stream` content type (SSE)
- Response refs (`$ref: '#/components/responses/...'`)
- Inline schemas in responses
- `security: []` (empty security)

## Key OAS 3.1 Features to Implement

From the full specification:
1. **JSON Schema 2020-12 alignment**: `type` as array, `const`, `$dynamicRef`, `contentMediaType`, etc.
2. **`nullable` removal**: Replace with `type: ["string", "null"]` (but accept `nullable: true` for compat)
3. **`$ref` with siblings**: Allow properties alongside `$ref` (3.0 required `$ref` to be alone)
4. **Webhooks**: New top-level `webhooks` key
5. **PathItems in components**: `components/pathItems`
6. **`exclusiveMinimum`/`exclusiveMaximum` as numbers**: Not booleans (3.0 used boolean+minimum pair)
7. **`mutualTLS` security scheme type**: First-class support
8. **Minimal documents**: Specs without `paths` are valid in 3.1
9. **`jsonSchemaDialect`**: Optional top-level key specifying schema dialect
10. **`summary` on $ref objects**: 3.1 allows summary/description alongside $ref

## Requirements

### Validated

- ✓ Swagger 2.0 spec loading and validation — existing
- ✓ OpenAPI 3.0 spec loading and validation — existing
- ✓ Middleware pipeline (routing, security, validation) — existing
- ✓ Flask and Starlette/ASGI framework support — existing
- ✓ Request/response body validation via jsonschema — existing
- ✓ Parameter validation — existing
- ✓ Security handler framework — existing
- ✓ Resolver system (operationId → function) — existing
- ✓ Test suite passing — existing

### Active

- [ ] OAS 3.1 spec detection and routing (version >= 3.1.0 → new spec class)
- [ ] OAS 3.1 JSON meta-schema for spec validation
- [ ] JSON Schema 2020-12 validators for request/response bodies
- [ ] Type array support (`type: ["string", "null"]`)
- [ ] Backwards-compatible `nullable: true` handling in 3.1 specs
- [ ] `$ref` with sibling properties
- [ ] `exclusiveMinimum`/`exclusiveMaximum` as numeric values
- [ ] Webhooks top-level key
- [ ] PathItems in components
- [ ] `const` keyword support
- [ ] Minimal documents (no `paths` key)
- [ ] `mutualTLS` security scheme type
- [ ] `jsonSchemaDialect` support
- [ ] `summary`/`description` alongside `$ref`
- [ ] SongViber spec loads and validates without errors
- [ ] allOf/anyOf/oneOf in form data (valid per 3.1 spec)
- [ ] Comprehensive test suite for all 3.1 features
- [ ] Clean CI: flake8, isort, no warnings

### Out of Scope

- Upstream PR preparation — this is a fork for our use
- Python 3.9/3.10 support — we're 3.11+ only
- Swagger UI 3.1 rendering changes — UI changes are separate
- OpenAPI 3.2 forward-looking changes — not published yet
- Performance optimization — correctness first

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Clean rewrite over PR port | PR #2043 has quality issues, reviewer flagged dead code, unused vars, debug prints | Write from scratch using PR as feature reference |
| Python 3.11+ only | Simplifies datetime, typing; matches our deployment target | Drop 3.9/3.10 compat |
| Fork, not upstream PR | Optimized for our timeline and needs | Branch in our repo |
| Zero test breakage | 3.0/2.0 must work identically | Add new tests, don't modify existing |
| Full 3.1 spec coverage | "If it's valid in the spec, it should be valid here" | Implement every 3.1 feature |
| `nullable: true` compat in 3.1 | SongViber spec uses it; common in real-world 3.1 specs | Accept both forms |
| allOf/anyOf/oneOf in form data | Valid per 3.1 spec, even though 3.0 didn't support it | Include in scope |

---
*Last updated: 2026-02-05 after initialization*
