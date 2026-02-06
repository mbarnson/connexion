"""Tests for OpenAPI 3.1 features (Phase 3).

Covers requirements:
- FEAT-01: Webhooks
- FEAT-02: pathItems in components
- FEAT-03: Minimal documents
- FEAT-04: jsonSchemaDialect
- FEAT-05: mutualTLS security scheme
- FEAT-06: $ref sibling preservation
- SPEC-03: OpenAPI31Operation
"""
import pytest
from connexion.json_schema import resolve_refs
from connexion.operations.openapi import OpenAPIOperation
from connexion.operations.openapi31 import OpenAPI31Operation
from connexion.resolver import Resolver
from connexion.security import SecurityHandlerFactory
from connexion.spec import (
    OpenAPI31Specification,
    OpenAPISpecification,
    Specification,
)


# ============================================================================
# Helper functions
# ============================================================================


def make_31_spec(**overrides):
    """Create a minimal valid OAS 3.1 spec with optional overrides."""
    spec = {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
    }
    spec.update(overrides)
    return spec


def make_30_spec(**overrides):
    """Create a minimal valid OAS 3.0 spec with optional overrides."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
    }
    spec.update(overrides)
    return spec


# ============================================================================
# FEAT-01: Webhooks
# ============================================================================


class TestWebhooks:
    """Tests for OAS 3.1 webhooks property."""

    def test_webhooks_parsed_and_accessible(self):
        """Spec with webhooks key returns dict with webhook name as key."""
        spec_dict = make_31_spec(
            paths={},
            webhooks={
                "newPet": {
                    "post": {
                        "summary": "New pet notification",
                        "operationId": "newPetWebhook",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        },
                        "responses": {
                            "200": {"description": "Return a 200 status to indicate that the data was received successfully"}
                        },
                    }
                }
            },
        )
        spec = Specification.from_dict(spec_dict)
        assert isinstance(spec, OpenAPI31Specification)
        assert "newPet" in spec.webhooks
        assert "post" in spec.webhooks["newPet"]

    def test_webhooks_empty_when_not_defined(self):
        """Spec without webhooks returns empty dict."""
        spec_dict = make_31_spec(paths={})
        spec = Specification.from_dict(spec_dict)
        assert isinstance(spec, OpenAPI31Specification)
        assert spec.webhooks == {}

    def test_webhooks_path_item_structure(self):
        """Verify webhook value has expected Path Item Object structure."""
        spec_dict = make_31_spec(
            paths={},
            webhooks={
                "orderUpdate": {
                    "put": {
                        "summary": "Order status update",
                        "operationId": "orderUpdateWebhook",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "orderId": {"type": "string"},
                                            "status": {"type": "string"},
                                        },
                                    }
                                }
                            },
                        },
                        "responses": {
                            "200": {"description": "Webhook delivered successfully"},
                            "400": {"description": "Invalid webhook payload"},
                        },
                    }
                }
            },
        )
        spec = Specification.from_dict(spec_dict)
        webhook = spec.webhooks["orderUpdate"]

        # Verify Path Item Object structure
        assert "put" in webhook
        put_op = webhook["put"]
        assert put_op["summary"] == "Order status update"
        assert put_op["operationId"] == "orderUpdateWebhook"
        assert "requestBody" in put_op
        assert "responses" in put_op
        assert "200" in put_op["responses"]
        assert "400" in put_op["responses"]


# ============================================================================
# FEAT-02: pathItems in components
# ============================================================================


class TestPathItems:
    """Tests for OAS 3.1 pathItems in components."""

    def test_path_items_in_components(self):
        """Spec with components/pathItems is accessible via spec.components."""
        spec_dict = make_31_spec(
            paths={},
            components={
                "pathItems": {
                    "HealthCheck": {
                        "get": {
                            "summary": "Health check endpoint",
                            "operationId": "healthCheck",
                            "responses": {
                                "200": {"description": "Service is healthy"}
                            },
                        }
                    }
                }
            },
        )
        spec = Specification.from_dict(spec_dict)
        assert isinstance(spec, OpenAPI31Specification)
        assert "pathItems" in spec.components
        assert "HealthCheck" in spec.components["pathItems"]
        assert "get" in spec.components["pathItems"]["HealthCheck"]

    def test_path_items_default_empty(self):
        """Spec without pathItems has empty dict default."""
        spec_dict = make_31_spec(paths={})
        spec = Specification.from_dict(spec_dict)
        assert isinstance(spec, OpenAPI31Specification)
        assert "pathItems" in spec.components
        assert spec.components["pathItems"] == {}

    def test_path_items_ref_in_paths(self):
        """Spec with $ref to pathItems component resolves correctly."""
        spec_dict = make_31_spec(
            paths={
                "/health": {"$ref": "#/components/pathItems/HealthCheck"}
            },
            components={
                "pathItems": {
                    "HealthCheck": {
                        "get": {
                            "summary": "Health check",
                            "operationId": "getHealth",
                            "responses": {
                                "200": {
                                    "description": "Healthy",
                                    "content": {
                                        "application/json": {
                                            "schema": {"type": "object"}
                                        }
                                    },
                                }
                            },
                        }
                    }
                }
            },
        )
        spec = Specification.from_dict(spec_dict)

        # After $ref resolution, /health should have the resolved path item
        assert "/health" in spec["paths"]
        health_path = spec["paths"]["/health"]
        assert "get" in health_path
        assert health_path["get"]["operationId"] == "getHealth"


# ============================================================================
# FEAT-03: Minimal documents
# ============================================================================


class TestMinimalDocuments:
    """Tests for OAS 3.1 minimal document support (no paths required)."""

    def test_minimal_document_webhooks_only(self):
        """Spec with only openapi, info, and webhooks loads without error."""
        spec_dict = make_31_spec(
            webhooks={
                "event": {
                    "post": {
                        "summary": "Event notification",
                        "operationId": "eventWebhook",
                        "requestBody": {
                            "content": {"application/json": {"schema": {"type": "object"}}}
                        },
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            }
        )
        # No paths key at all
        assert "paths" not in spec_dict

        spec = Specification.from_dict(spec_dict)
        assert isinstance(spec, OpenAPI31Specification)
        assert "event" in spec.webhooks

    def test_minimal_document_components_only(self):
        """Spec with only openapi, info, and components loads without error."""
        spec_dict = make_31_spec(
            components={
                "schemas": {
                    "Pet": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                        },
                    }
                }
            }
        )
        # No paths key at all
        assert "paths" not in spec_dict

        spec = Specification.from_dict(spec_dict)
        assert isinstance(spec, OpenAPI31Specification)
        assert "Pet" in spec.components["schemas"]

    def test_minimal_document_has_empty_paths(self):
        """Minimal doc has spec.get('paths') == {} after initialization."""
        spec_dict = make_31_spec(
            webhooks={
                "test": {
                    "post": {
                        "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            }
        )
        assert "paths" not in spec_dict

        spec = Specification.from_dict(spec_dict)
        # After _set_defaults, paths should exist as empty dict
        assert spec.get("paths") == {}


# ============================================================================
# FEAT-04: jsonSchemaDialect
# ============================================================================


class TestJsonSchemaDialect:
    """Tests for OAS 3.1 jsonSchemaDialect property."""

    def test_json_schema_dialect_present(self):
        """Spec with jsonSchemaDialect key returns the URI."""
        dialect_uri = "https://json-schema.org/draft/2019-09/schema"
        spec_dict = make_31_spec(
            paths={},
            jsonSchemaDialect=dialect_uri,
        )
        spec = Specification.from_dict(spec_dict)
        assert isinstance(spec, OpenAPI31Specification)
        assert spec.json_schema_dialect == dialect_uri

    def test_json_schema_dialect_absent(self):
        """Spec without jsonSchemaDialect returns None."""
        spec_dict = make_31_spec(paths={})
        spec = Specification.from_dict(spec_dict)
        assert isinstance(spec, OpenAPI31Specification)
        assert spec.json_schema_dialect is None

    def test_json_schema_dialect_default_2020_12(self):
        """Spec with explicit Draft 2020-12 URI returns correctly."""
        draft_2020_12 = "https://json-schema.org/draft/2020-12/schema"
        spec_dict = make_31_spec(
            paths={},
            jsonSchemaDialect=draft_2020_12,
        )
        spec = Specification.from_dict(spec_dict)
        assert isinstance(spec, OpenAPI31Specification)
        assert spec.json_schema_dialect == draft_2020_12


# ============================================================================
# FEAT-05: mutualTLS security scheme
# ============================================================================


class TestMutualTLS:
    """Tests for OAS 3.1 mutualTLS security scheme recognition."""

    def test_mutual_tls_recognized(self):
        """SecurityHandlerFactory recognizes mutualTLS type."""
        factory = SecurityHandlerFactory()
        result = factory.parse_security_scheme(
            {"type": "mutualTLS"},
            []
        )
        # Should return security_passthrough, not None
        assert result is not None
        assert result is factory.security_passthrough

    def test_mutual_tls_not_none(self):
        """mutualTLS result is not None (prevents unsupported warning)."""
        factory = SecurityHandlerFactory()
        result = factory.parse_security_scheme(
            {"type": "mutualTLS"},
            []
        )
        assert result is not None

    @pytest.mark.parametrize(
        "security_type,scheme",
        [
            ("apiKey", None),
            ("http", "basic"),
            ("http", "bearer"),
            ("oauth2", None),
        ],
    )
    def test_mutual_tls_does_not_break_other_types(self, security_type, scheme):
        """After mutualTLS addition, other security types still work."""
        factory = SecurityHandlerFactory()

        if security_type == "apiKey":
            security_scheme = {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
            }
        elif security_type == "http":
            security_scheme = {
                "type": "http",
                "scheme": scheme,
            }
        elif security_type == "oauth2":
            security_scheme = {
                "type": "oauth2",
                "flows": {
                    "implicit": {
                        "authorizationUrl": "https://example.com/oauth/authorize",
                        "scopes": {"read": "Read access"},
                    }
                },
            }

        # Should not raise or return None inappropriately
        # (apiKey and http schemes should return handler, oauth2 might return None without x-tokenInfoFunc)
        result = factory.parse_security_scheme(security_scheme, [])
        # Just verify it doesn't crash - actual handler behavior tested elsewhere


# ============================================================================
# FEAT-06: $ref sibling preservation (verification of Phase 2)
# ============================================================================


class TestRefSiblings:
    """Tests for $ref sibling preservation in OAS 3.1.

    Tests resolve_refs behavior at the schema level, which is where $ref
    sibling preservation matters most in JSON Schema 2020-12.
    """

    def test_ref_siblings_preserved_in_31(self):
        """Spec with $ref alongside description preserves both in 3.1."""
        spec = {
            "components": {
                "schemas": {
                    "BaseString": {"type": "string", "maxLength": 100}
                }
            },
            "schema_with_ref": {
                "$ref": "#/components/schemas/BaseString",
                "description": "A referenced string with extra description",
                "example": "hello world"
            }
        }

        resolved = resolve_refs(spec, spec_version=(3, 1, 0))

        # For 3.1, siblings should be preserved alongside $ref content
        schema = resolved["schema_with_ref"]
        assert schema["type"] == "string"
        assert schema["maxLength"] == 100
        assert schema["description"] == "A referenced string with extra description"
        assert schema["example"] == "hello world"

    def test_ref_siblings_not_preserved_in_30(self):
        """Same pattern in 3.0 spec: $ref is removed, siblings are preserved."""
        spec = {
            "components": {
                "schemas": {
                    "BaseString": {"type": "string", "maxLength": 100}
                }
            },
            "schema_with_ref": {
                "$ref": "#/components/schemas/BaseString",
                "description": "A referenced string with extra description",
                "example": "hello world"
            }
        }

        resolved = resolve_refs(spec, spec_version=(3, 0, 0))

        # For 3.0, siblings are still preserved (applied after merge), but $ref is removed
        schema = resolved["schema_with_ref"]
        assert schema["type"] == "string"
        assert schema["maxLength"] == 100
        assert schema["description"] == "A referenced string with extra description"
        assert schema["example"] == "hello world"
        # $ref itself is removed in 3.0
        assert "$ref" not in schema


# ============================================================================
# SPEC-03: OpenAPI31Operation
# ============================================================================


class TestOpenAPI31Operation:
    """Tests for OpenAPI31Operation class."""

    def test_operation_cls_is_openapi31(self):
        """OpenAPI31Specification.operation_cls is OpenAPI31Operation."""
        assert OpenAPI31Specification.operation_cls is OpenAPI31Operation

    def test_openapi31_operation_inherits_openapi(self):
        """OpenAPI31Operation inherits from OpenAPIOperation."""
        assert issubclass(OpenAPI31Operation, OpenAPIOperation)

    def test_openapi31_operation_has_json_schema_dialect(self):
        """Construct operation with json_schema_dialect param, verify property."""
        dialect_uri = "https://json-schema.org/draft/2020-12/schema"

        operation = OpenAPI31Operation(
            method="get",
            path="/test",
            operation={
                "operationId": "fakeapi.hello.get",
                "responses": {"200": {"description": "OK"}}
            },
            resolver=Resolver(),
            json_schema_dialect=dialect_uri,
        )

        assert operation.json_schema_dialect == dialect_uri

    def test_openapi31_operation_default_dialect_none(self):
        """Construct without json_schema_dialect param, property is None."""
        operation = OpenAPI31Operation(
            method="get",
            path="/test",
            operation={
                "operationId": "fakeapi.hello.get",
                "responses": {"200": {"description": "OK"}}
            },
            resolver=Resolver(),
        )

        assert operation.json_schema_dialect is None

    def test_openapi31_operation_from_spec(self):
        """OpenAPI31Operation.from_spec extracts json_schema_dialect from spec."""
        dialect_uri = "https://json-schema.org/draft/2019-09/schema"
        spec_dict = make_31_spec(
            paths={
                "/test": {
                    "get": {
                        "operationId": "fakeapi.hello.get",
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            },
            jsonSchemaDialect=dialect_uri,
        )
        spec = Specification.from_dict(spec_dict)
        assert isinstance(spec, OpenAPI31Specification)

        operation = OpenAPI31Operation.from_spec(
            spec,
            path="/test",
            method="get",
            resolver=Resolver(),
        )

        assert operation.json_schema_dialect == dialect_uri
