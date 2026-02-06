# Project: OpenAPI 3.1 Support for Connexion

## What This Is

A fork of Connexion with comprehensive OpenAPI 3.1.0 support, including JSON Schema 2020-12 validation, full structural feature coverage (webhooks, pathItems, minimal documents, mutualTLS, jsonSchemaDialect), and strict nullable rejection. Ships as a drop-in replacement for connexion with 3.1 specs.

## Why It Matters

Connexion upstream only supports Swagger 2.0 and OpenAPI 3.0.x. OpenAPI 3.1, released in Feb 2021 and now the dominant version in production, introduces full JSON Schema alignment and features that 3.0 users already expect. SongViber's API spec declares `openapi: 3.1.0` and requires this fork.

## Core Value

**SongViber's 3.1 spec must load, validate, and generate working code through connexion without errors.** Extended goal: full OAS 3.1 specification compliance for other projects.

## Reference Material

- **PR #2043** (spec-first/connexion): AI-generated attempt at 3.1 support. Used as feature reference, not ported.
- **OpenAPI 3.1.0 spec**: https://github.com/oai/openapi-specification/blob/main/versions/3.1.0.md
- **JSON Schema 2020-12**: https://json-schema.org/draft/2020-12/schema
- **SongViber API spec**: `../songviber/server/openapi/songviber-api.yaml`

## Constraints

- **Python 3.11+**: Modern typing, datetime parsing, pattern matching
- **Zero existing test breakage**: All Swagger 2.0 and OpenAPI 3.0 tests pass unchanged
- **Backwards compatible**: Version detection routes to correct validator/spec class
- **Fork for our use**: Optimized for our needs (SongViber + other projects)
- **Clean code**: Pass flake8, isort, existing CI checks

## Context

Shipped v1.0 with 3,649 net lines of Python across 21 files.
Tech stack: Python 3.11+, jsonschema (Draft202012Validator), pytest.
912 total tests (110 new OAS 3.1 + 802 existing), zero regression.
SongViber spec migrated to 3.1 type arrays (14 fields, zero nullable: true remaining).

## Requirements

### Validated

- ✓ Swagger 2.0 spec loading and validation — existing
- ✓ OpenAPI 3.0 spec loading and validation — existing
- ✓ Middleware pipeline (routing, security, validation) — existing
- ✓ Flask and Starlette/ASGI framework support — existing
- ✓ Request/response body validation via jsonschema — existing
- ✓ Parameter validation — existing
- ✓ Security handler framework — existing
- ✓ Resolver system (operationId -> function) — existing
- ✓ Test suite passing — existing
- ✓ OAS 3.1 spec detection and routing — v1.0
- ✓ OAS 3.1 JSON meta-schema for spec validation — v1.0
- ✓ JSON Schema 2020-12 validators for request/response bodies — v1.0
- ✓ Type array support (`type: ["string", "null"]`) — v1.0
- ✓ Strict nullable rejection (`nullable: true` rejected at load time) — v1.0
- ✓ `$ref` with sibling properties preserved — v1.0
- ✓ `exclusiveMinimum`/`exclusiveMaximum` as numeric values — v1.0
- ✓ Webhooks top-level key — v1.0
- ✓ PathItems in components — v1.0
- ✓ `const` keyword support — v1.0
- ✓ Minimal documents (no `paths` key) — v1.0
- ✓ `mutualTLS` security scheme type — v1.0
- ✓ `jsonSchemaDialect` support — v1.0
- ✓ `summary`/`description` alongside `$ref` — v1.0
- ✓ SongViber spec loads and validates without errors — v1.0
- ✓ allOf/anyOf/oneOf in form data — v1.0
- ✓ Comprehensive test suite for all 3.1 features (110 tests) — v1.0
- ✓ Clean CI: flake8, isort, no warnings — v1.0

### Active

(None — all v1.0 requirements shipped)

### Out of Scope

- Upstream PR preparation — this is a fork for our use
- Python 3.9/3.10 support — we're 3.11+ only
- Swagger UI 3.1 rendering changes — UI changes are separate
- OpenAPI 3.2 forward-looking changes — not published yet
- Performance optimization of 2020-12 validation — correctness shipped, perf if needed later

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Clean rewrite over PR port | PR #2043 has quality issues | ✓ Good — clean, lint-free code |
| Python 3.11+ only | Simplifies datetime, typing; matches deployment target | ✓ Good — no compat issues |
| Fork, not upstream PR | Optimized for our timeline and needs | ✓ Good — shipped in 2 days |
| Zero test breakage | 3.0/2.0 must work identically | ✓ Good — 802 legacy tests pass |
| Full 3.1 spec coverage | "If it's valid in the spec, it should be valid here" | ✓ Good — all 10 features implemented |
| Strict nullable rejection | SongViber spec updated to use type arrays | ✓ Good — enforces correct 3.1 usage |
| allOf/anyOf/oneOf in form data | Valid per 3.1 spec | ✓ Good — tested in kitchen-sink |
| OpenAPI31Specification as sibling class | Avoids inheritance complexity | ✓ Good — clean separation |
| Version-aware resolve_refs | Preserves $ref siblings for 3.1, legacy for 3.0 | ✓ Good — zero regression |
| mutualTLS via security_passthrough | Avoids middleware ordering conflicts | ✓ Good — matches deployment patterns |
| Inline test fixtures over YAML files | Self-contained, fast tests | ✓ Good — easy to maintain |

---
*Last updated: 2026-02-06 after v1.0 milestone*
