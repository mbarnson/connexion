"""Fixtures for OpenAPI 3.1 integration tests."""
import pytest
from conftest import build_app_from_fixture


@pytest.fixture(scope="session")
def kitchen_sink_app(app_class):
    """Load the OAS 3.1 kitchen-sink spec through connexion."""
    return build_app_from_fixture(
        "openapi31_kitchen_sink",
        app_class=app_class,
        spec_file="openapi.yaml",
        validate_responses=True,
    )
