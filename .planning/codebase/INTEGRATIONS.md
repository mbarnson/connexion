# External Integrations

**Analysis Date:** 2026-02-05

## APIs & External Services

**OpenAPI Specification Registries:**
- Remote OpenAPI spec loading via HTTP/HTTPS URLs
  - Client: `requests` library (`connexion/json_schema.py` `URLHandler`)
  - No auth required (public spec URLs)
  - Used for both `$ref` resolution and loading entire specs from URLs

**OAuth Token Info Endpoints:**
- Remote OAuth token validation via configurable URL
  - Client: `httpx.AsyncClient` (`connexion/security.py` `OAuthSecurityHandler.get_token_info_remote()`)
  - Auth: Bearer token forwarded in Authorization header
  - URL configured via OpenAPI spec `x-tokenInfoUrl` extension or `TOKENINFO_URL` env var
  - 5-second timeout per request

## Data Storage

**Databases:**
- None built-in. Connexion is a framework, not an application.

**File Storage:**
- Local filesystem for OpenAPI spec files (YAML/JSON)
- File ref resolution uses local paths (`connexion/json_schema.py` `FileHandler`)

**Caching:**
- None

## Authentication & Identity

**Auth Provider:** Custom, spec-driven

Connexion supports multiple authentication schemes defined in OpenAPI specs, resolved to user-provided Python functions:

**Supported Schemes (`connexion/security.py`):**
- `basic` - HTTP Basic auth (`x-basicInfoFunc` / `BASICINFO_FUNC` env var)
- `bearer` - HTTP Bearer token (`x-bearerInfoFunc` / `BEARERINFO_FUNC` env var)
- `apiKey` - API key in header, query, or cookie (`x-apikeyInfoFunc` / `APIKEYINFO_FUNC` env var)
- `oauth2` - OAuth 2.0 (`x-tokenInfoFunc` / `TOKENINFO_FUNC` env var, or `x-tokenInfoUrl` / `TOKENINFO_URL`)
- `openIdConnect` - OpenID Connect Discovery (requires custom handler via `security_map`)

**Scope Validation:**
- `x-scopeValidateFunc` / `SCOPEVALIDATE_FUNC` env var for custom scope validation
- Default: checks required scopes are a subset of token scopes

**Security Handler Factory (`SecurityHandlerFactory`):**
- Extensible via `security_map` parameter passed to App constructor
- Handlers registered in `SECURITY_HANDLERS` dict, keyed by security type
- Supports AND composition of multiple security schemes (`verify_multiple_schemes`)
- Supports OR composition via `verify_security` (tries each until one succeeds)

## Monitoring & Observability

**Error Tracking:**
- None built-in

**Logs:**
- Standard Python `logging` module throughout
- Logger per module: `logging.getLogger(__name__)`
- No structured logging

## CI/CD & Deployment

**Hosting:**
- Published to PyPI as `connexion` package
- TestPyPI for pre-release testing

**CI Pipeline:**
- GitHub Actions (`.github/workflows/pipeline.yml`)
- Coverage: Coveralls (parallel upload per Python version, then finish step)

**Release Pipeline:**
- GitHub Actions (`.github/workflows/release.yml`)
- Triggered by git tags or GitHub release events
- Uses `pypa/gh-action-pypi-publish@v1.13.0`

## Environment Configuration

**Required env vars:** None strictly required. All env vars are optional alternatives to spec-level configuration.

**Optional env vars (used in `connexion/security.py`):**
- `TOKENINFO_FUNC` - Python dotted path to token info function
- `TOKENINFO_URL` - URL for remote OAuth token validation
- `BASICINFO_FUNC` - Python dotted path to basic auth info function
- `BEARERINFO_FUNC` - Python dotted path to bearer token info function
- `APIKEYINFO_FUNC` - Python dotted path to API key info function
- `SCOPEVALIDATE_FUNC` - Python dotted path to scope validation function

**Secrets location:**
- No secrets managed by connexion itself; credentials are handled by user-provided auth functions

## Webhooks & Callbacks

**Incoming:**
- None (connexion is a framework for building APIs, not a service)

**Outgoing:**
- OAuth token validation requests to `x-tokenInfoUrl` endpoints (when configured)

## Swagger UI Integration

**Bundle:** `swagger-ui-bundle` >= 1.1.0 (optional, via `swagger-ui` extra)
- Served by `connexion/middleware/swagger_ui.py`
- Configurable via `SwaggerUIOptions` (path, template dir)
- Middleware-based: `SwaggerUIMiddleware` in the middleware stack

## OpenAPI Spec Extensions (Vendor Extensions)

Connexion recognizes these custom extensions in OpenAPI specs:

**Security:**
- `x-basicInfoFunc` - Basic auth handler function
- `x-bearerInfoFunc` - Bearer token handler function
- `x-apikeyInfoFunc` - API key handler function
- `x-tokenInfoFunc` - OAuth token info function
- `x-tokenInfoUrl` - OAuth token info URL
- `x-scopeValidateFunc` - Scope validation function
- `x-authentication-scheme` - Override authentication scheme for apiKey type

**Validation:**
- `x-nullable` - Mark property as nullable (Swagger 2.0 compat; OpenAPI 3.0 uses `nullable`)
- `x-writeOnly` - Mark property as write-only (Swagger 2.0 compat; OpenAPI 3.0 uses `writeOnly`)

**Operation:**
- `operationId` - Standard OpenAPI, maps to Python function via resolver

---

*Integration audit: 2026-02-05*
