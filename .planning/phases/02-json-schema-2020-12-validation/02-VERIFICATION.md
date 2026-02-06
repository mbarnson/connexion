---
phase: 02-json-schema-2020-12-validation
verified: 2026-02-06T04:41:55Z
status: passed
score: 10/10 must-haves verified
---

# Phase 2: JSON Schema 2020-12 Validation Verification Report

**Phase Goal:** All request and response validation for 3.1 specs uses JSON Schema 2020-12 semantics with full support for type arrays, strict nullable rejection, and updated keywords

**Verified:** 2026-02-06T04:41:55Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Request bodies in 3.1 specs validate using Draft202012Validator (not Draft4) | ✓ VERIFIED | `JSONRequestBodyValidator._validator` returns `Draft202012RequestValidator` when `spec_version >= (3,1,0)` |
| 2 | Response bodies in 3.1 specs validate using Draft202012Validator | ✓ VERIFIED | `JSONResponseBodyValidator.validator` returns `Draft202012ResponseValidator` when `spec_version >= (3,1,0)` |
| 3 | Type arrays work: `type: ["string", "null"]` correctly validates null or string values | ✓ VERIFIED | Test `test_type_array_accepts_string` and `test_type_array_accepts_null` pass |
| 4 | Strict nullable: `nullable: true` in 3.1 specs is rejected at load time with actionable error | ✓ VERIFIED | `OpenAPI31Specification._validate_spec()` detects nullable and provides migration guidance |
| 5 | Numeric exclusive bounds work: `exclusiveMinimum: 5` validates correctly | ✓ VERIFIED | Tests `test_exclusive_minimum_numeric_passes` and `test_exclusive_minimum_numeric_rejects` pass |
| 6 | The `const` keyword validates values correctly | ✓ VERIFIED | Tests `test_const_validates_matching_value` and `test_const_rejects_non_matching_value` pass |
| 7 | `$ref` with sibling properties preserves siblings after resolution | ✓ VERIFIED | `resolve_refs()` preserves siblings when `spec_version >= (3,1,0)` per test `test_resolve_refs_preserves_siblings_for_31` |
| 8 | Parameter validation respects 3.1 schema semantics | ✓ VERIFIED | `ParameterValidator.validate_parameter()` uses `Draft202012Validator` when `spec_version >= (3,1,0)` |
| 9 | Form data with allOf/anyOf/oneOf composition validates correctly | ✓ VERIFIED | `FormDataValidator._validator` uses `Draft202012RequestValidator` for 3.1 specs; test `test_form_data_allof_composition_31` passes |
| 10 | `unevaluatedProperties` keyword validates correctly in schemas | ✓ VERIFIED | Tests `test_unevaluated_properties_rejects_extra` and `test_unevaluated_properties_accepts_declared` pass |

**Score:** 10/10 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `connexion/json_schema.py` | Draft202012 validators and version-aware resolve_refs | ✓ VERIFIED | Lines 173-181: `Draft202012RequestValidator` and `Draft202012ResponseValidator` defined; Lines 73-122: `resolve_refs()` with `spec_version` parameter |
| `connexion/validators/json.py` | Version-aware JSON validators | ✓ VERIFIED | Lines 36, 50-56: `JSONRequestBodyValidator` uses spec_version; Lines 133, 140-146: `JSONResponseBodyValidator` uses spec_version |
| `connexion/validators/parameter.py` | Version-aware parameter validator | ✓ VERIFIED | Lines 28, 49, 58-65: `ParameterValidator` accepts and uses spec_version |
| `connexion/validators/form_data.py` | Version-aware form data validator | ✓ VERIFIED | Lines 33, 47-53: `FormDataValidator` accepts spec_version and selects validator |
| `connexion/middleware/request_validation.py` | Passes spec_version to validators | ✓ VERIFIED | Lines 99, 112, 143: Extracts `spec_version` from operation and passes to parameter and body validators |
| `connexion/middleware/response_validation.py` | Passes spec_version to response validators | ✓ VERIFIED | Lines 95, 125: Extracts `spec_version` and passes to response body validator |
| `tests/test_validation_31.py` | Comprehensive test suite for VALID-* requirements | ✓ VERIFIED | 28 tests covering all 10 VALID requirements, all passing |
| `../songviber/server/openapi/songviber-api.yaml` | 3.1-compliant spec with type arrays | ✓ VERIFIED | Zero `nullable: true` occurrences; 14 type arrays with `"null"`; declares `openapi: 3.1.0` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `request_validation.py` | `validators/json.py` | spec_version in constructor kwargs | ✓ WIRED | Line 143: `spec_version=spec_version` passed to body validator constructor |
| `validators/json.py` | `json_schema.py` | Import Draft202012 validators | ✓ WIRED | Line 13-14: Imports `Draft202012RequestValidator` and `Draft202012ResponseValidator` |
| `validators/json.py` | Draft202012Validator | Conditional selection based on spec_version | ✓ WIRED | Lines 50-56, 140-146: `if self._spec_version >= (3, 1, 0)` branches |
| `response_validation.py` | `validators/json.py` | spec_version in constructor | ✓ WIRED | Line 125: `spec_version=spec_version` passed to response validator |
| `request_validation.py` | `validators/parameter.py` | spec_version in constructor | ✓ WIRED | Line 112: `spec_version=spec_version` passed to ParameterValidator |
| `validators/parameter.py` | Draft202012Validator | Conditional selection in validate_parameter | ✓ WIRED | Lines 58-65: `if spec_version >= (3, 1, 0)` uses Draft202012Validator |
| `validators/form_data.py` | Draft202012RequestValidator | Conditional selection | ✓ WIRED | Lines 47-53: `if self._spec_version >= (3, 1, 0)` uses Draft202012RequestValidator |
| `operations/openapi.py` | `spec.version` | from_spec extracts version | ✓ WIRED | From Plan 02-01: `spec.version` flows to `operation.spec_version` |

### Requirements Coverage

All 10 VALID requirements from Phase 2 are satisfied:

| Requirement | Status | Supporting Truths |
|-------------|--------|-------------------|
| VALID-01: Request body validation uses Draft202012Validator for 3.1 | ✓ SATISFIED | Truth 1 |
| VALID-02: Response body validation uses Draft202012Validator for 3.1 | ✓ SATISFIED | Truth 2 |
| VALID-03: Type arrays supported | ✓ SATISFIED | Truth 3 |
| VALID-04: Nullable rejected with actionable error | ✓ SATISFIED | Truth 4 |
| VALID-05: Numeric exclusive bounds work | ✓ SATISFIED | Truth 5 |
| VALID-06: const keyword validates | ✓ SATISFIED | Truth 6 |
| VALID-07: $ref sibling preservation | ✓ SATISFIED | Truth 7 |
| VALID-08: Parameter validation uses Draft202012 | ✓ SATISFIED | Truth 8 |
| VALID-09: Form data composition validates | ✓ SATISFIED | Truth 9 |
| VALID-10: unevaluatedProperties validates | ✓ SATISFIED | Truth 10 |

### Anti-Patterns Found

**None detected.**

Scanned files:
- `connexion/json_schema.py`
- `connexion/validators/json.py`
- `connexion/validators/parameter.py`
- `connexion/validators/form_data.py`
- `connexion/middleware/request_validation.py`
- `connexion/middleware/response_validation.py`

**Results:**
- Zero TODO/FIXME/HACK comments
- Zero console.log-only implementations
- Zero placeholder returns
- Zero flake8 violations in modified files

### Test Results

**Phase 2 test suite:** `tests/test_validation_31.py`
```
28 tests, 28 passed, 0 failed
Duration: 0.02s
```

**Phase 1 regression check:** `tests/test_spec_31.py`
```
22 tests, 22 passed, 0 failed
Duration: 0.02s
```

**Combined Phase 1+2:**
```
50 tests, 50 passed, 0 failed
```

**Coverage by requirement:**
- VALID-01: 4 tests (validator existence, selection, usage)
- VALID-02: 2 tests (validator selection)
- VALID-03: 4 tests (type arrays with string, null, integer, multi-type)
- VALID-04: 3 tests (rejection, actionable message, 3.0 compatibility)
- VALID-05: 3 tests (exclusive min/max numeric bounds)
- VALID-06: 2 tests (const validates matching/non-matching)
- VALID-07: 2 tests (sibling preservation in 3.1, stripping in 3.0)
- VALID-08: 2 tests (parameter validator selection)
- VALID-09: 2 tests (form data validator selection, allOf composition)
- VALID-10: 2 tests (unevaluatedProperties rejects/accepts)
- Regression: 2 tests (3.0 and 2.0 unchanged)

### Code Quality Verification

**Substantiveness check:**
- `json_schema.py`: Version-aware `resolve_refs()` (49 lines), Draft202012 validators (10 lines)
- `validators/json.py`: Conditional validator selection in 2 classes (6 lines each)
- `validators/parameter.py`: spec_version parameter and conditional selection (18 lines)
- `validators/form_data.py`: spec_version parameter and conditional selection (7 lines)
- `middleware/request_validation.py`: spec_version extraction and passing (3 lines)
- `middleware/response_validation.py`: spec_version extraction and passing (2 lines)

All implementations are substantive, not stubs. Real conditional logic based on spec_version with meaningful behavior differences.

**Wiring check:**
- All validators imported and used in middleware
- spec_version flows from operation → middleware → validators
- Conditional branches tested and verified via test suite
- Zero orphaned code

### SongViber Spec Migration

**Verification:**
```bash
grep -c "nullable: true" songviber-api.yaml → 0 occurrences
grep -c '"null"' songviber-api.yaml → 14 occurrences (type arrays)
openapi version → 3.1.0
YAML validity → valid (parsed successfully)
```

**Sample migrated field:**
```yaml
approved_at:
  type:
    - string
    - "null"
  format: date-time
```

**Migration completeness:** All 14 nullable fields migrated per Plan 02-03 summary.

---

## Summary

**Phase 2 Goal: ACHIEVED**

All 10 success criteria verified:
1. ✓ Request bodies in 3.1 specs use Draft202012Validator
2. ✓ Response bodies in 3.1 specs use Draft202012Validator
3. ✓ Type arrays work correctly
4. ✓ Strict nullable rejection with actionable errors
5. ✓ Numeric exclusive bounds work
6. ✓ const keyword validates
7. ✓ $ref sibling preservation works
8. ✓ Parameter validation uses Draft202012
9. ✓ Form data composition validates
10. ✓ unevaluatedProperties validates

**Evidence quality:** Strong
- 50 automated tests covering all requirements
- All validators structurally verified (imports, conditionals, usage)
- Complete wiring verified from operation → middleware → validators
- Zero regression in existing tests
- SongViber spec successfully migrated

**Confidence level:** High
- All critical paths tested
- Validator selection logic verified both structurally and behaviorally
- Zero gaps, zero anti-patterns
- Ready for Phase 3 (OAS 3.1 Features)

---

_Verified: 2026-02-06T04:41:55Z_
_Verifier: Claude (gsd-verifier)_
_Method: Structural code verification + test suite execution + behavioral validation_
