# Requirements: OpenAPI 3.1 Support for Connexion

## v1 Requirements

### Spec Infrastructure (SPEC)

- [ ] **SPEC-01**: Connexion detects `openapi: "3.1.x"` and routes to `OpenAPI31Specification` class (version tuple >= (3,1,0))
- [ ] **SPEC-02**: `OpenAPI31Specification` loads and validates specs against the OAS 3.1 JSON meta-schema (`resources/schemas/v3.1/schema.json`)
- [ ] **SPEC-03**: `OpenAPI31Operation` extends operation handling for 3.1-specific features (webhooks, pathItems refs, etc.)
- [ ] **SPEC-04**: Error messages reference 3.1.0 when a 3.1 spec fails validation (not "3.0.0")
- [ ] **SPEC-05**: `Specification.from_dict()` correctly branches: `< (3,0,0)` → Swagger2, `>= (3,0,0) and < (3,1,0)` → OpenAPI3.0, `>= (3,1,0)` → OpenAPI3.1

### JSON Schema 2020-12 Validation (VALID)

- [ ] **VALID-01**: 3.1 specs use `Draft202012Validator` (from jsonschema) for request body validation instead of `Draft4Validator`
- [ ] **VALID-02**: 3.1 specs use `Draft202012Validator` for response body validation
- [ ] **VALID-03**: Type arrays are supported (`type: ["string", "null"]` validates correctly)
- [ ] **VALID-04**: `nullable: true` in 3.1 specs is handled for backwards compatibility (internally mapped to type array)
- [ ] **VALID-05**: `exclusiveMinimum` and `exclusiveMaximum` work as numeric values (not booleans) in 3.1 specs
- [ ] **VALID-06**: `const` keyword validates correctly in 3.1 specs
- [ ] **VALID-07**: `$ref` with sibling properties is preserved and validated (not stripped on resolution)
- [ ] **VALID-08**: Parameter validation uses appropriate validator for 3.1 specs
- [ ] **VALID-09**: Form data validation supports allOf/anyOf/oneOf composition in 3.1 specs
- [ ] **VALID-10**: `unevaluatedProperties` keyword is supported in 3.1 specs

### OAS 3.1 Structural Features (FEAT)

- [ ] **FEAT-01**: Top-level `webhooks` key is parsed and accessible via `OpenAPI31Specification`
- [ ] **FEAT-02**: `components/pathItems` is recognized and resolvable via `$ref`
- [ ] **FEAT-03**: Minimal documents (no `paths` key) load without error — valid in 3.1
- [ ] **FEAT-04**: `jsonSchemaDialect` top-level key is recognized and respected
- [ ] **FEAT-05**: `mutualTLS` security scheme type is recognized by `SecurityHandlerFactory`
- [ ] **FEAT-06**: `summary` and `description` alongside `$ref` objects are preserved

### Testing & Validation (TEST)

- [ ] **TEST-01**: SongViber's `songviber-api.yaml` (openapi 3.1.0) loads and validates without errors
- [ ] **TEST-02**: All existing Swagger 2.0 tests pass unchanged
- [ ] **TEST-03**: All existing OpenAPI 3.0 tests pass unchanged
- [ ] **TEST-04**: Comprehensive test suite covers every 3.1 feature (type arrays, const, webhooks, pathItems, nullable compat, $ref siblings, exclusiveMin/Max, minimal docs, mutualTLS, jsonSchemaDialect)
- [ ] **TEST-05**: allOf/anyOf/oneOf form data has dedicated test fixtures and tests
- [ ] **TEST-06**: CI clean: flake8, isort pass with no new warnings
- [ ] **TEST-07**: 3.1 spec with all features combined loads and validates (integration test)

## v2 Requirements (Deferred)

- Upstream PR preparation (contribution guidelines, maintainer review prep)
- Swagger UI rendering for 3.1-specific features (webhooks display, etc.)
- OpenAPI 3.2 forward compatibility
- Performance optimization of 2020-12 validation (if slower than Draft4)

## Out of Scope

- Python 3.9/3.10 support — we require 3.11+ (simplifies datetime, typing)
- Swagger UI theme/rendering changes — separate concern
- Breaking changes to 3.0/2.0 behavior — zero regression policy
- Documentation beyond code comments — fork for our use

## Traceability

| REQ-ID | Phase | Status |
|--------|-------|--------|
| SPEC-01 | — | pending |
| SPEC-02 | — | pending |
| SPEC-03 | — | pending |
| SPEC-04 | — | pending |
| SPEC-05 | — | pending |
| VALID-01 | — | pending |
| VALID-02 | — | pending |
| VALID-03 | — | pending |
| VALID-04 | — | pending |
| VALID-05 | — | pending |
| VALID-06 | — | pending |
| VALID-07 | — | pending |
| VALID-08 | — | pending |
| VALID-09 | — | pending |
| VALID-10 | — | pending |
| FEAT-01 | — | pending |
| FEAT-02 | — | pending |
| FEAT-03 | — | pending |
| FEAT-04 | — | pending |
| FEAT-05 | — | pending |
| FEAT-06 | — | pending |
| TEST-01 | — | pending |
| TEST-02 | — | pending |
| TEST-03 | — | pending |
| TEST-04 | — | pending |
| TEST-05 | — | pending |
| TEST-06 | — | pending |
| TEST-07 | — | pending |

---
*Last updated: 2026-02-05 after initialization*
