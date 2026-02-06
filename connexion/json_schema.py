"""
Module containing all code related to json schema validation.
"""

import contextlib
import io
import os
import typing as t
import urllib.parse
import urllib.request
from collections.abc import Mapping
from copy import deepcopy

import requests
import yaml
from jsonschema import Draft4Validator, Draft202012Validator, RefResolver
from jsonschema.exceptions import RefResolutionError, ValidationError  # noqa
from jsonschema.validators import extend

from .utils import deep_get


class ExtendedSafeLoader(yaml.SafeLoader):
    """Extends the yaml SafeLoader to coerce all keys to string so the result is valid json."""

    def __init__(self, stream):
        self.original_construct_mapping = self.construct_mapping
        self.construct_mapping = self.extended_construct_mapping
        super().__init__(stream)

    def extended_construct_mapping(self, node, deep=False):
        data = self.original_construct_mapping(node, deep)
        return {str(key): data[key] for key in data}


class FileHandler:
    """Handler to resolve file refs."""

    def __call__(self, uri):
        filepath = self._uri_to_path(uri)
        with open(filepath) as fh:
            return yaml.load(fh, ExtendedSafeLoader)

    @staticmethod
    def _uri_to_path(uri):
        parsed = urllib.parse.urlparse(uri)
        host = "{0}{0}{mnt}{0}".format(os.path.sep, mnt=parsed.netloc)
        return os.path.abspath(
            os.path.join(host, urllib.request.url2pathname(parsed.path))
        )


class URLHandler:
    """Handler to resolve url refs."""

    def __call__(self, uri):
        response = requests.get(uri)
        response.raise_for_status()

        data = io.StringIO(response.text)
        with contextlib.closing(data) as fh:
            return yaml.load(fh, ExtendedSafeLoader)


handlers = {
    "http": URLHandler(),
    "https": URLHandler(),
    "file": FileHandler(),
    "": FileHandler(),
}


def resolve_refs(spec, store=None, base_uri="", spec_version=(3, 0, 0)):
    """
    Resolve JSON references like {"$ref": <some URI>} in a spec.
    Optionally takes a store, which is a mapping from reference URLs to a
    dereferenced objects. Prepopulating the store can avoid network calls.

    For OpenAPI 3.1+ (spec_version >= (3, 1, 0)), preserves sibling keywords
    alongside $ref per JSON Schema 2020-12 semantics where $ref is an applicator.
    For earlier versions, strips $ref and merges content (legacy behavior).
    """
    spec = deepcopy(spec)
    store = store or {}
    resolver = RefResolver(base_uri, spec, store, handlers=handlers)

    def _do_resolve(node):
        if isinstance(node, Mapping) and "$ref" in node:
            path = node["$ref"][2:].split("/")
            try:
                # resolve known references
                retrieved = deep_get(spec, path)

                # For 3.1+, preserve sibling keywords (they override $ref content)
                if spec_version >= (3, 1, 0):
                    # Save all non-$ref keys before update
                    siblings = {k: v for k, v in node.items() if k != "$ref"}
                    node.update(retrieved)
                    # Restore siblings (they take precedence per 2020-12 semantics)
                    node.update(siblings)
                else:
                    # Legacy behavior: merge and strip $ref
                    node.update(retrieved)

                if isinstance(retrieved, Mapping) and "$ref" in retrieved:
                    node = _do_resolve(node)
                node.pop("$ref", None)
                return node
            except KeyError:
                # resolve external references
                with resolver.resolving(node["$ref"]) as resolved:
                    return _do_resolve(resolved)
        elif isinstance(node, Mapping):
            for k, v in node.items():
                node[k] = _do_resolve(v)
        elif isinstance(node, (list, tuple)):
            for i, _ in enumerate(node):
                node[i] = _do_resolve(node[i])
        return node

    res = _do_resolve(spec)
    return res


def format_error_with_path(exception: ValidationError) -> str:
    """Format a `ValidationError` with path to error."""
    error_path = ".".join(str(item) for item in exception.path)
    error_path_msg = f" - '{error_path}'" if error_path else ""
    return error_path_msg


def allow_nullable(validation_fn: t.Callable) -> t.Callable:
    """Extend an existing validation function, so it allows nullable values to be null."""

    def nullable_validation_fn(validator, to_validate, instance, schema):
        if instance is None and (
            schema.get("x-nullable") is True or schema.get("nullable")
        ):
            return

        yield from validation_fn(validator, to_validate, instance, schema)

    return nullable_validation_fn


def validate_writeOnly(validator, wo, instance, schema):
    yield ValidationError("Property is write-only")


NullableTypeValidator = allow_nullable(Draft4Validator.VALIDATORS["type"])
NullableEnumValidator = allow_nullable(Draft4Validator.VALIDATORS["enum"])

Draft4RequestValidator = extend(
    Draft4Validator,
    {
        "type": NullableTypeValidator,
        "enum": NullableEnumValidator,
    },
)

Draft4ResponseValidator = extend(
    Draft4Validator,
    {
        "type": NullableTypeValidator,
        "enum": NullableEnumValidator,
        "writeOnly": validate_writeOnly,
        "x-writeOnly": validate_writeOnly,
    },
)

# Draft 2020-12 validators for OpenAPI 3.1 support
# Type arrays like ["string", "null"] are natively supported in 2020-12, no NullableTypeValidator needed
Draft202012RequestValidator = Draft202012Validator

Draft202012ResponseValidator = extend(
    Draft202012Validator,
    {
        "writeOnly": validate_writeOnly,
        "x-writeOnly": validate_writeOnly,
    },
)
