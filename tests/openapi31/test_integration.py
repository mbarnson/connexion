"""Comprehensive OAS 3.1 kitchen-sink integration tests with HTTP round-trips.

Covers TEST-04 (all features tested), TEST-05 (form data composition), TEST-07
(all features combined in one spec).
"""
import pytest
from connexion.exceptions import InvalidSpecification
from connexion.spec import OpenAPI31Specification, Specification


class TestKitchenSinkIntegration:
    """Integration tests for OpenAPI 3.1 kitchen-sink spec."""

    def test_spec_loads_successfully(self, kitchen_sink_app):
        """Kitchen-sink spec loads without errors."""
        # Verify the app loaded and is an OpenAPI 3.1 spec
        spec = kitchen_sink_app.middleware.apis[0].specification
        assert isinstance(spec, OpenAPI31Specification)
        assert spec.version == (3, 1, 0)

    def test_type_array_accepts_null(self, kitchen_sink_app):
        """POST with null value in type: ["string", "null"] field returns 200."""
        app_client = kitchen_sink_app.test_client()
        response = app_client.post(
            "/api/type-array",
            json={"nullable_field": None},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["received"] is None

    def test_type_array_accepts_string(self, kitchen_sink_app):
        """POST with string value in type: ["string", "null"] field returns 200."""
        app_client = kitchen_sink_app.test_client()
        response = app_client.post(
            "/api/type-array",
            json={"nullable_field": "test_value"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["received"] == "test_value"

    def test_type_array_rejects_invalid(self, kitchen_sink_app):
        """POST with integer in string|null field returns 400."""
        app_client = kitchen_sink_app.test_client()
        response = app_client.post(
            "/api/type-array",
            json={"nullable_field": 42},
        )
        assert response.status_code == 400

    def test_const_valid_value(self, kitchen_sink_app):
        """Validates that const matches expected value."""
        app_client = kitchen_sink_app.test_client()
        response = app_client.post(
            "/api/const-value",
            json={"api_version": "v1.0.0"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_const_invalid_value(self, kitchen_sink_app):
        """Validates that wrong const value returns 400."""
        app_client = kitchen_sink_app.test_client()
        response = app_client.post(
            "/api/const-value",
            json={"api_version": "v2.0.0"},
        )
        assert response.status_code == 400

    def test_exclusive_minimum_rejects_boundary(self, kitchen_sink_app):
        """POST with value == exclusiveMinimum returns 400."""
        app_client = kitchen_sink_app.test_client()
        response = app_client.post(
            "/api/exclusive-minimum",
            json={"count": 0},
        )
        assert response.status_code == 400

    def test_exclusive_minimum_accepts_above(self, kitchen_sink_app):
        """POST with value > exclusiveMinimum returns 200."""
        app_client = kitchen_sink_app.test_client()
        response = app_client.post(
            "/api/exclusive-minimum",
            json={"count": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1

    def test_webhooks_parsed(self, kitchen_sink_app):
        """Access spec.webhooks, verify webhook name and method exist."""
        spec = kitchen_sink_app.middleware.apis[0].specification
        webhooks = spec.webhooks
        assert "newDataAvailable" in webhooks
        assert "post" in webhooks["newDataAvailable"]

    def test_path_items_ref_works(self, kitchen_sink_app):
        """GET endpoint defined via pathItems $ref returns 200."""
        app_client = kitchen_sink_app.test_client()
        response = app_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_mutual_tls_recognized(self, kitchen_sink_app):
        """Verify mutualTLS is in securitySchemes."""
        spec = kitchen_sink_app.middleware.apis[0].specification
        security_schemes = spec.security_schemes
        assert "mutualTLS" in security_schemes
        assert security_schemes["mutualTLS"]["type"] == "mutualTLS"

    def test_ref_siblings_preserved(self, kitchen_sink_app):
        """Verify $ref with siblings is preserved in raw spec."""
        spec = kitchen_sink_app.middleware.apis[0].specification
        # Check the raw spec before resolution
        raw_schema = spec._raw_spec["components"]["schemas"]["ItemWithSiblings"]
        # In 3.1, $ref with siblings should be preserved
        assert "$ref" in raw_schema
        assert "description" in raw_schema
        assert "summary" in raw_schema

    def test_json_schema_dialect_present(self, kitchen_sink_app):
        """Verify json_schema_dialect property returns correct value."""
        spec = kitchen_sink_app.middleware.apis[0].specification
        dialect = spec.json_schema_dialect
        assert dialect == "https://json-schema.org/draft/2020-12/schema"

    def test_allof_composition_valid(self, kitchen_sink_app):
        """POST body matching allOf returns 200."""
        app_client = kitchen_sink_app.test_client()
        response = app_client.post(
            "/api/allof-composition",
            json={"name": "John", "age": 30},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "John"
        assert data["age"] == 30

    def test_anyof_composition_valid(self, kitchen_sink_app):
        """POST body matching anyOf returns 200."""
        app_client = kitchen_sink_app.test_client()

        # Test with email
        response = app_client.post(
            "/api/anyof-composition",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 200

        # Test with phone
        response = app_client.post(
            "/api/anyof-composition",
            json={"phone": "555-1234"},
        )
        assert response.status_code == 200

    def test_oneof_composition_valid(self, kitchen_sink_app):
        """POST body matching exactly one oneOf schema returns 200."""
        app_client = kitchen_sink_app.test_client()

        # Test individual type
        response = app_client.post(
            "/api/oneof-composition",
            json={"type": "individual", "name": "John Doe"},
        )
        assert response.status_code == 200

        # Test organization type
        response = app_client.post(
            "/api/oneof-composition",
            json={"type": "organization", "company_name": "Acme Corp"},
        )
        assert response.status_code == 200

    def test_form_data_anyof(self, kitchen_sink_app):
        """POST form data matching anyOf composition validates correctly."""
        app_client = kitchen_sink_app.test_client()

        # Test with username
        response = app_client.post(
            "/api/form-data-anyof",
            data={"username": "testuser"},
        )
        assert response.status_code == 200

        # Test with email
        response = app_client.post(
            "/api/form-data-anyof",
            data={"email": "test@example.com"},
        )
        assert response.status_code == 200


def test_nullable_rejection_in_31():
    """Building a spec with nullable: true in 3.1 raises InvalidSpecification."""
    spec_with_nullable = {
        "openapi": "3.1.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "field": {
                                                "type": "string",
                                                "nullable": True,  # 3.0-only pattern
                                            }
                                        },
                                    }
                                }
                            },
                        }
                    }
                }
            }
        },
    }

    with pytest.raises(InvalidSpecification) as exc_info:
        Specification.from_dict(spec_with_nullable)

    # Verify the error message is helpful
    error_msg = str(exc_info.value)
    assert "nullable" in error_msg.lower()
    assert "3.1" in error_msg
    assert "type" in error_msg.lower()  # Should suggest type arrays
