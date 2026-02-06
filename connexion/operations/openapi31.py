"""
This module defines an OpenAPI31Operation class, extending the OpenAPI 3.0 operation
with OAS 3.1-specific context (jsonSchemaDialect).
"""

import logging

from connexion.operations.openapi import OpenAPIOperation

logger = logging.getLogger("connexion.operations.openapi31")


class OpenAPI31Operation(OpenAPIOperation):
    """OpenAPI 3.1 operation with additional context for 3.1-specific features.

    Extends OpenAPIOperation to carry:
    - json_schema_dialect: the spec-level jsonSchemaDialect URI for schema validation
    """

    def __init__(
        self,
        method,
        path,
        operation,
        resolver,
        path_parameters=None,
        app_security=None,
        security_schemes=None,
        components=None,
        randomize_endpoint=None,
        uri_parser_class=None,
        spec_version=(3, 1, 0),
        json_schema_dialect=None,
    ):
        """
        :param json_schema_dialect: Default $schema URI for Schema Objects (from spec root).
            If None, the OAS 3.1 dialect (Draft 2020-12) is assumed.
        :type json_schema_dialect: str or None
        """
        super().__init__(
            method=method,
            path=path,
            operation=operation,
            resolver=resolver,
            path_parameters=path_parameters,
            app_security=app_security,
            security_schemes=security_schemes,
            components=components,
            randomize_endpoint=randomize_endpoint,
            uri_parser_class=uri_parser_class,
            spec_version=spec_version,
        )
        self._json_schema_dialect = json_schema_dialect

    @classmethod
    def from_spec(cls, spec, *args, path, method, resolver, **kwargs):
        return cls(
            method,
            path,
            spec.get_operation(path, method),
            resolver=resolver,
            path_parameters=spec.get_path_params(path),
            app_security=spec.security,
            security_schemes=spec.security_schemes,
            components=spec.components,
            spec_version=spec.version,
            json_schema_dialect=getattr(spec, 'json_schema_dialect', None),
            *args,
            **kwargs,
        )

    @property
    def json_schema_dialect(self):
        """JSON Schema dialect URI for this operation's schemas.

        Returns the spec-level jsonSchemaDialect value. None means the default
        OAS 3.1 dialect (Draft 2020-12).
        """
        return self._json_schema_dialect
