# Technology Stack

**Analysis Date:** 2026-02-05

## Languages

**Primary:**
- Python ^3.9 - Entire codebase. Classifiers declare support for 3.9, 3.10, 3.11, 3.12, 3.13, and 3.14.

## Runtime

**Environment:**
- CPython 3.9 through 3.14 (tested in CI matrix)
- No `.python-version` file; version is controlled by CI matrix and tox environments

**Package Manager:**
- Poetry (build system and dependency management)
- `pyproject.toml` declares `poetry-core>=1.2.0` as build backend
- Lockfile: **not present** (no `poetry.lock` committed)
- CI pins `"poetry<2"` during installation

## Build System

**Build Backend:** `poetry.core.masonry.api` (declared in `pyproject.toml`)

**Build/Release Process:**
- Release CI (`/.github/workflows/release.yml`) uses `poetry build` to create sdist and wheel
- Version is `3.0.dev0` in source; release CI rewrites it via `sed` from the git tag
- Published to PyPI and TestPyPI via `pypa/gh-action-pypi-publish@v1.13.0`

## Frameworks

**Core:**
- Starlette >= 0.35 - ASGI foundation; provides Router, Request, Response, Types, Headers, MutableHeaders, UploadFile, HTTPException
- Werkzeug >= 2.2.1 - WSGI request handling for Flask integration
- Flask >= 2.2 (optional, `flask` extra) - Flask application integration with `[async]` sub-extra

**Testing:**
- pytest 8.4.2 - Test runner
- pytest-asyncio ~0.18.3 - Async test support (`asyncio_mode = "auto"` in `pyproject.toml`)
- pytest-cov ~2.12.1 - Coverage reporting
- tox (with `tox-gh-actions`) - Multi-Python test matrix

**Linting/Formatting/Quality:**
- pre-commit ~2.21.0 - Git hook manager (dev dependency)
- flake8 7.1.1 - Linter (via pre-commit hook)
- flake8-rst-docstrings 0.2.3 - RST docstring linting
- black 22.3.0 - Code formatter (via pre-commit hook)
- isort 5.12.0 - Import sorting (via pre-commit hook, `profile = "black"`)
- mypy v0.981 - Static type checking (via pre-commit hook)

**Documentation:**
- Sphinx 5.3.0 - Documentation generator
- sphinx-rtd-theme 1.2.0 - Read the Docs theme
- sphinx_copybutton 0.5.2
- sphinx_design 0.4.1
- sphinxemoji 0.2.0

## Key Dependencies

**Critical (Core Runtime):**
- `jsonschema` >= 4.17.3 - **Central to the entire framework.** Used for spec validation, request body validation, response body validation, and OpenAPI schema enforcement. Uses `Draft4Validator` exclusively (not Draft 2019-09, Draft 2020-12, or any other). Key classes/APIs used:
  - `jsonschema.Draft4Validator` - Base validator class
  - `jsonschema.validators.extend` - Creates custom validator classes (e.g., `Draft4RequestValidator`, `Draft4ResponseValidator` in `connexion/json_schema.py`)
  - `jsonschema.RefResolver` - JSON reference resolution (legacy API, deprecated in jsonschema >= 4.18)
  - `jsonschema.exceptions.ValidationError` - Validation error type
  - `jsonschema.exceptions.RefResolutionError` - Reference resolution error type
  - `jsonschema.validators._utils` - Internal utilities used in test custom validators
  - `jsonschema.FORMAT_CHECKER` - Format validation support
- `starlette` >= 0.35 - ASGI application infrastructure (Scope, Receive, Send, Router, Request, Response)
- `werkzeug` >= 2.2.1 - WSGI request interface for Flask integration path

**Networking/IO:**
- `httpx` >= 0.23 - HTTP client for OAuth token info remote validation and test client
- `requests` >= 2.27 - HTTP client for resolving remote `$ref` URLs in OpenAPI specs

**Serialization/Templating:**
- `PyYAML` >= 5.1 - OpenAPI spec parsing (YAML format)
- `Jinja2` >= 3.0.0 - Spec templating (allows arguments to be substituted into spec files)
- `python-multipart` >= 0.0.15 - Multipart form data parsing

**Utilities:**
- `inflection` >= 0.3.1 - String inflection (snake_case, camelCase conversions for pythonic_params)
- `asgiref` >= 3.4 - ASGI utilities
- `typing-extensions` >= 4.6.1 - Backported typing features

**Optional (Extras):**
- `flask` extra: `a2wsgi` >= 1.7 (ASGI-to-WSGI adapter), `flask` >= 2.2 with `[async]`
- `swagger-ui` extra: `swagger-ui-bundle` >= 1.1.0
- `uvicorn` extra: `uvicorn` >= 0.17.6 with `[standard]`
- `mock` extra: `jsf` >= 0.10.0 (JSON Schema Faker for mock response generation)

## jsonschema Deep Dive

**This is the most critical dependency for the SongViber server integration.**

**Validator Used:** `Draft4Validator` exclusively. The codebase does NOT use Draft 6, Draft 7, Draft 2019-09, or Draft 2020-12 validators.

**Custom Validators Defined in `connexion/json_schema.py`:**
- `Draft4RequestValidator` - Extends Draft4Validator with nullable type and enum support
- `Draft4ResponseValidator` - Extends Draft4RequestValidator with writeOnly property validation
- `NullableTypeValidator` - Wraps the `type` validator to allow null when `x-nullable: true` or `nullable: true`
- `NullableEnumValidator` - Wraps the `enum` validator to allow null for nullable enums

**Custom Validators in `connexion/spec.py`:**
- `create_spec_validator()` - Creates a validator that validates the OpenAPI spec itself, including validating default values against their schemas

**Reference Resolution:**
- Uses the **legacy** `jsonschema.RefResolver` API (deprecated since jsonschema 4.18.0, replaced by `referencing` library)
- Custom handlers for `http://`, `https://`, `file://`, and relative file refs
- `connexion/json_schema.py:resolve_refs()` fully dereferences all `$ref` entries in-memory

**OpenAPI Schema Files (for spec validation):**
- `connexion/resources/schemas/v2.0/schema.json` - Swagger 2.0 schema
- `connexion/resources/schemas/v3.0/schema.json` - OpenAPI 3.0 schema

**mypy Overrides (in `pyproject.toml`):**
- `referencing.jsonschema.*` and `referencing._core.*` have `follow_imports = "skip"` - these are the `referencing` library modules that jsonschema >= 4.18 uses internally

## Configuration

**Formatting Config (`pyproject.toml`):**
```toml
[tool.isort]
profile = "black"
```

**Flake8 Config (`tox.ini`):**
```ini
[flake8]
exclude=connexion/__init__.py
rst-roles=class,mod,obj
max-line-length=137
extend-ignore=E203,RST303
```

**pytest Config (`pyproject.toml`):**
```toml
[tool.pytest.ini_options]
filterwarnings = [
    "ignore::DeprecationWarning:connexion.*:",
    "ignore::FutureWarning:connexion.*:",
]
asyncio_mode = "auto"
```

**Coverage Config (`pyproject.toml`):**
```toml
[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if t.TYPE_CHECKING:",
    "@t.overload",
]
```

**pre-commit Config (`.pre-commit-config.yaml`):**
- CI auto-update on `main` branch, monthly schedule
- flake8 targets `^connexion/` files only
- isort runs separately for `connexion/`, `examples/`, and `tests/` with different args
- black runs separately for `connexion/`, `examples/`, and `tests/`
- mypy targets `^connexion/` with `--ignore-missing-imports` and type stubs for `jsonschema`, `PyYAML`, `requests`

## CI/CD

**Test Pipeline (`.github/workflows/pipeline.yml`):**
- Triggers: push to `main`, pull requests
- Matrix: Python 3.9, 3.10, 3.11, 3.12, 3.13, 3.14 on `ubuntu-latest`
- Uses tox with `tox-gh-actions` for env selection
- Coverage uploaded to Coveralls (parallel mode)

**tox Environments (`tox.ini`):**
- `py39-min` - Tests with minimum dependency versions (sed rewrites `>=` and `^` to `==` in pyproject.toml)
- `{py39,py310,py311,py312,py313,py314}-pypi` - Tests with latest PyPI versions
- `pre-commit` - Runs all pre-commit hooks
- All test envs: `poetry lock && poetry install --all-extras --with tests && poetry run python -m pytest tests --cov connexion --cov-report term-missing`

**tox env-to-Python mapping for CI:**
- Python 3.9 runs `py39-min` and `py39-pypi`
- Python 3.12 runs `py312-pypi` and `pre-commit`
- All others run their `pypi` variant only

**Release Pipeline (`.github/workflows/release.yml`):**
- Triggers: tag push matching `[0-9]+.[0-9]+.[0-9]+*`, or GitHub release published
- Tags go to TestPyPI; releases go to PyPI
- Uses Python 3.12 for build

## Platform Requirements

**Development:**
- Python 3.9+ with Poetry installed
- tox for running the full test matrix
- pre-commit for running linting hooks locally

**Production/Deployment:**
- Any platform with Python 3.9+ and pip/poetry
- Optional: uvicorn for ASGI server (included via `uvicorn` extra)
- No OS-specific dependencies; pure Python

## CLI Entry Points

**Registered Script:** `connexion` CLI command mapped to `connexion.cli:main`
- Subcommands: `run` (serves an OpenAPI spec)
- Also runnable as `python -m connexion` via `connexion/__main__.py`

---

*Stack analysis: 2026-02-05*
