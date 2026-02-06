# Roadmap: OpenAPI 3.1 Support for Connexion

## Overview

This roadmap delivers comprehensive OpenAPI 3.1.0 support to Connexion through four focused phases: establishing version detection and routing infrastructure, upgrading the validation engine to JSON Schema 2020-12, implementing OAS 3.1 structural features, and proving correctness through comprehensive testing. The journey takes Connexion from "3.1 specs fail to load" to "SongViber's 3.1 spec loads, validates, and generates working code."

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Spec Detection & Schema** - Version routing and meta-schema validation
- [ ] **Phase 2: JSON Schema 2020-12 Validation** - Core validation engine upgrade
- [ ] **Phase 3: OAS 3.1 Features** - Structural features and operation handling
- [ ] **Phase 4: Testing & Integration** - Comprehensive validation and CI

## Phase Details

### Phase 1: Spec Detection & Schema
**Goal**: Connexion correctly detects OpenAPI 3.1.x specs and routes them to dedicated handling with proper meta-schema validation

**Depends on**: Nothing (first phase)

**Requirements**: SPEC-01, SPEC-02, SPEC-04, SPEC-05

**Success Criteria** (what must be TRUE):
  1. A spec with `openapi: "3.1.0"` loads and routes to `OpenAPI31Specification` class (not `OpenAPISpecification`)
  2. The OAS 3.1 meta-schema validates valid 3.1 specs without errors
  3. Error messages reference "3.1.0" when a 3.1 spec fails validation (not "3.0.0")
  4. Swagger 2.0 and OpenAPI 3.0 specs continue routing correctly (no regression)

**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md -- Bundle OAS 3.1 meta-schema, create OpenAPI31Specification class, update version routing
- [x] 01-02-PLAN.md -- Test suite proving version detection, routing, validation, and zero regression

### Phase 2: JSON Schema 2020-12 Validation
**Goal**: All request and response validation for 3.1 specs uses JSON Schema 2020-12 semantics with full support for type arrays, nullable compatibility, and updated keywords

**Depends on**: Phase 1

**Requirements**: VALID-01, VALID-02, VALID-03, VALID-04, VALID-05, VALID-06, VALID-07, VALID-08, VALID-09, VALID-10

**Success Criteria** (what must be TRUE):
  1. Request bodies in 3.1 specs validate using `Draft202012Validator` (not Draft4)
  2. Response bodies in 3.1 specs validate using `Draft202012Validator`
  3. Type arrays work: `type: ["string", "null"]` correctly validates null or string values
  4. Backwards-compatible nullable: `nullable: true` in 3.1 specs is accepted and works identically to type arrays
  5. Numeric exclusive bounds work: `exclusiveMinimum: 5` validates correctly (not as boolean)
  6. The `const` keyword validates values correctly
  7. `$ref` with sibling properties preserves siblings after resolution
  8. Parameter validation respects 3.1 schema semantics
  9. Form data with allOf/anyOf/oneOf composition validates correctly
  10. `unevaluatedProperties` keyword validates correctly in schemas

**Plans**: TBD

Plans:
- [ ] 02-01: TBD during planning

### Phase 3: OAS 3.1 Features
**Goal**: All OpenAPI 3.1 structural features (webhooks, pathItems, minimal docs, mutualTLS, jsonSchemaDialect, $ref siblings) are recognized, parsed, and accessible

**Depends on**: Phase 2

**Requirements**: SPEC-03, FEAT-01, FEAT-02, FEAT-03, FEAT-04, FEAT-05, FEAT-06

**Success Criteria** (what must be TRUE):
  1. The top-level `webhooks` key is parsed and accessible via `OpenAPI31Specification` API
  2. `components/pathItems` can be defined and referenced via `$ref` in paths
  3. Minimal documents (specs without a `paths` key) load without error
  4. The `jsonSchemaDialect` top-level key is recognized and respected during validation
  5. `mutualTLS` security scheme type is recognized by `SecurityHandlerFactory`
  6. `summary` and `description` alongside `$ref` objects are preserved (not stripped)
  7. `OpenAPI31Operation` extends operation handling for 3.1-specific contexts

**Plans**: TBD

Plans:
- [ ] 03-01: TBD during planning

### Phase 4: Testing & Integration
**Goal**: Comprehensive test coverage proves all OAS 3.1 features work correctly, SongViber's spec loads and validates, and all existing tests pass with no regressions

**Depends on**: Phase 3

**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06, TEST-07

**Success Criteria** (what must be TRUE):
  1. SongViber's `songviber-api.yaml` (openapi 3.1.0) loads and validates without errors
  2. All existing Swagger 2.0 tests pass unchanged (zero regression)
  3. All existing OpenAPI 3.0 tests pass unchanged (zero regression)
  4. Every 3.1 feature has dedicated test coverage: type arrays, const, webhooks, pathItems, nullable compat, $ref siblings, numeric exclusive bounds, minimal docs, mutualTLS, jsonSchemaDialect
  5. allOf/anyOf/oneOf form data validation has test fixtures and passing tests
  6. CI passes clean: flake8, isort, mypy with no new warnings
  7. An integration test with a 3.1 spec using all features combined loads and validates successfully

**Plans**: TBD

Plans:
- [ ] 04-01: TBD during planning

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Spec Detection & Schema | 2/2 | ✓ Complete | 2026-02-05 |
| 2. JSON Schema 2020-12 Validation | 0/TBD | Not started | - |
| 3. OAS 3.1 Features | 0/TBD | Not started | - |
| 4. Testing & Integration | 0/TBD | Not started | - |

---
*Last updated: 2026-02-05 (phase 1 complete)*
