# Architecture

**Analysis Date:** 2026-02-05

## Pattern Overview

**Overall:** ASGI Middleware Pipeline with Spec-Driven Dispatch

Connexion is an ASGI middleware framework that maps OpenAPI specifications (Swagger 2.0 and OpenAPI 3.0.x) to Python handler functions. It wraps a downstream ASGI application (Flask via a2wsgi adapter, or native async Starlette) with a pipeline of specialized middlewares that handle routing, security, validation, and context injection -- all driven by the parsed OpenAPI spec.

**Key Characteristics:**
- Spec-first: The OpenAPI spec is the single source of truth for routing, validation, and security
- Middleware-layered: Each cross-cutting concern (routing, security, validation) is its own ASGI middleware
- Dual-spec support: Swagger 2.0 and OpenAPI 3.0.x via parallel `Specification` and `Operation` subclasses
- Framework-agnostic core: Flask and async/Starlette are both supported via pluggable `App` and `Decorator` implementations
- JSON Schema validation uses `jsonschema` library's `Draft4Validator` throughout (for both spec validation and request/response validation)

## Layers

### 1. Application Layer (User-Facing API)

- Purpose: Provides the public API users interact with to create and configure applications
- Location: `connexion/apps/`
- Contains: `AbstractApp` base class, `FlaskApp`, `AsyncApp`
- Depends on: `ConnexionMiddleware`, framework-specific code
- Used by: User application code

`AbstractApp` (`connexion/apps/abstract.py`) is a thin interface that delegates everything to `ConnexionMiddleware`. It exposes `add_api()`, `add_middleware()`, `add_error_handler()`, `run()`, and routes ASGI `__call__` directly to the middleware.

`FlaskApp` (`connexion/apps/flask.py`) creates a `FlaskASGIApp` wrapping a Flask WSGI app via `a2wsgi.WSGIMiddleware`. The Flask app handles final request dispatch after all middleware processing is complete.

`AsyncApp` (`connexion/apps/asynchronous.py`) creates an `AsyncASGIApp` using Starlette's `Router` for native async request dispatch.

**The default `App` is `FlaskApp`** (set in `connexion/__init__.py` line 31: `App = FlaskApp`).

### 2. Middleware Orchestration Layer

- Purpose: Assembles and manages the middleware stack
- Location: `connexion/middleware/main.py`
- Contains: `ConnexionMiddleware`, `_Options`, `MiddlewarePosition`, `API` data class
- Depends on: All middleware classes, `Specification`, `Resolver`
- Used by: `AbstractApp` subclasses

`ConnexionMiddleware` is the core orchestrator. It:
1. Holds a list of middleware classes (not instances) in `self.middlewares`
2. Stores API registrations as `API` data objects in `self.apis`
3. Lazily builds the middleware stack on first `__call__` via `_build_middleware_stack()`
4. When building, wraps each middleware around the previous, innermost-first (reversed iteration)
5. After building, iterates all apps in the stack and calls `add_api()` on any `SpecMiddleware` instances

### 3. Specification Layer

- Purpose: Loads, parses, validates, and provides access to OpenAPI specifications
- Location: `connexion/spec.py`, `connexion/json_schema.py`, `connexion/resources/schemas/`
- Contains: `Specification` base class, `Swagger2Specification`, `OpenAPISpecification`
- Depends on: `jsonschema`, `jinja2`, `yaml`, `connexion.json_schema`
- Used by: Middleware layer, Operations layer

### 4. Operations Layer

- Purpose: Represents individual API operations (a single path+method pair) and resolves them to handler functions
- Location: `connexion/operations/`
- Contains: `AbstractOperation`, `OpenAPIOperation`, `Swagger2Operation`
- Depends on: `Resolver`, `Specification`, URI parsers
- Used by: Middleware layer (routing, security, validation)

### 5. Middleware Pipeline Layer

- Purpose: Individual middleware components that process requests/responses
- Location: `connexion/middleware/`
- Contains: 9 middleware classes (see Middleware Pipeline section)
- Depends on: Operations, Validators, Security, Specification
- Used by: `ConnexionMiddleware` orchestrator

### 6. Validation Layer

- Purpose: Validates request parameters, request bodies, and response bodies against spec schemas
- Location: `connexion/validators/`, `connexion/json_schema.py`
- Contains: `ParameterValidator`, `JSONRequestBodyValidator`, `FormDataValidator`, `JSONResponseBodyValidator`
- Depends on: `jsonschema` (Draft4Validator)
- Used by: `RequestValidationMiddleware`, `ResponseValidationMiddleware`

### 7. Security Layer

- Purpose: Authenticates and authorizes requests based on spec security definitions
- Location: `connexion/security.py`, `connexion/middleware/security.py`
- Contains: `SecurityHandlerFactory`, handler classes for each auth type
- Depends on: Operations, Specification
- Used by: `SecurityMiddleware`

### 8. Decorator/Framework Layer

- Purpose: Adapts between the middleware pipeline and the framework-specific request/response handling
- Location: `connexion/decorators/`, `connexion/frameworks/`
- Contains: `FlaskDecorator`, `StarletteDecorator`, framework-specific utilities
- Depends on: Context, Operations, URI parsers
- Used by: `FlaskApp`, `AsyncApp` (innermost application layer)

## Middleware Pipeline

The default middleware stack is defined in `connexion/middleware/main.py` lines 183-193:

```python
default_middlewares = [
    ServerErrorMiddleware,      # Outermost: catches unhandled exceptions
    ExceptionMiddleware,        # Converts ProblemExceptions to responses
    SwaggerUIMiddleware,        # Serves Swagger UI and spec endpoints
    RoutingMiddleware,          # Matches requests to operations, sets routing context
    SecurityMiddleware,         # Enforces security schemes from spec
    RequestValidationMiddleware,# Validates request params/body against spec
    ResponseValidationMiddleware,# Validates response body/headers against spec (if enabled)
    LifespanMiddleware,         # Handles ASGI lifespan events
    ContextMiddleware,          # Sets contextvars for request/operation access
]
```

Request flow (outside-in): `ServerError -> Exception -> SwaggerUI -> Routing -> Security -> RequestValidation -> ResponseValidation -> Lifespan -> Context -> Framework App`

**Middleware Inheritance Pattern:**

There are two fundamental middleware patterns:

1. **`SpecMiddleware`** (`connexion/middleware/abstract.py` line 19): Base for middleware that needs spec registration. Has an `add_api()` method. Used by: `RoutingMiddleware`, `SwaggerUIMiddleware`.

2. **`RoutedMiddleware`** (`connexion/middleware/abstract.py` line 218): Base for middleware that operates on individual operations, using the routing context set by `RoutingMiddleware`. Looks up operations by `operation_id` from `scope["extensions"]["connexion_routing"]`. Used by: `SecurityMiddleware`, `RequestValidationMiddleware`, `ResponseValidationMiddleware`, `ContextMiddleware`.

Each `RoutedMiddleware` has a paired `RoutedAPI` that holds a dict of operations keyed by `operation_id`. The middleware dispatches to operations by looking up the `operation_id` from the ASGI scope's routing context.

## Specification Loading and Parsing

### Loading Pipeline

1. **Entry**: `Specification.load()` (`connexion/spec.py` line 215-223) determines the input type:
   - URL string (http/https) -> `from_url()` -> `URLHandler` fetches and parses YAML
   - File path -> `from_file()` -> reads file, renders Jinja2 templates, parses YAML
   - Dict -> `from_dict()` directly

2. **Version Detection**: `_get_spec_version()` (`connexion/spec.py` line 174-191) reads `spec["openapi"]` or `spec["swagger"]` and parses it as a semantic version tuple. This is the key branching point:
   - Version `< (3, 0, 0)` -> `Swagger2Specification`
   - Version `>= (3, 0, 0)` -> `OpenAPISpecification`
   - **No handling for 3.1.x** -- currently all OpenAPI 3.x versions are treated identically via `OpenAPISpecification`

3. **Defaults**: Each subclass sets defaults in `_set_defaults()`:
   - Swagger2: sets `produces`, `consumes`, `definitions`, `parameters`, `responses`
   - OpenAPI3: sets `components` to `{}`

4. **Schema Validation**: `_validate_spec()` (`connexion/spec.py` line 92-99) validates the raw spec against a bundled JSON Schema:
   - Swagger 2.0: `connexion/resources/schemas/v2.0/schema.json` (40KB)
   - OpenAPI 3.0: `connexion/resources/schemas/v3.0/schema.json` (35KB)
   - Uses a custom `Draft4Validator` extended with `NullableTypeValidator` and default value validation
   - **For OpenAPI 3.1 support**: A new `v3.1/schema.json` would be needed, and `from_dict()` would need to branch on `>= (3, 1, 0)`

5. **$ref Resolution**: `resolve_refs()` (`connexion/json_schema.py` line 73-107) eagerly resolves all `$ref` references in the spec:
   - Internal refs (`#/...`) are resolved by deep-getting from the spec dict
   - External refs are resolved via `jsonschema.RefResolver` with custom handlers for `file://`, `http://`, `https://` protocols
   - The resolved spec is stored as `self._spec` (mutable dict, refs inlined)
   - The raw unresolved spec is preserved as `self._raw_spec`
   - **Important for 3.1**: This eager resolution approach means `$ref` siblings (new in 3.1) would be lost since `$ref` is removed after resolution

### Spec Access Pattern

`Specification` implements `collections.abc.Mapping`, so it can be used like a dict. Key properties:
- `spec.raw` -> unresolved spec dict
- `spec.spec` -> fully resolved spec dict (refs inlined)
- `spec["paths"]` -> proxies to resolved spec
- `spec.security` -> top-level security requirements
- `spec.security_schemes` -> security scheme definitions (location varies by spec version)
- `spec.base_path` -> computed from `basePath` (Swagger 2) or `servers[0].url` (OpenAPI 3)
- `spec.operation_cls` -> `Swagger2Operation` or `OpenAPIOperation` (class, not instance)

## Operation Resolution

### From Spec to Handler Function

1. **Operation Discovery**: `AbstractRoutingAPI.add_paths()` (`connexion/middleware/abstract.py` line 83-105) iterates `spec["paths"]` and for each `(path, method)` pair calls `add_operation()`.

2. **Operation Object Creation**: `add_operation()` calls `spec.operation_cls.from_spec()` which creates a `Swagger2Operation` or `OpenAPIOperation` from the spec data:
   - `OpenAPIOperation.from_spec()` (`connexion/operations/openapi.py` line 103-116): extracts `path_parameters`, `app_security`, `security_schemes`, `components`
   - `Swagger2Operation.from_spec()` (`connexion/operations/swagger2.py` line 107-122): extracts `path_parameters`, `app_produces`, `app_consumes`, `app_security`, `security_schemes`, `definitions`

3. **Handler Resolution**: Inside `AbstractOperation.__init__()` (`connexion/operations/abstract.py` line 75-76):
   ```python
   self._resolution = resolver.resolve(self)
   self._operation_id = self._resolution.operation_id
   ```
   The `Resolver.resolve()` method:
   - Gets the `operationId` from the operation (or generates one via `RestyResolver`)
   - Prepends the `x-openapi-router-controller` or `x-swagger-router-controller` if present
   - Calls `utils.get_function_from_name()` to import the Python function by dotted path
   - Returns a `Resolution(function, operation_id)` object

### Resolver Hierarchy

- `Resolver` (`connexion/resolver.py` line 30): Default -- requires explicit `operationId` in spec
- `RelativeResolver` (`connexion/resolver.py` line 77): Prepends a root path to all operation IDs
- `RestyResolver` (`connexion/resolver.py` line 112): Generates operation IDs from REST semantics (path + HTTP method)
- `MethodResolverBase` (`connexion/resolver.py` line 188): Resolves to class-based views (CamelCase + "View")
- `MethodResolver` (`connexion/resolver.py` line 286): Instantiates view classes and extracts methods
- `MethodViewResolver` (`connexion/resolver.py` line 312): Works with Flask's `MethodView.as_view()`

## Request/Response Validation

### Validator Map

The `VALIDATOR_MAP` (`connexion/validators/__init__.py` line 16-31) maps validator types to implementations:

```python
VALIDATOR_MAP = {
    "parameter": ParameterValidator,
    "body": MediaTypeDict({
        "*/*json": JSONRequestBodyValidator,
        "application/x-www-form-urlencoded": FormDataValidator,
        "multipart/form-data": MultiPartFormDataValidator,
    }),
    "response": MediaTypeDict({
        "*/*json": JSONResponseBodyValidator,
        "text/plain": TextResponseBodyValidator,
    }),
}
```

Users can override this via the `validator_map` parameter.

### Request Validation Flow

`RequestValidationOperation.__call__()` (`connexion/middleware/request_validation.py` line 97-142):

1. **Parameter Validation**: Creates a `ParameterValidator` with the operation's parameters and a URI parser. Validates query, path, header, and cookie parameters against their spec schemas using `Draft4Validator`.

2. **Content-Type Validation**: Extracts content type from headers. If the operation defines `consumes`, validates the mime type is acceptable.

3. **Body Validation**: Gets the body schema for the request's content type. Looks up the appropriate body validator from `VALIDATOR_MAP["body"]` by mime type. The validator:
   - Wraps the ASGI `receive` channel to intercept the body stream
   - Parses the body (JSON decode, form parse, etc.)
   - Validates against the schema using `Draft4RequestValidator` (extended `Draft4Validator` with nullable support)
   - Either replays original messages or (if `MUTABLE_VALIDATION`) inserts modified body

### Response Validation Flow

`ResponseValidationOperation.__call__()` (`connexion/middleware/response_validation.py` line 89-127):

1. Wraps the ASGI `send` channel with `wrapped_send`
2. On `http.response.start` message: extracts content type, validates mime type against `produces`, validates required headers
3. Looks up response body validator from `VALIDATOR_MAP["response"]`
4. The validator wraps `send` to buffer body messages, then validates the complete body

### JSON Schema Validation Details

All validation uses `Draft4Validator` from `jsonschema` library (`connexion/json_schema.py`):

- `Draft4RequestValidator`: Extended with `NullableTypeValidator` and `NullableEnumValidator` to support `x-nullable` and `nullable` properties
- `Draft4ResponseValidator`: Same as request plus `writeOnly` / `x-writeOnly` validators
- **Critical for 3.1**: OpenAPI 3.1 aligns with JSON Schema draft 2020-12, which replaces `nullable` with `type: ["string", "null"]` and uses different validation semantics. The current `Draft4Validator` base would need to be replaced or supplemented.

## Security Handling

### Security Scheme Processing

1. **Spec-Level**: `SecurityMiddleware` (`connexion/middleware/security.py` line 155-158) uses `RoutedMiddleware` pattern. For each operation, it creates a `SecurityOperation`.

2. **Operation-Level**: `SecurityOperation._get_verification_fn()` (`connexion/middleware/security.py` line 57-102):
   - If no security requirements: returns `security_passthrough` (no-op)
   - For each security requirement (OR logic):
     - For each scheme in the requirement (AND logic):
       - Calls `SecurityHandlerFactory.parse_security_scheme()` to get a verification function
     - Multiple schemes in AND are combined via `verify_multiple_schemes()`
   - All alternatives are combined via `verify_security()` (tries each, first success wins)

3. **Handler Factory**: `SecurityHandlerFactory.parse_security_scheme()` (`connexion/security.py` line 463-521) dispatches by `type`:
   - `basic` -> `BasicSecurityHandler` (reads `x-basicInfoFunc` extension)
   - `apiKey` -> `ApiKeySecurityHandler` (reads `x-apikeyInfoFunc`, supports query/header/cookie)
   - `oauth2` -> `OAuthSecurityHandler` (reads `x-tokenInfoFunc` or `x-tokenInfoUrl`)
   - `http` -> dispatches by `scheme` (e.g., `bearer` -> `BearerSecurityHandler`)
   - `openIdConnect` -> custom handler if registered, otherwise warns
   - Custom handlers can be registered via `security_map` parameter

4. **Runtime**: `SecurityOperation.__call__()` (`connexion/middleware/security.py` line 104-111):
   - Creates `ConnexionRequest` from scope
   - Calls the composed verification function
   - On success: stores `user` and `token_info` in `request.context`
   - On failure: raises `OAuthProblem` (401) or `OAuthScopeProblem` (403)

### Security Extension Keys

Security handler functions are resolved from spec extensions:
- `x-basicInfoFunc`: Function for basic auth validation
- `x-bearerInfoFunc`: Function for bearer token validation
- `x-apikeyInfoFunc`: Function for API key validation
- `x-tokenInfoFunc`: Function for OAuth token info retrieval
- `x-tokenInfoUrl`: URL for remote OAuth token info retrieval
- `x-scopeValidateFunc`: Custom scope validation function

Each also has an environment variable fallback (e.g., `BASICINFO_FUNC`, `TOKENINFO_URL`).

## Relationship: App, FlaskApp, ConnexionMiddleware

```
User Code
  |
  v
FlaskApp (or AsyncApp)
  |  extends AbstractApp
  |  creates self._middleware_app (FlaskASGIApp or AsyncASGIApp)
  |  creates self.middleware (ConnexionMiddleware wrapping _middleware_app)
  |
  |  __call__ -> self.middleware.__call__
  |
  v
ConnexionMiddleware
  |  holds list of middleware classes
  |  builds stack lazily on first __call__
  |  stack: ServerError -> Exception -> SwaggerUI -> Routing -> Security ->
  |         RequestValidation -> ResponseValidation -> Lifespan -> Context
  |
  v
FlaskASGIApp (SpecMiddleware)
  |  wraps Flask app via a2wsgi.WSGIMiddleware
  |  registers Flask blueprints from spec operations
  |
  v
Flask WSGI App
  |  dispatches to FlaskOperation -> FlaskDecorator -> user handler function
```

For `AsyncApp`:
```
AsyncASGIApp (RoutedMiddleware)
  |  uses Starlette Router
  |  dispatches to AsyncOperation -> StarletteDecorator -> user handler function
```

## Context System

Connexion uses Python `contextvars` to provide request-scoped global access (`connexion/context.py`):

- `connexion.context.context` -> `dict` from `scope["extensions"]["connexion_context"]`
- `connexion.context.operation` -> current `AbstractOperation` instance
- `connexion.context.request` -> `ConnexionRequest` proxy (lazily constructed from scope + receive)
- `connexion.context.scope` -> raw ASGI scope
- `connexion.context.receive` -> raw ASGI receive channel

These are set by `ContextMiddleware` (`connexion/middleware/context.py`), the innermost middleware in the default stack.

## Error Handling

**Strategy:** Exception-based with RFC 7807 Problem Details

**Patterns:**

1. **ProblemException hierarchy** (`connexion/exceptions.py`): All HTTP errors extend `ProblemException` which extends both `starlette.exceptions.HTTPException` and `ConnexionException`. Each has a `to_problem()` method that creates a `ConnexionResponse` with Problem Details JSON.

2. **ExceptionMiddleware** (`connexion/middleware/exceptions.py`): Extends Starlette's `ExceptionMiddleware`. Registers handlers for `ProblemException` and generic `Exception`. Translates `ConnexionRequest`/`ConnexionResponse` to/from Starlette types via `connexion_wrapper`.

3. **ServerErrorMiddleware** (`connexion/middleware/server_error.py`): Outermost catch-all. Extends Starlette's `ServerErrorMiddleware`. Catches errors that escape `ExceptionMiddleware`.

**Exception Hierarchy:**
```
ConnexionException
  ResolverError (LookupError)
  InvalidSpecification (ValidationError)
  MissingMiddleware
  ProblemException (HTTPException)
    ClientProblem (400)
      BadRequestProblem (400)
        ExtraParameterProblem (400)
        TypeValidationError (400)
      Unauthorized (401)
        OAuthProblem (401)
          OAuthResponseProblem (401)
      UnsupportedMediaTypeProblem (415)
    ServerError (500)
      InternalServerError (500)
        NonConformingResponse (500)
          NonConformingResponseBody (500)
          NonConformingResponseHeaders (500)
      ResolverProblem (501)
```

## Key Abstractions for OpenAPI 3.1 Support

### Version Branching Points

These are the places where spec version determines behavior:

1. **`Specification.from_dict()`** (`connexion/spec.py` line 194-209): Version `< (3,0,0)` vs `>= (3,0,0)`. A 3.1 subclass would need a new branch here.

2. **`NO_SPEC_VERSION_ERR_MSG`** (`connexion/spec.py` line 63-65): Hard-codes expected versions as "2.0" or "3.0.0" in error message.

3. **`OpenAPISpecification.openapi_schema`** (`connexion/spec.py` line 300-302): Loads `v3.0/schema.json` for validation. A 3.1 schema would be needed.

4. **`OpenAPISpecification.operation_cls`** (`connexion/spec.py` line 298): Points to `OpenAPIOperation`. A 3.1-specific operation class may be needed if the operation-level spec differs significantly.

5. **`Draft4Validator` usage** (`connexion/json_schema.py`): Used everywhere for both spec validation and request/response validation. OpenAPI 3.1 uses JSON Schema 2020-12, which is not compatible with Draft 4.

### Key Differences for 3.1 That Impact Architecture

- **JSON Schema alignment**: 3.1 uses JSON Schema 2020-12, not a subset. `nullable` is replaced by `type: ["string", "null"]`. `exclusiveMinimum`/`exclusiveMaximum` become numbers, not booleans. `Draft4Validator` cannot handle this.
- **`$ref` with siblings**: 3.1 allows properties alongside `$ref`. The current `resolve_refs()` function strips `$ref` after resolution, losing sibling data.
- **`type` as array**: 3.1 allows `type: ["string", "integer"]`. Current `NullableTypeValidator` only handles single-type validation.
- **`discriminator` changes**: Subtle behavior changes that may affect validation.
- **Webhooks**: New top-level `webhooks` key.
- **`pathItems` in components**: Components can contain reusable path items.
- **`const` keyword**: New validation keyword in JSON Schema 2020-12.

---

*Architecture analysis: 2026-02-05*
