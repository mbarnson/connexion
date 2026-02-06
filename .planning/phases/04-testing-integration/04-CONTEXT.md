# Phase 4: Testing & Integration - Context

**Gathered:** 2026-02-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Comprehensive test coverage proving all OAS 3.1 features work correctly, existing tests have zero regressions, and code quality passes lint/type checks. This phase does NOT add new features — it validates everything built in Phases 1-3 and cleans up code quality.

</domain>

<decisions>
## Implementation Decisions

### SongViber Integration Scope
- No cross-repo dependency from connexion to SongViber — connexion tests must be fully self-contained
- Integration test uses a generic OAS 3.1 "kitchen-sink" YAML spec that exercises every 3.1 feature connexion supports (type arrays, const, webhooks, pathItems, nullable rejection, $ref siblings, numeric exclusive bounds, minimal docs, mutualTLS, jsonSchemaDialect, allOf/anyOf/oneOf composition)
- The kitchen-sink spec is a YAML file in connexion's test fixtures (not inline dict)
- Full mock request/response testing through the connexion app — not just load+validate, but actual HTTP round-trips
- Cover all endpoints in the kitchen-sink spec with mock requests
- SongViber-specific validation (proving songviber-api.yaml works) happens in the SongViber repo, not here

### Test Organization Strategy
- Consolidate all 3.1 tests from Phases 1-3 into a consistent structure (e.g., tests/openapi31/ directory)
- Test file organization: Claude's discretion based on connexion's existing patterns
- Kitchen-sink integration spec: YAML file in test fixtures
- Fakeapi handlers for the kitchen-sink spec go in the existing fakeapi module (no new module)

### Regression Verification Approach
- Zero regression = existing test suite passes unchanged
- No new cross-version isolation tests needed — existing suite passing is sufficient proof
- Any existing test failure is a blocker — fix immediately before continuing, zero tolerance
- Full test suite runs after each plan execution (not just 3.1 tests), to catch regressions early
- Test against Python 3.11, 3.12, and 3.13 locally (multi-version via tox or similar)

### CI & Lint Cleanup
- Manual validation only — no GitHub Actions CI pipeline for this fork
- flake8/isort: zero warnings in new/modified files; don't touch files we didn't modify
- mypy: match existing connexion annotation style (function signatures, not every local var)
- Clean sweep: scan all Phase 1-3 code for debug prints, unused imports, unused variables (F841) and remove them (avoiding PR #2043 reviewer issues)

### Claude's Discretion
- Test file organization within the consolidation structure
- Kitchen-sink spec endpoint design (as long as it covers all 3.1 features)
- tox configuration for multi-version testing
- Order of plans within the phase

</decisions>

<specifics>
## Specific Ideas

- Kitchen-sink spec should be a realistic API (not just schema fragments) — every feature exercised through actual endpoints with request/response validation
- PR #2043 had reviewer complaints about unused variables, debug prints, and unused imports — the clean sweep specifically addresses these
- "If the kitchen-sink passes, SongViber's spec will work too" — the kitchen-sink should cover every OAS 3.1 pattern that SongViber uses and more

</specifics>

<deferred>
## Deferred Ideas

- SongViber-specific integration test (validating songviber-api.yaml) — belongs in SongViber repo
- GitHub Actions CI pipeline — may add later if fork becomes long-lived
- Upstream PR to connexion — potential future work after fork is proven

</deferred>

---

*Phase: 04-testing-integration*
*Context gathered: 2026-02-05*
