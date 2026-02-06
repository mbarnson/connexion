"""Tests for OpenAPI 3.1 spec detection, routing, and validation (Phase 1).

Covers requirements: SPEC-01, SPEC-02, SPEC-04, SPEC-05
"""
import json
import pkgutil

import pytest
from connexion.exceptions import InvalidSpecification
from connexion.spec import (
    OpenAPI31Specification,
    OpenAPISpecification,
    Specification,
    Swagger2Specification,
)


# ============================================================================
# Helper fixtures
# ============================================================================


@pytest.fixture
def valid_31_spec():
    """Minimal valid OpenAPI 3.1.0 spec."""
    return {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
    }


@pytest.fixture
def valid_30_spec():
    """Minimal valid OpenAPI 3.0.0 spec."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
    }


@pytest.fixture
def valid_20_spec():
    """Minimal valid Swagger 2.0 spec."""
    return {
        "swagger": "2.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
        "basePath": "/",
    }


# ============================================================================
# SPEC-01: Version detection routes to OpenAPI31Specification
# ============================================================================


def test_31_spec_routes_to_openapi31_specification(valid_31_spec):
    """from_dict() with openapi: 3.1.0 returns OpenAPI31Specification."""
    spec = Specification.from_dict(valid_31_spec)
    assert isinstance(spec, OpenAPI31Specification)


@pytest.mark.parametrize("version", ["3.1.0", "3.1.1", "3.1.2"])
def test_31_patch_versions_route_correctly(valid_31_spec, version):
    """All 3.1.x patch versions route to OpenAPI31Specification."""
    valid_31_spec["openapi"] = version
    spec = Specification.from_dict(valid_31_spec)
    assert isinstance(spec, OpenAPI31Specification)
    assert spec.version[0] == 3
    assert spec.version[1] == 1


# ============================================================================
# SPEC-05: Three-way version branching (2.0, 3.0.x, 3.1.x)
# ============================================================================


def test_30_spec_routes_to_openapi_specification(valid_30_spec):
    """from_dict() with openapi: 3.0.0 returns OpenAPISpecification."""
    spec = Specification.from_dict(valid_30_spec)
    assert isinstance(spec, OpenAPISpecification)
    assert not isinstance(spec, OpenAPI31Specification)


@pytest.mark.parametrize("version", ["3.0.0", "3.0.1", "3.0.3"])
def test_30_patch_versions_route_correctly(valid_30_spec, version):
    """All 3.0.x patch versions route to OpenAPISpecification."""
    valid_30_spec["openapi"] = version
    spec = Specification.from_dict(valid_30_spec)
    assert isinstance(spec, OpenAPISpecification)
    assert not isinstance(spec, OpenAPI31Specification)
    assert spec.version[0] == 3
    assert spec.version[1] == 0


def test_20_spec_routes_to_swagger2_specification(valid_20_spec):
    """from_dict() with swagger: 2.0 returns Swagger2Specification."""
    spec = Specification.from_dict(valid_20_spec)
    assert isinstance(spec, Swagger2Specification)


def test_unsupported_version_raises_error():
    """from_dict() with openapi: 4.0.0 raises InvalidSpecification with helpful message."""
    spec_dict = {
        "openapi": "4.0.0",
        "info": {"title": "Future Spec", "version": "1.0.0"},
        "paths": {},
    }
    with pytest.raises(InvalidSpecification) as exc_info:
        Specification.from_dict(spec_dict)

    error_msg = str(exc_info.value)
    assert "4.0.0" in error_msg
    assert "not supported" in error_msg
    assert "Supported versions: 2.0, 3.0.x, 3.1.x" in error_msg


def test_missing_version_raises_error():
    """from_dict() with no version field raises InvalidSpecification."""
    spec_dict = {"info": {"title": "No Version", "version": "1.0.0"}, "paths": {}}
    with pytest.raises(InvalidSpecification) as exc_info:
        Specification.from_dict(spec_dict)

    error_msg = str(exc_info.value)
    assert "3.1.x" in error_msg  # Error message mentions supported versions


def test_invalid_version_string_raises_error():
    """from_dict() with malformed version raises InvalidSpecification."""
    spec_dict = {
        "openapi": "not.a.version",
        "info": {"title": "Bad Version", "version": "1.0.0"},
        "paths": {},
    }
    with pytest.raises(InvalidSpecification) as exc_info:
        Specification.from_dict(spec_dict)

    error_msg = str(exc_info.value)
    assert "Unable to convert version string" in error_msg


# ============================================================================
# SPEC-02: Meta-schema validates valid specs
# ============================================================================


def test_valid_31_spec_validates_successfully(valid_31_spec):
    """A valid minimal 3.1 spec passes validation without exception."""
    spec = Specification.from_dict(valid_31_spec)
    assert spec is not None
    assert isinstance(spec, OpenAPI31Specification)


def test_invalid_31_spec_missing_info_fails():
    """A 3.1 spec without info field raises InvalidSpecification."""
    invalid_spec = {
        "openapi": "3.1.0",
        "paths": {},
    }
    with pytest.raises(InvalidSpecification) as exc_info:
        Specification.from_dict(invalid_spec)

    error_msg = str(exc_info.value)
    assert "3.1.0" in error_msg  # Error mentions the version
    # The error should mention validation failure
    assert "validation failed" in error_msg.lower() or "required" in error_msg.lower()


def test_invalid_31_spec_missing_openapi_field_fails():
    """A spec claiming to be 3.1 but missing openapi field raises error."""
    invalid_spec = {
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {},
    }
    # This will fail at version detection, not validation
    with pytest.raises(InvalidSpecification) as exc_info:
        Specification.from_dict(invalid_spec)

    error_msg = str(exc_info.value)
    # Should mention missing version fields
    assert "openapi" in error_msg.lower() or "swagger" in error_msg.lower()


def test_bundled_schema_is_valid_json():
    """The bundled v3.1 schema loads and parses as valid JSON."""
    schema_data = pkgutil.get_data("connexion", "resources/schemas/v3.1/schema.json")
    assert schema_data is not None
    schema = json.loads(schema_data)
    assert isinstance(schema, dict)


def test_bundled_schema_uses_draft_2020_12():
    """The bundled schema's $schema field references Draft 2020-12."""
    schema_data = pkgutil.get_data("connexion", "resources/schemas/v3.1/schema.json")
    schema = json.loads(schema_data)
    assert "$schema" in schema
    assert "draft/2020-12" in schema["$schema"]


def test_bundled_schema_has_31_version_pattern():
    """The schema's openapi property pattern matches 3.1.x versions."""
    schema_data = pkgutil.get_data("connexion", "resources/schemas/v3.1/schema.json")
    schema = json.loads(schema_data)

    # Navigate to the openapi field definition
    # The structure is: properties -> openapi -> pattern
    assert "properties" in schema
    assert "openapi" in schema["properties"]
    openapi_prop = schema["properties"]["openapi"]

    # Check that the pattern accepts 3.1.x versions
    if "pattern" in openapi_prop:
        pattern = openapi_prop["pattern"]
        # Pattern should match "3.1.0", "3.1.1", etc.
        # The actual pattern is: ^3\\.1\\.\\d+(-.+)?$
        assert "3" in pattern and "1" in pattern
    elif "const" in openapi_prop:
        # Some schemas use const instead of pattern
        const_value = openapi_prop["const"]
        assert const_value.startswith("3.1")


# ============================================================================
# SPEC-04: Error messages reference 3.1.0
# ============================================================================


def test_validation_error_includes_version():
    """When a 3.1 spec fails validation, error message contains '3.1.0'."""
    invalid_spec = {
        "openapi": "3.1.0",
        # Missing required 'info' field
        "paths": {},
    }
    with pytest.raises(InvalidSpecification) as exc_info:
        Specification.from_dict(invalid_spec)

    error_msg = str(exc_info.value)
    assert "3.1" in error_msg  # Error references the detected version


def test_unsupported_version_error_message_format():
    """Error for unsupported version contains version and supported list."""
    spec_dict = {
        "openapi": "4.0.0",
        "info": {"title": "Future", "version": "1.0.0"},
        "paths": {},
    }
    with pytest.raises(InvalidSpecification) as exc_info:
        Specification.from_dict(spec_dict)

    error_msg = str(exc_info.value)
    assert "4.0.0" in error_msg
    assert "Supported versions" in error_msg
    assert "2.0" in error_msg
    assert "3.0.x" in error_msg
    assert "3.1.x" in error_msg


# ============================================================================
# Regression tests: Ensure 2.0 and 3.0 still work
# ============================================================================


def test_existing_30_spec_still_validates(valid_30_spec):
    """A known-good 3.0 spec still validates correctly."""
    spec = Specification.from_dict(valid_30_spec)
    assert isinstance(spec, OpenAPISpecification)
    assert spec.version == (3, 0, 0)
    # Verify it has the expected structure
    assert "components" in spec
    assert spec.security_schemes == {}


def test_existing_20_spec_still_validates(valid_20_spec):
    """A known-good 2.0 spec still validates correctly."""
    spec = Specification.from_dict(valid_20_spec)
    assert isinstance(spec, Swagger2Specification)
    assert spec.version == (2, 0)
    # Verify it has the expected structure
    assert spec.base_path == ""
    assert spec.produces == []
    assert spec.consumes == ["application/json"]
