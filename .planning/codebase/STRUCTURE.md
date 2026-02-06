# Codebase Structure

**Analysis Date:** 2026-02-05

## Directory Layout

```
connexion/
├── connexion/                    # Main Python package
│   ├── __init__.py               # Public API exports (App, FlaskApp, AsyncApp, etc.)
│   ├── __main__.py               # CLI entry point
│   ├── apps/                     # Application classes (user-facing API)
│   │   ├── __init__.py           # Exports AbstractApp
│   │   ├── abstract.py           # AbstractApp base class
│   │   ├── asynchronous.py       # AsyncApp, AsyncApi, AsyncASGIApp
│   │   └── flask.py              # FlaskApp, FlaskApi, FlaskASGIApp, FlaskOperation
│   ├── cli.py                    # CLI implementation
│   ├── context.py                # ContextVar-based request context globals
│   ├── datastructures.py         # MediaTypeDict, NoContent sentinel
│   ├── decorators/               # Handler function decorators
│   │   ├── __init__.py           # Exports decorator classes
│   │   ├── main.py               # BaseDecorator, FlaskDecorator, StarletteDecorator, etc.
│   │   ├── parameter.py          # Parameter injection decorators
│   │   └── response.py           # Response serialization decorators
│   ├── exceptions.py             # Exception hierarchy (ProblemException, etc.)
│   ├── frameworks/               # Framework-specific adapters
│   │   ├── __init__.py
│   │   ├── abstract.py           # Framework ABC
│   │   ├── flask.py              # Flask-specific utilities and converters
│   │   └── starlette.py          # Starlette-specific utilities and converters
│   ├── handlers.py               # ResolverErrorHandler
│   ├── http_facts.py             # HTTP method list, status codes, content type constants
│   ├── json_schema.py            # JSON Schema validation (Draft4 validators, ref resolution)
│   ├── jsonifier.py              # JSON serialization helper
│   ├── lifecycle.py              # ConnexionRequest, ConnexionResponse, WSGIRequest
│   ├── middleware/               # ASGI middleware pipeline
│   │   ├── __init__.py           # Exports SpecMiddleware, ConnexionMiddleware, MiddlewarePosition
│   │   ├── abstract.py           # SpecMiddleware, RoutedMiddleware, RoutedAPI base classes
│   │   ├── context.py            # ContextMiddleware (sets contextvars)
│   │   ├── exceptions.py         # ExceptionMiddleware (Problem Details handling)
│   │   ├── lifespan.py           # LifespanMiddleware (ASGI lifespan events)
│   │   ├── main.py               # ConnexionMiddleware orchestrator, _Options, MiddlewarePosition
│   │   ├── request_validation.py # RequestValidationMiddleware
│   │   ├── response_validation.py# ResponseValidationMiddleware
│   │   ├── routing.py            # RoutingMiddleware (path+method -> operation dispatch)
│   │   ├── security.py           # SecurityMiddleware (auth enforcement)
│   │   ├── server_error.py       # ServerErrorMiddleware (outermost error catch)
│   │   └── swagger_ui.py         # SwaggerUIMiddleware (serves UI and spec endpoints)
│   ├── mock.py                   # MockResolver for testing
│   ├── operations/               # Operation abstractions per spec version
│   │   ├── __init__.py           # Exports all operation classes
│   │   ├── abstract.py           # AbstractOperation (base class)
│   │   ├── openapi.py            # OpenAPIOperation (OpenAPI 3.0.x)
│   │   └── swagger2.py           # Swagger2Operation (Swagger 2.0)
│   ├── options.py                # SwaggerUIOptions, SwaggerUIConfig
│   ├── problem.py                # problem() helper (RFC 7807 responses)
│   ├── resolver.py               # Resolver, RestyResolver, MethodResolver, etc.
│   ├── resources/                # Bundled static resources
│   │   └── schemas/              # OpenAPI meta-schemas for spec validation
│   │       ├── v2.0/
│   │       │   └── schema.json   # Swagger 2.0 JSON Schema (40KB)
│   │       └── v3.0/
│   │           └── schema.json   # OpenAPI 3.0 JSON Schema (35KB)
│   ├── security.py               # SecurityHandlerFactory, auth handler classes
│   ├── spec.py                   # Specification, Swagger2Specification, OpenAPISpecification
│   ├── testing.py                # Test helpers
│   ├── types.py                  # Type aliases (MaybeAwaitable, WSGIApp)
│   ├── uri_parsing.py            # URI parsers (OpenAPIURIParser, Swagger2URIParser)
│   └── utils.py                  # Utility functions (get_function_from_name, etc.)
├── docs/                         # Sphinx documentation
├── examples/                     # Example applications
│   ├── apikey/                   # API key auth example
│   ├── basicauth/                # Basic auth example
│   ├── enforcedefaults/          # Default value enforcement example
│   ├── frameworks/               # Framework integration example
│   ├── helloworld/               # Minimal Flask example
│   ├── helloworld_async/         # Minimal async example
│   ├── jwt/                      # JWT auth example
│   ├── methodresolver/           # MethodResolver example
│   ├── oauth2/                   # OAuth2 example
│   ├── oauth2_local_tokeninfo/   # OAuth2 with local token info
│   ├── restyresolver/            # RestyResolver example
│   ├── reverseproxy/             # Reverse proxy example
│   ├── splitspecs/               # Split spec files example
│   └── sqlalchemy/               # SQLAlchemy integration example
├── tests/                        # Test suite
│   ├── api/                      # API-level integration tests
│   ├── decorators/               # Decorator unit tests
│   ├── fakeapi/                  # Fake handler functions for testing
│   │   └── hello/                # Handler modules
│   └── fixtures/                 # Test fixture spec files
│       ├── bad_operations/
│       ├── bad_specs/
│       ├── simple/
│       ├── secure_api/
│       ├── secure_endpoint/
│       └── ...                   # Many more fixture directories
├── pyproject.toml                # Project configuration
├── setup.cfg                     # Additional setup config
└── tox.ini                       # Tox test configuration
```

## Directory Purposes

**`connexion/apps/`**
- Purpose: User-facing application classes that wrap framework apps with ConnexionMiddleware
- Contains: AbstractApp base class, FlaskApp (WSGI), AsyncApp (ASGI)
- Key files: `abstract.py` (interface definition), `flask.py` (Flask integration), `asynchronous.py` (Starlette integration)

**`connexion/middleware/`**
- Purpose: ASGI middleware components forming the request processing pipeline
- Contains: 9 middleware classes, base classes, and the orchestrator
- Key files: `main.py` (orchestrator), `abstract.py` (base classes), `routing.py` (request dispatch)

**`connexion/operations/`**
- Purpose: Spec-version-specific operation abstractions that bridge spec definitions to handler functions
- Contains: Abstract base and concrete implementations for Swagger 2 and OpenAPI 3
- Key files: `abstract.py` (base), `openapi.py` (3.0.x), `swagger2.py` (2.0)

**`connexion/validators/`**
- Purpose: Request and response body/parameter validators
- Contains: Parameter validator, JSON body validators, form data validators
- Key files: `abstract.py` (base classes), `json.py` (JSON validators), `parameter.py` (param validators)

**`connexion/decorators/`**
- Purpose: Decorates user handler functions with parameter injection and response serialization
- Contains: Flask and Starlette decorator variants
- Key files: `main.py` (decorator classes), `parameter.py` (parameter injection), `response.py` (response formatting)

**`connexion/frameworks/`**
- Purpose: Framework-specific request/response translation utilities
- Contains: Flask and Starlette adapters
- Key files: `flask.py` (Flask path/type converters, JSON provider), `starlette.py` (Starlette path converters)

**`connexion/resources/schemas/`**
- Purpose: Bundled JSON Schema files for validating OpenAPI specifications
- Contains: Meta-schemas for Swagger 2.0 and OpenAPI 3.0
- Key files: `v2.0/schema.json`, `v3.0/schema.json`

**`tests/fixtures/`**
- Purpose: OpenAPI spec files used as test fixtures
- Contains: YAML spec files organized by test scenario
- Key files: Various `openapi.yaml` and `swagger.yaml` files per directory

## Key File Locations

**Entry Points:**
- `connexion/__init__.py`: Public API; exports `App`, `FlaskApp`, `AsyncApp`, `ConnexionMiddleware`
- `connexion/__main__.py`: CLI entry point
- `connexion/cli.py`: CLI implementation with `connexion run` command

**Configuration:**
- `connexion/options.py`: `SwaggerUIOptions` and `SwaggerUIConfig` classes
- `connexion/middleware/main.py`: `_Options` dataclass for middleware configuration
- `pyproject.toml`: Project metadata, dependencies, build config
- `tox.ini`: Test environment configuration

**Core Logic:**
- `connexion/spec.py`: Spec loading, parsing, validation, version branching
- `connexion/json_schema.py`: JSON Schema ref resolution, custom validators
- `connexion/resolver.py`: operationId-to-function resolution
- `connexion/security.py`: Security handler factory and implementations
- `connexion/middleware/main.py`: Middleware stack orchestration
- `connexion/middleware/routing.py`: Request-to-operation routing
- `connexion/middleware/abstract.py`: Base classes for routed middleware pattern

**Testing:**
- `tests/`: All tests
- `tests/fakeapi/`: Mock handler functions used in tests
- `tests/fixtures/`: OpenAPI spec YAML files for test scenarios
- `connexion/testing.py`: Test helper utilities

## Naming Conventions

**Files:**
- `snake_case.py` for all Python modules
- `__init__.py` in every package with explicit exports
- Operation/middleware files named after their concern (e.g., `routing.py`, `security.py`)

**Directories:**
- `snake_case` for all directories
- Spec version directories use `vX.Y` format (e.g., `v2.0/`, `v3.0/`)

**Classes:**
- `PascalCase` for all classes
- Middleware classes end with `Middleware` (e.g., `RoutingMiddleware`)
- API classes end with `API` (e.g., `RoutingAPI`, `SecurityAPI`)
- Operation classes end with `Operation` (e.g., `SecurityOperation`, `RoutingOperation`)
- Spec classes end with `Specification` (e.g., `OpenAPISpecification`)

**Constants:**
- `UPPER_SNAKE_CASE` for module-level constants
- `VALIDATOR_MAP`, `SECURITY_HANDLERS`, `ROUTING_CONTEXT`

## Where to Add New Code

**New Spec Version (e.g., OpenAPI 3.1):**
- New specification subclass: add to `connexion/spec.py` (alongside `OpenAPISpecification`)
- New operation subclass (if needed): add to `connexion/operations/` (new file or extend `openapi.py`)
- New meta-schema: add `connexion/resources/schemas/v3.1/schema.json`
- Version branching: modify `Specification.from_dict()` in `connexion/spec.py`
- Validator updates: modify `connexion/json_schema.py` (may need 2020-12 support)

**New Middleware:**
- Implementation: add file to `connexion/middleware/` following `RoutedMiddleware` or `SpecMiddleware` pattern
- Registration: add to `ConnexionMiddleware.default_middlewares` in `connexion/middleware/main.py`
- Position enum: add to `MiddlewarePosition` in `connexion/middleware/main.py`

**New Security Handler:**
- Handler class: add to `connexion/security.py` extending `AbstractSecurityHandler`
- Registration: add to `SECURITY_HANDLERS` dict in `connexion/security.py`

**New Validator:**
- Validator class: add to `connexion/validators/` extending `AbstractRequestBodyValidator` or `AbstractResponseBodyValidator`
- Registration: add to `VALIDATOR_MAP` in `connexion/validators/__init__.py`

**New Resolver:**
- Resolver class: add to `connexion/resolver.py` extending `Resolver`

**New URI Parser:**
- Parser class: add to `connexion/uri_parsing.py` extending `AbstractURIParser`

**New Framework Adapter:**
- Framework utilities: add file to `connexion/frameworks/`
- App class: add file to `connexion/apps/`
- Decorator: add to `connexion/decorators/main.py`

**New Test Fixtures:**
- Spec files: add directory under `tests/fixtures/` with YAML spec
- Handler functions: add to `tests/fakeapi/`

## Special Directories

**`connexion/resources/`**
- Purpose: Static resources bundled with the package (meta-schemas for spec validation)
- Generated: No (manually maintained)
- Committed: Yes

**`tests/fixtures/`**
- Purpose: OpenAPI/Swagger spec files for test scenarios
- Generated: No
- Committed: Yes

**`docs/`**
- Purpose: Sphinx documentation source
- Generated: Docs are built from these sources
- Committed: Yes (source files)

**`examples/`**
- Purpose: Working example applications demonstrating various features
- Generated: No
- Committed: Yes

---

*Structure analysis: 2026-02-05*
