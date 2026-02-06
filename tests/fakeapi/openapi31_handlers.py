"""Handler functions for OpenAPI 3.1 kitchen-sink integration tests."""


def test_type_array(body):
    """Echo back the nullable field for type array testing."""
    return {"received": body.get("nullable_field")}, 200


def test_const_value(body):
    """Validate const value (validation happens before this runs)."""
    return {"status": "ok"}, 200


def test_exclusive_minimum(body):
    """Echo back count for exclusiveMinimum testing."""
    return {"count": body.get("count")}, 200


def test_ref_siblings():
    """Return data for $ref with siblings testing."""
    return {"id": "123", "name": "Test Item"}, 200


def test_allof_composition(body):
    """Echo back body for allOf testing."""
    return body, 200


def test_anyof_composition(body):
    """Echo back body for anyOf testing."""
    return body, 200


def test_oneof_composition(body):
    """Echo back body for oneOf testing."""
    return body, 200


def test_form_data_anyof(body):
    """Echo back form data for anyOf testing."""
    return body, 200


def health_check():
    """Health check endpoint via pathItems reference."""
    return {"status": "healthy"}, 200


def test_secure_endpoint():
    """Secured endpoint with mutualTLS."""
    return {"status": "authenticated"}, 200


def webhook_new_data(body):
    """Webhook handler (for documentation/spec purposes)."""
    return {"received": True}, 200
