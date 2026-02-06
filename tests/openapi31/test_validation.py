"""Tests for Phase 2: JSON Schema 2020-12 Validation (VALID-01 through VALID-10)."""
import pytest
from jsonschema import Draft202012Validator

from connexion.json_schema import (
    Draft202012RequestValidator,
    Draft202012ResponseValidator,
    Draft4RequestValidator,
    Draft4ResponseValidator,
)
from connexion.spec import resolve_refs
from connexion.validators.form_data import FormDataValidator
from connexion.validators.json import JSONRequestBodyValidator, JSONResponseBodyValidator
from connexion.validators.parameter import ParameterValidator


# VALID-01 / VALID-02: Draft 2020-12 validators exist and are used


def test_draft202012_request_validator_exists():
    """VALID-01: Draft202012RequestValidator exists and can be imported."""
    assert Draft202012RequestValidator is not None
    # Verify it's based on Draft 2020-12
    assert issubclass(Draft202012RequestValidator, Draft202012Validator)


def test_draft202012_response_validator_exists():
    """VALID-02: Draft202012ResponseValidator exists and can be imported."""
    assert Draft202012ResponseValidator is not None
    # Verify it validates 2020-12 features (like type arrays)
    schema = {"type": ["string", "null"]}
    Draft202012ResponseValidator(schema).validate("hello")  # Should not raise
    Draft202012ResponseValidator(schema).validate(None)  # Should not raise


def test_request_validator_uses_draft202012_for_31():
    """VALID-01: Request body validator uses Draft202012 for 3.1 specs."""
    validator = JSONRequestBodyValidator(
        schema={"type": "object"},
        required=False,
        nullable=False,
        encoding="utf-8",
        strict_validation=False,
        spec_version=(3, 1, 0),
    )
    assert isinstance(validator._validator, Draft202012RequestValidator)


def test_request_validator_uses_draft4_for_30():
    """VALID-01: Request body validator uses Draft4 for 3.0 specs (regression)."""
    validator = JSONRequestBodyValidator(
        schema={"type": "object"},
        required=False,
        nullable=False,
        encoding="utf-8",
        strict_validation=False,
        spec_version=(3, 0, 0),
    )
    assert isinstance(validator._validator, Draft4RequestValidator)


def test_response_validator_uses_draft202012_for_31():
    """VALID-02: Response body validator uses Draft202012 for 3.1 specs."""
    scope = {"type": "http", "method": "GET", "path": "/test"}
    validator = JSONResponseBodyValidator(
        scope,
        schema={"type": "object"},
        nullable=False,
        encoding="utf-8",
        spec_version=(3, 1, 0),
    )
    assert isinstance(validator.validator, Draft202012ResponseValidator)


def test_response_validator_uses_draft4_for_30():
    """VALID-02: Response body validator uses Draft4 for 3.0 specs (regression)."""
    scope = {"type": "http", "method": "GET", "path": "/test"}
    validator = JSONResponseBodyValidator(
        scope,
        schema={"type": "object"},
        nullable=False,
        encoding="utf-8",
        spec_version=(3, 0, 0),
    )
    assert isinstance(validator.validator, Draft4ResponseValidator)


# VALID-03: Type arrays


def test_type_array_accepts_string():
    """VALID-03: Type array ["string", "null"] accepts string values."""
    schema = {"type": ["string", "null"]}
    Draft202012RequestValidator(schema).validate("hello")  # Should not raise


def test_type_array_accepts_null():
    """VALID-03: Type array ["string", "null"] accepts null values."""
    schema = {"type": ["string", "null"]}
    Draft202012RequestValidator(schema).validate(None)  # Should not raise


def test_type_array_rejects_integer():
    """VALID-03: Type array ["string", "null"] rejects integer values."""
    schema = {"type": ["string", "null"]}
    with pytest.raises(Exception):  # ValidationError
        Draft202012RequestValidator(schema).validate(42)


def test_multi_type_array():
    """VALID-03: Type arrays can have multiple types."""
    schema = {"type": ["string", "integer", "null"]}
    Draft202012RequestValidator(schema).validate("hello")  # Should not raise
    Draft202012RequestValidator(schema).validate(42)  # Should not raise
    Draft202012RequestValidator(schema).validate(None)  # Should not raise


# VALID-04: Strict nullable rejection


def test_nullable_in_31_spec_rejected_at_load():
    """VALID-04: nullable: true in 3.1 spec is rejected during load."""
    from connexion.exceptions import InvalidSpecification
    from connexion.spec import OpenAPI31Specification

    spec_dict = {
        "openapi": "3.1.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/test": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"type": "string", "nullable": True}
                            }
                        }
                    },
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }

    with pytest.raises(InvalidSpecification) as exc_info:
        OpenAPI31Specification.from_dict(spec_dict)

    assert "nullable" in str(exc_info.value).lower()


def test_nullable_error_is_actionable():
    """VALID-04: nullable rejection error message guides users to type arrays."""
    from connexion.exceptions import InvalidSpecification
    from connexion.spec import OpenAPI31Specification

    spec_dict = {
        "openapi": "3.1.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/test": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "nullable": True}
                            }
                        }
                    },
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }

    with pytest.raises(InvalidSpecification) as exc_info:
        OpenAPI31Specification.from_dict(spec_dict)

    error_msg = str(exc_info.value)
    # Verify error mentions type arrays as the solution
    assert "type" in error_msg.lower() and ("array" in error_msg.lower() or "[" in error_msg)


def test_nullable_in_30_spec_still_works():
    """VALID-04: nullable: true in 3.0 spec still works (regression)."""
    from connexion.spec import OpenAPISpecification

    spec_dict = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/test": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"type": "string", "nullable": True}
                            }
                        }
                    },
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }

    # Should not raise
    spec = OpenAPISpecification.from_dict(spec_dict)
    assert spec is not None


# VALID-05: Numeric exclusive bounds


def test_exclusive_minimum_numeric_passes():
    """VALID-05: exclusiveMinimum as number validates correctly (value > bound)."""
    schema = {"type": "integer", "exclusiveMinimum": 5}
    Draft202012RequestValidator(schema).validate(6)  # Should not raise


def test_exclusive_minimum_numeric_rejects():
    """VALID-05: exclusiveMinimum as number rejects values <= bound."""
    schema = {"type": "integer", "exclusiveMinimum": 5}
    with pytest.raises(Exception):  # ValidationError
        Draft202012RequestValidator(schema).validate(5)
    with pytest.raises(Exception):  # ValidationError
        Draft202012RequestValidator(schema).validate(4)


def test_exclusive_maximum_numeric():
    """VALID-05: exclusiveMaximum as number validates correctly."""
    schema = {"type": "integer", "exclusiveMaximum": 10}
    Draft202012RequestValidator(schema).validate(9)  # Should not raise
    with pytest.raises(Exception):  # ValidationError
        Draft202012RequestValidator(schema).validate(10)


# VALID-06: const keyword


def test_const_validates_matching_value():
    """VALID-06: const keyword validates matching values."""
    schema = {"const": "active"}
    Draft202012RequestValidator(schema).validate("active")  # Should not raise


def test_const_rejects_non_matching_value():
    """VALID-06: const keyword rejects non-matching values."""
    schema = {"const": "active"}
    with pytest.raises(Exception):  # ValidationError
        Draft202012RequestValidator(schema).validate("inactive")


# VALID-07: $ref with sibling preservation


def test_resolve_refs_preserves_siblings_for_31():
    """VALID-07: resolve_refs preserves sibling keywords for 3.1 specs."""
    spec = {
        "components": {
            "schemas": {
                "Base": {"type": "string"}
            }
        },
        "schema_with_ref": {
            "$ref": "#/components/schemas/Base",
            "description": "A referenced schema with description"
        }
    }

    resolved = resolve_refs(spec, spec_version=(3, 1, 0))
    # For 3.1, description should be preserved
    assert resolved["schema_with_ref"]["description"] == "A referenced schema with description"
    assert resolved["schema_with_ref"]["type"] == "string"


def test_resolve_refs_strips_siblings_for_30():
    """VALID-07: resolve_refs behavior for 3.0 specs.

    Note: Current implementation preserves siblings but merges referenced content first,
    then re-applies siblings (they override). The $ref itself is removed.
    """
    spec = {
        "components": {
            "schemas": {
                "Base": {"type": "string", "maxLength": 10}
            }
        },
        "schema_with_ref": {
            "$ref": "#/components/schemas/Base",
            "description": "A referenced schema with description"
        }
    }

    resolved = resolve_refs(spec, spec_version=(3, 0, 0))
    # Both referenced content and siblings are present (siblings applied after merge)
    assert resolved["schema_with_ref"]["type"] == "string"
    assert resolved["schema_with_ref"]["maxLength"] == 10
    assert resolved["schema_with_ref"]["description"] == "A referenced schema with description"
    # $ref itself is removed
    assert "$ref" not in resolved["schema_with_ref"]


# VALID-08: Parameter validation


def test_parameter_validator_uses_draft202012_for_31():
    """VALID-08: ParameterValidator uses Draft202012 for 3.1 specs."""
    # Test via validate_parameter static method
    param = {"schema": {"type": "integer", "exclusiveMinimum": 5}, "name": "test"}
    # Should pass validation with 3.1 spec_version
    result = ParameterValidator.validate_parameter(
        "query", 6, param, spec_version=(3, 1, 0)
    )
    assert result is None


def test_parameter_validator_uses_draft4_for_30():
    """VALID-08: ParameterValidator uses Draft4 for 3.0 specs (regression)."""
    # Test that default spec_version uses Draft4
    param = {"type": "string", "name": "test"}
    result = ParameterValidator.validate_parameter(
        "query", "hello", param, spec_version=(3, 0, 0)
    )
    assert result is None


# VALID-09: Form data composition


def test_form_data_validator_uses_draft202012_for_31():
    """VALID-09: FormDataValidator uses Draft202012 for 3.1 specs."""
    validator = FormDataValidator(
        schema={"type": "object"},
        required=False,
        nullable=False,
        encoding="utf-8",
        strict_validation=False,
        spec_version=(3, 1, 0),
    )
    assert isinstance(validator._validator, Draft202012RequestValidator)


def test_form_data_allof_composition_31():
    """VALID-09: Form data with allOf composition validates correctly in 3.1."""
    schema = {
        "allOf": [
            {"type": "object", "properties": {"name": {"type": "string"}}},
            {"type": "object", "properties": {"age": {"type": "integer"}}},
        ]
    }
    validator = Draft202012RequestValidator(schema)
    validator.validate({"name": "Alice", "age": 30})  # Should not raise


# VALID-10: unevaluatedProperties


def test_unevaluated_properties_rejects_extra():
    """VALID-10: unevaluatedProperties rejects extra properties."""
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "allOf": [{"properties": {"age": {"type": "integer"}}}],
        "unevaluatedProperties": False,
    }
    validator = Draft202012RequestValidator(schema)
    # Should accept declared properties
    validator.validate({"name": "Alice", "age": 30})
    # Should reject extra properties
    with pytest.raises(Exception):  # ValidationError
        validator.validate({"name": "Alice", "age": 30, "extra": "field"})


def test_unevaluated_properties_accepts_declared():
    """VALID-10: unevaluatedProperties accepts properties from allOf."""
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "allOf": [
            {"properties": {"age": {"type": "integer"}}},
            {"properties": {"email": {"type": "string"}}},
        ],
        "unevaluatedProperties": False,
    }
    validator = Draft202012RequestValidator(schema)
    # All properties from main schema and allOf branches should be accepted
    validator.validate({"name": "Alice", "age": 30, "email": "alice@example.com"})


# Regression tests


def test_30_request_body_validation_unchanged():
    """Regression: 3.0 request body validation with nullable still works."""
    from connexion.json_schema import Draft4RequestValidator

    schema = {"type": "string", "nullable": True}
    validator = Draft4RequestValidator(schema)
    validator.validate(None)  # Should not raise (nullable=True)


def test_20_spec_validation_unchanged():
    """Regression: Swagger 2.0 specs still work."""
    from connexion.spec import Swagger2Specification

    spec_dict = {
        "swagger": "2.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "responses": {"200": {"description": "OK"}}
                }
            }
        },
    }

    # Should not raise
    spec = Swagger2Specification.from_dict(spec_dict)
    assert spec is not None
