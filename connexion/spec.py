"""
This module defines Python interfaces for OpenAPI specifications.
"""

import abc
import copy
import json
import logging
import os
import pathlib
import pkgutil
import typing as t
from collections.abc import Mapping
from urllib.parse import urlsplit

import jinja2
import jsonschema
import yaml
from jsonschema import Draft4Validator, Draft202012Validator
from jsonschema.validators import extend as extend_validator

logger = logging.getLogger(__name__)

from .exceptions import InvalidSpecification
from .json_schema import NullableTypeValidator, URLHandler, resolve_refs
from .operations import AbstractOperation, OpenAPIOperation, Swagger2Operation
from .utils import deep_get

validate_properties = Draft4Validator.VALIDATORS["properties"]


def create_spec_validator(spec: dict) -> Draft4Validator:
    """Create a Validator to validate an OpenAPI spec against the OpenAPI schema.

    :param spec: specification to validate
    """
    # Create an instance validator, which validates defaults against the spec itself instead of
    # against the OpenAPI schema.
    InstanceValidator = extend_validator(
        Draft4Validator, {"type": NullableTypeValidator}
    )
    instance_validator = InstanceValidator(spec)

    def validate_defaults(validator, properties, instance, schema):
        """Validation function to validate the `properties` subschema, enforcing each default
        value validates against the schema in which it resides.
        """
        valid = True
        for error in validate_properties(validator, properties, instance, schema):
            valid = False
            yield error

        # Validate default only when the subschema has validated successfully
        if not valid:
            return
        if isinstance(instance, dict) and "default" in instance:
            for error in instance_validator.evolve(schema=instance).iter_errors(
                instance["default"]
            ):
                yield error

    SpecValidator = extend_validator(Draft4Validator, {"properties": validate_defaults})
    return SpecValidator


def create_spec_validator_31(spec: dict) -> Draft202012Validator:
    """Create a Validator to validate an OpenAPI 3.1 spec against the OAS 3.1 schema.

    Uses Draft 2020-12 validator base, matching OAS 3.1's JSON Schema alignment.

    :param spec: specification to validate
    """
    validate_properties_202012 = Draft202012Validator.VALIDATORS["properties"]

    def validate_defaults(validator, properties, instance, schema):
        """Validation function to validate the `properties` subschema, enforcing each default
        value validates against the schema in which it resides.
        """
        valid = True
        for error in validate_properties_202012(validator, properties, instance, schema):
            valid = False
            yield error

        # Validate default only when the subschema has validated successfully
        if not valid:
            return
        if isinstance(instance, dict) and "default" in instance:
            instance_validator = Draft202012Validator(instance)
            for error in instance_validator.evolve(schema=instance).iter_errors(
                instance["default"]
            ):
                yield error

    SpecValidator31 = extend_validator(Draft202012Validator, {"properties": validate_defaults})
    return SpecValidator31


NO_SPEC_VERSION_ERR_MSG = """Unable to get the spec version.
You are missing either '"swagger": "2.0"', '"openapi": "3.0.x"', or '"openapi": "3.1.x"'
from the top level of your spec."""


def canonical_base_path(base_path):
    """
    Make given "basePath" a canonical base URL which can be prepended to paths starting with "/".
    """
    return base_path.rstrip("/")


class Specification(Mapping):

    operation_cls: t.Type[AbstractOperation]

    def __init__(self, raw_spec, *, base_uri=""):
        self._raw_spec = copy.deepcopy(raw_spec)
        self._set_defaults(raw_spec)
        self._validate_spec(raw_spec)
        self._spec = resolve_refs(raw_spec, base_uri=base_uri)
        self._base_uri = base_uri

    @classmethod
    @abc.abstractmethod
    def _set_defaults(cls, spec):
        """set some default values in the spec"""

    @classmethod
    def _validate_spec(cls, spec):
        """validate spec against schema"""
        try:
            OpenApiValidator = create_spec_validator(spec)
            validator = OpenApiValidator(cls.openapi_schema)
            validator.validate(spec)
        except jsonschema.exceptions.ValidationError as e:
            raise InvalidSpecification.create_from(e)

    def get_path_params(self, path):
        return deep_get(self._spec, ["paths", path]).get("parameters", [])

    def get_operation(self, path, method):
        return deep_get(self._spec, ["paths", path, method])

    @property
    def raw(self):
        return self._raw_spec

    @property
    def spec(self):
        return self._spec

    @property
    def version(self):
        return self._get_spec_version(self._spec)

    @property
    def security(self):
        return self._spec.get("security")

    @property
    @abc.abstractmethod
    def security_schemes(self):
        raise NotImplementedError

    def __getitem__(self, k):
        return self._spec[k]

    def __iter__(self):
        return self._spec.__iter__()

    def __len__(self):
        return self._spec.__len__()

    @staticmethod
    def _load_spec_from_file(arguments, specification):
        """
        Loads a YAML specification file, optionally rendering it with Jinja2.

        :param arguments: passed to Jinja2 renderer
        :param specification: path to specification
        """
        arguments = arguments or {}

        with specification.open(mode="rb") as openapi_yaml:
            contents = openapi_yaml.read()
            try:
                openapi_template = contents.decode()
            except UnicodeDecodeError:
                openapi_template = contents.decode("utf-8", "replace")

            openapi_string = jinja2.Template(openapi_template).render(**arguments)
            return yaml.safe_load(openapi_string)

    @classmethod
    def from_file(cls, spec, *, arguments=None, base_uri=""):
        """
        Takes in a path to a YAML file, and returns a Specification
        """
        specification_path = pathlib.Path(spec)
        spec = cls._load_spec_from_file(arguments, specification_path)
        return cls.from_dict(spec, base_uri=base_uri)

    @classmethod
    def from_url(cls, spec, *, base_uri=""):
        """
        Takes in a path to a YAML file, and returns a Specification
        """
        spec = URLHandler()(spec)
        return cls.from_dict(spec, base_uri=base_uri)

    @staticmethod
    def _get_spec_version(spec):
        try:
            version_string = spec.get("openapi") or spec.get("swagger")
        except AttributeError:
            raise InvalidSpecification(NO_SPEC_VERSION_ERR_MSG)
        if version_string is None:
            raise InvalidSpecification(NO_SPEC_VERSION_ERR_MSG)
        try:
            version_tuple = tuple(map(int, version_string.split(".")))
        except (TypeError, ValueError):
            err = (
                "Unable to convert version string to semantic version tuple: "
                "{version_string}."
            )
            err = err.format(version_string=version_string)
            raise InvalidSpecification(err)
        return version_tuple

    @classmethod
    def from_dict(cls, spec, *, base_uri=""):
        """
        Takes in a dictionary, and returns a Specification
        """

        def enforce_string_keys(obj):
            # YAML supports integer keys, but JSON does not
            if isinstance(obj, dict):
                return {str(k): enforce_string_keys(v) for k, v in obj.items()}
            return obj

        spec = enforce_string_keys(spec)
        version = cls._get_spec_version(spec)
        if version < (3, 0, 0):
            return Swagger2Specification(spec, base_uri=base_uri)
        elif version < (3, 1, 0):
            return OpenAPISpecification(spec, base_uri=base_uri)
        elif version < (4, 0, 0):
            return OpenAPI31Specification(spec, base_uri=base_uri)
        else:
            version_str = ".".join(map(str, version))
            raise InvalidSpecification(
                f"OpenAPI {version_str} is not supported. "
                f"Supported versions: 2.0, 3.0.x, 3.1.x"
            )

    def clone(self):
        return type(self)(copy.deepcopy(self._raw_spec), base_uri=self._base_uri)

    @classmethod
    def load(cls, spec, *, arguments=None):
        if isinstance(spec, str) and (
            spec.startswith("http://") or spec.startswith("https://")
        ):
            return cls.from_url(spec)
        if not isinstance(spec, dict):
            base_uri = f"{pathlib.Path(spec).parent}{os.sep}"
            return cls.from_file(spec, arguments=arguments, base_uri=base_uri)
        return cls.from_dict(spec)

    def with_base_path(self, base_path):
        new_spec = self.clone()
        new_spec.base_path = base_path
        return new_spec

    @property
    @abc.abstractmethod
    def base_path(self):
        pass

    @base_path.setter
    @abc.abstractmethod
    def base_path(self, base_path):
        pass


class Swagger2Specification(Specification):
    """Python interface for a Swagger 2 specification."""

    yaml_name = "swagger.yaml"
    operation_cls = Swagger2Operation

    openapi_schema = json.loads(
        pkgutil.get_data("connexion", "resources/schemas/v2.0/schema.json")  # type: ignore
    )

    @classmethod
    def _set_defaults(cls, spec):
        spec.setdefault("produces", [])
        spec.setdefault("consumes", ["application/json"])
        spec.setdefault("definitions", {})
        spec.setdefault("parameters", {})
        spec.setdefault("responses", {})

    @property
    def produces(self):
        return self._spec["produces"]

    @property
    def consumes(self):
        return self._spec["consumes"]

    @property
    def definitions(self):
        return self._spec["definitions"]

    @property
    def parameter_definitions(self):
        return self._spec["parameters"]

    @property
    def response_definitions(self):
        return self._spec["responses"]

    @property
    def security_schemes(self):
        return self._spec.get("securityDefinitions", {})

    @property
    def base_path(self):
        return canonical_base_path(self._spec.get("basePath", ""))

    @base_path.setter
    def base_path(self, base_path):
        base_path = canonical_base_path(base_path)
        self._raw_spec["basePath"] = base_path
        self._spec["basePath"] = base_path


class OpenAPISpecification(Specification):
    """Python interface for an OpenAPI 3 specification."""

    yaml_name = "openapi.yaml"
    operation_cls = OpenAPIOperation

    openapi_schema = json.loads(
        pkgutil.get_data("connexion", "resources/schemas/v3.0/schema.json")  # type: ignore
    )

    @classmethod
    def _set_defaults(cls, spec):
        spec.setdefault("components", {})

    @property
    def security_schemes(self):
        return self._spec["components"].get("securitySchemes", {})

    @property
    def components(self):
        return self._spec["components"]

    @property
    def base_path(self):
        servers = self._spec.get("servers", [])
        try:
            # assume we're the first server in list
            server = copy.deepcopy(servers[0])
            server_vars = server.pop("variables", {})
            server["url"] = server["url"].format(
                **{k: v["default"] for k, v in server_vars.items()}
            )
            base_path = urlsplit(server["url"]).path
        except IndexError:
            base_path = ""
        return canonical_base_path(base_path)

    @base_path.setter
    def base_path(self, base_path):
        base_path = canonical_base_path(base_path)
        user_servers = [{"url": base_path}]
        self._raw_spec["servers"] = user_servers
        self._spec["servers"] = user_servers


class OpenAPI31Specification(Specification):
    """Python interface for an OpenAPI 3.1 specification."""

    yaml_name = "openapi31.yaml"
    operation_cls = OpenAPIOperation  # Reuse 3.0 operation class; Phase 3 may introduce OpenAPI31Operation

    openapi_schema = json.loads(
        pkgutil.get_data("connexion", "resources/schemas/v3.1/schema.json")  # type: ignore
    )

    def __init__(self, raw_spec, *, base_uri=""):
        """Initialize OpenAPI 3.1 spec with version-aware ref resolution."""
        self._raw_spec = copy.deepcopy(raw_spec)
        self._set_defaults(raw_spec)
        self._validate_spec(raw_spec)
        # Pass spec_version to resolve_refs for 3.1-aware $ref sibling preservation
        self._spec = resolve_refs(raw_spec, base_uri=base_uri, spec_version=(3, 1, 0))
        self._base_uri = base_uri

    @classmethod
    def _set_defaults(cls, spec):
        spec.setdefault("components", {})

    @classmethod
    def _validate_spec(cls, spec):
        """Validate spec against OpenAPI 3.1 meta-schema using Draft 2020-12 validator.

        Per user decision: strict 3.1 validation. Reject 3.0-only patterns like
        nullable: true with helpful error messages suggesting the 3.1 equivalent.
        """
        version = spec.get("openapi", "unknown")
        logger.info(
            "Detected OpenAPI %s spec, using OpenAPI31Specification handler", version
        )

        # First, explicitly check for nullable keyword usage (3.0-only pattern)
        def _check_nullable(obj, path=""):
            """Recursively check for nullable keyword in spec."""
            if isinstance(obj, dict):
                if "nullable" in obj:
                    location = f" at '{path}'" if path else ""
                    raise InvalidSpecification(
                        f"OpenAPI {version} spec validation failed{location}: "
                        f"'nullable' keyword is not supported in OpenAPI 3.1.\n\n"
                        f"Hint: OpenAPI 3.1 removed the 'nullable' keyword. "
                        f"Use type arrays instead:\n"
                        f"  Before:  type: string\n"
                        f"           nullable: true\n"
                        f"  After:   type: [string, 'null']"
                    )
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    _check_nullable(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = f"{path}[{i}]"
                    _check_nullable(item, new_path)

        _check_nullable(spec)

        # Then validate against meta-schema
        try:
            OpenApi31Validator = create_spec_validator_31(spec)
            validator = OpenApi31Validator(cls.openapi_schema)
            validator.validate(spec)
        except jsonschema.exceptions.ValidationError as e:
            # Build version-aware error message per user decision:
            # "Every validation error includes the detected OAS version"
            error_path = ".".join(str(item) for item in e.path) if e.path else ""
            msg = f"OpenAPI {version} spec validation failed"
            if error_path:
                msg += f" at '{error_path}'"
            msg += f": {e.message}"
            raise InvalidSpecification(msg)

    @property
    def security_schemes(self):
        return self._spec["components"].get("securitySchemes", {})

    @property
    def components(self):
        return self._spec["components"]

    @property
    def base_path(self):
        servers = self._spec.get("servers", [])
        try:
            server = copy.deepcopy(servers[0])
            server_vars = server.pop("variables", {})
            server["url"] = server["url"].format(
                **{k: v["default"] for k, v in server_vars.items()}
            )
            base_path = urlsplit(server["url"]).path
        except IndexError:
            base_path = ""
        return canonical_base_path(base_path)

    @base_path.setter
    def base_path(self, base_path):
        base_path = canonical_base_path(base_path)
        user_servers = [{"url": base_path}]
        self._raw_spec["servers"] = user_servers
        self._spec["servers"] = user_servers
