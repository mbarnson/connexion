# Project Milestones: OpenAPI 3.1 Support for Connexion

## v1.0 OpenAPI 3.1 Support (Shipped: 2026-02-06)

**Delivered:** Comprehensive OpenAPI 3.1.0 support for Connexion with JSON Schema 2020-12 validation, full structural feature coverage, and 110 new tests proving correctness with zero regression.

**Phases completed:** 1-4 (11 plans total)

**Key accomplishments:**

- OpenAPI 3.1 spec detection and three-way version routing (2.0/3.0/3.1)
- JSON Schema 2020-12 validation engine for request bodies, response bodies, parameters, and form data
- Strict nullable rejection with actionable migration guidance to type arrays
- OAS 3.1 structural features: webhooks, pathItems, minimal documents, jsonSchemaDialect, mutualTLS, $ref sibling preservation
- SongViber spec migrated from nullable: true to type arrays (14 fields)
- Comprehensive test suite with kitchen-sink integration fixture exercising every 3.1 feature via HTTP round-trips

**Stats:**

- 21 files created/modified
- 3,649 net lines of Python
- 4 phases, 11 plans, ~22 tasks
- 2 days from project init to ship
- 912 total tests (110 new OAS 3.1 + 802 existing, zero regression)

**Git range:** `18e0583` (docs: initialize project) → `67228d0` (docs(04): complete)

**What's next:** Pin SongViber server to this fork, begin SongViber server development.

---
