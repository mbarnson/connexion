# Phase 3: OAS 3.1 Features - Research

**Researched:** 2026-02-05
**Domain:** OpenAPI 3.1 structural features and operation handling
**Confidence:** HIGH

## Summary

OpenAPI 3.1 introduced six major structural features beyond JSON Schema alignment: webhooks for documenting outbound API-initiated requests, reusable pathItems in components, minimal documents without the paths key, jsonSchemaDialect for schema validation control, mutualTLS security scheme, and $ref sibling preservation. Phase 3 implements these features in connexion, enabling full OAS 3.1 spec compliance.

The standard approach is straightforward: extend OpenAPI31Specification with properties to expose new top-level fields (webhooks, jsonSchemaDialect), add pathItems to the components property, relax the paths requirement in validation, add mutualTLS to SecurityHandlerFactory's type dispatch, and optionally create OpenAPI31Operation to carry 3.1-specific context. The $ref siblings feature is already complete from Phase 2 (resolve_refs preserves siblings for spec_version >= (3,1,0)).

**Primary recommendation:** Full support for all six features. Webhooks and pathItems get parse + API exposure (spec.webhooks dict, components["pathItems"]). Minimal docs work via relaxed validation. jsonSchemaDialect is recognized and logged but not enforced (enforcement deferred to validation layer improvements). mutualTLS gets recognize-only support (type allowed, no handler implementation to avoid security/middleware conflict). OpenAPI31Operation is minimal: extends OpenAPIOperation to carry jsonSchemaDialect context for future use.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Feature depth — full support where feasible:**
- All 3.1 structural features should be fully supported, not just parsed-without-error
- Webhooks: parsed, validated, exposed via API (e.g., `spec.webhooks`)
- pathItems: `components/pathItems` resolvable via `$ref` in paths
- Minimal docs: specs without `paths` key load without error
- jsonSchemaDialect: recognized and respected during validation
- mutualTLS: recognized by `SecurityHandlerFactory`
- $ref siblings: `summary`/`description` alongside `$ref` preserved (not stripped)

**mutualTLS handling:**
- Claude's discretion — pick approach that avoids the known security/middleware conflict
- Known pitfall: connexion security handlers run BEFORE middleware; SongViber uses custom AuthMiddleware for mTLS
- Must not break the pattern where `security: []` at root level lets middleware handle auth

**Webhook dispatch:**
- Claude's discretion — pick what's feasible within connexion's architecture
- Connexion has no webhook receiver infrastructure today
- Parse + API exposure is minimum; full operationId dispatch is stretch goal
- Don't overengineer — if dispatch requires major new routing infrastructure, defer it

### Claude's Discretion

- OpenAPI31Operation class design (inheritance, scope, what it carries)
- mutualTLS implementation approach (recognize-only vs handler)
- Webhook dispatch depth (parse+API vs full routing)
- pathItem $ref resolution implementation strategy
- jsonSchemaDialect enforcement depth

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

## Standard Stack

OAS 3.1 structural features are defined by the OpenAPI Initiative specification and implemented across multiple ecosystems. There is no "library" stack for this phase — it's about conforming to the spec.

### Core Dependencies (Already Present)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| jsonschema | 4.x | JSON Schema validation | Draft 2020-12 support for OAS 3.1 alignment |
| connexion | 3.x (fork) | OpenAPI framework | The project being extended |

### No Additional Dependencies Required

Phase 3 requires no new external libraries. All features are implemented via:
- Extensions to existing classes (OpenAPI31Specification, OpenAPI31Operation)
- Updates to SecurityHandlerFactory dispatch logic
- Property accessors for new top-level fields

## Architecture Patterns

### Pattern 1: Specification Property Exposure

**What:** Top-level spec fields exposed as properties on OpenAPI31Specification

**When to use:** Always for new OAS 3.1 top-level fields

**Example:**
```python
# In OpenAPI31Specification class
@property
def webhooks(self):
    """Map of webhook name to Path Item Object.

    Returns empty dict if no webhooks defined.
    Webhooks describe requests initiated by the API provider to consumers.
    """
    return self._spec.get("webhooks", {})

@property
def json_schema_dialect(self):
    """URI of the default JSON Schema dialect for Schema Objects.

    If not specified, defaults to OAS 3.1 dialect.
    """
    return self._spec.get("jsonSchemaDialect")
```

**Rationale:** This pattern is established in OpenAPISpecification for `components`, `security_schemes`, `base_path`. New 3.1 fields follow the same pattern for consistency.

### Pattern 2: Components Extension for Reusable Objects

**What:** Expose `components/pathItems` via existing `components` property

**When to use:** For reusable 3.1 components that can be $ref'd

**Example:**
```python
# Access pattern (already works if _set_defaults adds it)
spec.components["pathItems"]  # Dict of reusable path items

# In _set_defaults:
@classmethod
def _set_defaults(cls, spec):
    spec.setdefault("components", {})
    spec["components"].setdefault("pathItems", {})  # OAS 3.1 addition
```

**Rationale:** pathItems is just another components key like schemas, responses, parameters. No special handling needed beyond ensuring it exists in defaults.

### Pattern 3: Type-Based Security Scheme Dispatch

**What:** Add mutualTLS to the type-based dispatch in SecurityHandlerFactory.parse_security_scheme

**When to use:** When a new security scheme type is added to the spec

**Example:**
```python
# In SecurityHandlerFactory.parse_security_scheme
def parse_security_scheme(self, security_scheme: dict, required_scopes: list):
    security_type = security_scheme["type"]

    # ... existing handlers for basic, oauth2, http, apiKey, openIdConnect ...

    elif security_type == "mutualTLS":
        # Recognize-only: return None (let middleware handle actual mTLS)
        # This prevents "unsupported security scheme" warnings for valid 3.1 specs
        logger.debug("mutualTLS scheme recognized; delegate to middleware/infrastructure")
        return SecurityHandlerFactory.security_passthrough

    # ... custom handlers fallthrough ...
```

**Rationale:** SongViber uses custom AuthMiddleware for mTLS, not connexion's security handlers. Connexion security runs BEFORE middleware, so implementing an actual handler would conflict. Recognize-only support satisfies the requirement "recognized by SecurityHandlerFactory" without breaking the middleware pattern.

### Pattern 4: Minimal Document Support

**What:** Relax validation to allow specs without `paths` key

**When to use:** OAS 3.1 allows minimal documents with only `info` + one of (paths, webhooks, components)

**Implementation:**
- The bundled `v3.1/schema.json` already allows this (paths is optional)
- No code changes needed — the meta-schema handles it
- Verify with test: a spec with webhooks but no paths should load

**Rationale:** This is a meta-schema concern, not a runtime concern. OAS 3.1 meta-schema makes `paths` optional. Connexion's validation will accept it automatically.

### Pattern 5: Operation Context Carrier

**What:** OpenAPI31Operation extends OpenAPIOperation to carry 3.1-specific context

**When to use:** When operations need access to spec-level 3.1 features (jsonSchemaDialect, origin from webhooks vs paths)

**Example:**
```python
class OpenAPI31Operation(OpenAPIOperation):
    """Operation for OpenAPI 3.1 specs, extends 3.0 operation with 3.1 context."""

    def __init__(self, *args, json_schema_dialect=None, is_webhook=False, **kwargs):
        """
        :param json_schema_dialect: Default $schema for Schema Objects in this operation
        :param is_webhook: True if this operation is from webhooks, False if from paths
        """
        super().__init__(*args, **kwargs)
        self._json_schema_dialect = json_schema_dialect
        self._is_webhook = is_webhook

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
            json_schema_dialect=spec.json_schema_dialect,  # Pass down from spec
            is_webhook=False,  # Path operations; webhooks would set True
            *args,
            **kwargs,
        )

    @property
    def json_schema_dialect(self):
        """The JSON Schema dialect URI for this operation's schemas."""
        return self._json_schema_dialect
```

**Rationale:** Minimal extension. Most behavior inherited from OpenAPIOperation. Only adds context needed for 3.1-specific validation or tooling. The `is_webhook` flag enables future webhook dispatch if needed.

### Anti-Patterns to Avoid

- **Implementing mutualTLS handler that runs before middleware:** Breaks SongViber's AuthMiddleware pattern. Use recognize-only + passthrough.
- **Building webhook routing infrastructure:** Overengineering. Webhooks are outbound from API, not inbound routes. Parse and expose via API; routing is out of scope.
- **Enforcing jsonSchemaDialect in operation validation:** jsonSchemaDialect is already respected by validators selecting Draft 2020-12. Don't duplicate enforcement.
- **Creating pathItems resolver separate from existing $ref logic:** pathItems references work via existing resolve_refs. No special resolver needed.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Webhook routing/dispatch | Custom webhook receiver middleware | Parse + expose via `spec.webhooks` | Webhooks are API-initiated outbound requests, not inbound routes. Connexion routes inbound HTTP. Building webhook *sending* infrastructure is out of scope for a routing library. |
| jsonSchemaDialect enforcement | Custom dialect validator switcher | Existing validator selection via spec_version | Phase 2 already makes validators select Draft 2020-12 for 3.1 specs. jsonSchemaDialect override is an advanced feature; document it but don't enforce at operation level. |
| pathItems $ref resolution | New pathItems-specific resolver | Existing `resolve_refs` with components/pathItems | The $ref mechanism is the same. pathItems just adds a new components location. resolve_refs already handles this. |

**Key insight:** Most 3.1 features are additive data structures, not new runtime behaviors. Parse them, expose them via API, let consumers decide how to use them. Don't build infrastructure for features the spec describes but connexion doesn't consume (like webhook dispatch).

## Common Pitfalls

### Pitfall 1: mutualTLS Handler Conflicts with Middleware

**What goes wrong:** Implementing a mutualTLS handler in SecurityHandlerFactory that actually performs TLS certificate validation causes requests to fail before custom middleware sees them.

**Why it happens:** Connexion's middleware stack order is `Security -> RequestValidation -> ... -> Context -> Framework App`. SecurityMiddleware runs BEFORE any custom middleware. If the mutualTLS handler rejects a request (because it doesn't have TLS cert info in the ASGI scope, for example), the request never reaches AuthMiddleware.

**How to avoid:** Recognize mutualTLS as a valid type (prevents "unsupported scheme" warnings) but return `security_passthrough` instead of a validator. Log that mTLS is delegated to infrastructure/middleware.

**Warning signs:**
- Test with `security: [{mutualTLS: []}]` in a 3.1 spec
- If requests fail with 401 before hitting middleware, the handler is too aggressive

### Pitfall 2: Assuming Webhooks Need Routing

**What goes wrong:** Attempting to register webhook operations as routes (like `app.add_url_rule(webhook_name, ...)`) causes confusion because webhooks aren't inbound HTTP endpoints.

**Why it happens:** Misunderstanding the webhooks feature. Webhooks in OAS 3.1 document requests that the API *makes to consumers*, not requests consumers make to the API. They're reverse operations: the API is the client, the consumer is the server.

**How to avoid:** Expose webhooks via `spec.webhooks` property (dict of name → Path Item Object). Don't add them to routing tables. Don't create Operation objects for them unless building webhook *sending* logic (out of scope).

**Warning signs:**
- Trying to access `webhook_operation.function` (webhooks don't have handlers in the API)
- Routing errors like "webhook endpoint not found" (they're not endpoints)

### Pitfall 3: $ref to components/pathItems Fails

**What goes wrong:** A spec with `paths: { "/foo": { "$ref": "#/components/pathItems/CommonPath" } }` fails with "reference not found" error.

**Why it happens:** `_set_defaults` doesn't initialize `components["pathItems"]`, so the $ref resolver doesn't find it.

**How to avoid:** In `OpenAPI31Specification._set_defaults`, add:
```python
spec.setdefault("components", {})
spec["components"].setdefault("pathItems", {})
```

**Warning signs:**
- KeyError or "could not resolve reference" for pathItems refs
- Works for schemas/parameters but not pathItems

### Pitfall 4: Minimal Documents Rejected at Load

**What goes wrong:** A valid OAS 3.1 spec with only `webhooks` (no `paths`) fails validation with "paths is required".

**Why it happens:** Using the wrong meta-schema (v3.0/schema.json instead of v3.1/schema.json), or the v3.1 schema is incorrect.

**How to avoid:** Verify the bundled `v3.1/schema.json` has `"required": ["openapi", "info"]` (NOT including "paths"). Test with a minimal spec:
```yaml
openapi: 3.1.0
info:
  title: Minimal
  version: 1.0.0
webhooks:
  onEvent:
    post:
      requestBody:
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: OK
```

**Warning signs:**
- Error message says "paths is required" for a 3.1 spec with webhooks
- Check meta-schema's required array

### Pitfall 5: jsonSchemaDialect Ignored

**What goes wrong:** A spec with `jsonSchemaDialect: "https://json-schema.org/draft/2019-09/schema"` still validates using Draft 2020-12 semantics.

**Why it happens:** Phase 3 recognizes the field but doesn't enforce it. Validators are selected by spec_version, not jsonSchemaDialect.

**How to avoid:** Document the limitation. For Phase 3, jsonSchemaDialect is recognized and accessible but not enforced. Full enforcement would require dynamically switching validator classes per-schema based on dialect, which is complex. Current implementation: all 3.1 schemas use Draft 2020-12. Acceptable for SongViber (doesn't use jsonSchemaDialect).

**Warning signs:**
- User reports "my 2019-09 schemas validate incorrectly"
- Check if `spec.json_schema_dialect` returns the custom value but validators still use 2020-12

## Code Examples

Verified patterns from specification and existing connexion code:

### Webhooks Exposure
```python
# In OpenAPI31Specification class (connexion/spec.py)
@property
def webhooks(self):
    """Map of webhook names to Path Item Objects.

    From OAS 3.1 spec: "The incoming webhooks that MAY be received as part
    of this API and that the API consumer MAY choose to implement. Closely
    related to the callbacks feature, this section describes requests
    initiated other than by an API call."

    Returns:
        dict: Webhook name → Path Item Object, or empty dict if none defined
    """
    return self._spec.get("webhooks", {})
```

### pathItems in Components
```python
# In OpenAPI31Specification._set_defaults
@classmethod
def _set_defaults(cls, spec):
    spec.setdefault("components", {})
    spec["components"].setdefault("schemas", {})
    spec["components"].setdefault("responses", {})
    spec["components"].setdefault("parameters", {})
    spec["components"].setdefault("examples", {})
    spec["components"].setdefault("requestBodies", {})
    spec["components"].setdefault("headers", {})
    spec["components"].setdefault("securitySchemes", {})
    spec["components"].setdefault("links", {})
    spec["components"].setdefault("callbacks", {})
    spec["components"].setdefault("pathItems", {})  # OAS 3.1

# Usage in spec:
# components:
#   pathItems:
#     CommonHealthCheck:
#       get:
#         operationId: healthCheck
#         responses:
#           '200':
#             description: OK
# paths:
#   /health:
#     $ref: '#/components/pathItems/CommonHealthCheck'
```

### mutualTLS Recognition
```python
# In SecurityHandlerFactory.parse_security_scheme (connexion/security.py)
def parse_security_scheme(self, security_scheme: dict, required_scopes: list):
    security_type = security_scheme["type"]

    if security_type in ("basic", "oauth2"):
        security_handler = self.security_handlers[security_type]
        return security_handler().get_fn(security_scheme, required_scopes)

    elif security_type == "http":
        scheme = security_scheme["scheme"].lower()
        if scheme in self.security_handlers:
            security_handler = self.security_handlers[scheme]
            return security_handler().get_fn(security_scheme, required_scopes)
        else:
            logger.warning("... Unsupported http authorization scheme %s", scheme)
            return None

    elif security_type == "mutualTLS":
        # OAS 3.1: Recognize mutualTLS but delegate to infrastructure
        # Don't implement handler to avoid conflict with custom middleware
        logger.debug(
            "mutualTLS security scheme recognized; "
            "certificate validation delegated to TLS layer or custom middleware"
        )
        return SecurityHandlerFactory.security_passthrough

    # ... rest of existing code ...
```

### jsonSchemaDialect Exposure
```python
# In OpenAPI31Specification class
@property
def json_schema_dialect(self):
    """Default JSON Schema dialect URI for Schema Objects.

    From OAS 3.1 spec: "The default value for the $schema keyword within
    Schema Objects contained within this OAS document."

    If not specified, the OAS 3.1 dialect is assumed.

    Returns:
        str or None: Dialect URI, or None if using OAS 3.1 default
    """
    return self._spec.get("jsonSchemaDialect")
```

### OpenAPI31Operation Minimal Extension
```python
# In connexion/operations/openapi31.py (new file)
from connexion.operations.openapi import OpenAPIOperation

class OpenAPI31Operation(OpenAPIOperation):
    """OpenAPI 3.1 operation with additional context for 3.1 features."""

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
        Extends OpenAPIOperation with OAS 3.1 specific context.

        :param json_schema_dialect: Default $schema for Schema Objects (from spec root)
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
        """JSON Schema dialect URI for this operation's schemas."""
        return self._json_schema_dialect
```

## State of the Art

| Old Approach (3.0) | Current Approach (3.1) | When Changed | Impact |
|---------------------|------------------------|--------------|--------|
| Webhooks not specified | Top-level `webhooks` field | OAS 3.1.0 (2021) | APIs can document outbound webhook requests in the spec |
| Path items not reusable | `components/pathItems` | OAS 3.1.0 | Reduces duplication for common path patterns |
| `paths` required | `paths` OR `webhooks` OR `components` | OAS 3.1.0 | Allows schema-only or webhook-only specs |
| No schema dialect control | `jsonSchemaDialect` field | OAS 3.1.0 | Can specify JSON Schema version for all schemas |
| mutualTLS not standard | `mutualTLS` security type | OAS 3.1.0 | Financial/high-security APIs can document mTLS requirement |
| $ref siblings ignored | $ref siblings preserved | JSON Schema 2020-12 | Can add description/summary to referenced objects |

**Deprecated/outdated:**
- OAS 3.0 pattern: Documenting webhooks via `x-webhooks` vendor extension — replaced by standard `webhooks` field
- OAS 3.0 pattern: Duplicating path items across multiple paths — use `components/pathItems` + $ref in 3.1
- Assuming `paths` is always present — 3.1 allows minimal documents

## Open Questions

### 1. Should OpenAPI31Operation be created at all?

**What we know:**
- OpenAPIOperation works for 3.1 operations (Phase 2 confirmed)
- Operation structure is identical between 3.0 and 3.1
- jsonSchemaDialect is spec-level, not operation-level

**What's unclear:** Whether there's value in creating OpenAPI31Operation if it only carries jsonSchemaDialect context that's not currently used by validation.

**Recommendation:** Create minimal OpenAPI31Operation for future-proofing. Carries jsonSchemaDialect and is_webhook flag. Minimal overhead (just constructor params + properties). Makes Phase 4 testing cleaner (can assert operation type matches spec version). Cost is low, value is extensibility.

### 2. How deeply should jsonSchemaDialect be enforced?

**What we know:**
- Phase 2 validators select Draft 2020-12 for spec_version >= (3,1,0)
- jsonSchemaDialect can specify a different dialect (2019-09, custom, etc.)
- Full enforcement means per-schema validator selection

**What's unclear:** Whether to implement per-schema dialect switching or just recognize + log the field.

**Recommendation:** Recognize + log for Phase 3. Document that jsonSchemaDialect is recognized but all 3.1 schemas validate as Draft 2020-12. Full enforcement is Phase 4+ enhancement. Rationale: SongViber doesn't use jsonSchemaDialect, complexity is high, benefit is low for v1.

### 3. Should webhooks be represented as Operation objects?

**What we know:**
- Webhooks use Path Item Object structure (same as paths)
- Operation class is designed for routing (resolves to handler function)
- Webhooks are outbound (API → consumer), not routed inbound

**What's unclear:** Whether parsing webhooks into Operation objects provides value.

**Recommendation:** No. Expose webhooks as raw dict via `spec.webhooks` property. Don't create Operation objects. Rationale: Operations are for routing, webhooks aren't routes. Creating unused Operation objects adds confusion. If future use case needs webhook Operation objects (e.g., code generation), add it then.

## Sources

### Primary (HIGH confidence)

- [OpenAPI 3.1.0 Specification](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md) - Official specification for webhooks, pathItems, jsonSchemaDialect, mutualTLS, minimal documents
- Connexion codebase analysis - Existing patterns for components, security schemes, operation classes

### Secondary (MEDIUM confidence)

- [What's New in OpenAPI 3.1](https://nordicapis.com/whats-new-in-openapi-3-1-0/) - Overview of new features
- [OpenAPI 3.1 - The Gnarly Bits](https://dev.to/mikeralphson/openapi-31-the-gnarly-bits-58d0) - Implementation details and edge cases
- [LornaJane: What's New in OpenAPI 3.1](https://lornajane.net/posts/2020/whats-new-in-openapi-3-1) - Feature summaries
- [Bump.sh: Two OpenAPI 3.1 changes we love](https://bump.sh/blog/changes-in-openapi-3-1/) - Webhooks and pathItems usage
- [I'd Rather Be Writing: Webhooks and jsonSchemaDialect](https://idratherbewriting.com/learnapidoc/pubapis_openapi_step9_other_elements.html) - Tutorial on new elements
- [Redocly: Security Schemes](https://redocly.com/learn/openapi/openapi-visual-reference/security-schemes) - mutualTLS documentation
- [Speakeasy: Mutual TLS in OpenAPI](https://www.speakeasy.com/openapi/security/security-schemes/security-mutualtls) - mutualTLS examples
- [Stainless: $ref Examples and Common Errors](https://www.stainless.com/sdk-api-best-practices/practical-guide-to-openapi-ref-examples-and-common-errors) - $ref sibling properties
- [OpenAPI.NET PR #1056](https://github.com/microsoft/OpenAPI.NET/pull/1056) - pathItems implementation reference
- [OAS PR #2103](https://github.com/OAI/OpenAPI-Specification/pull/2103) - Webhooks specification development

## Metadata

**Confidence breakdown:**
- Webhooks: HIGH - Official spec and multiple implementations confirm structure and semantics
- pathItems: HIGH - Official spec, existing $ref mechanism handles it
- Minimal documents: HIGH - Meta-schema change, straightforward validation
- mutualTLS: HIGH - Simple type addition, recognize-only approach is safe
- jsonSchemaDialect: MEDIUM - Recognize-only is HIGH confidence, full enforcement complexity is MEDIUM
- $ref siblings: HIGH - Already implemented in Phase 2, verified working
- OpenAPI31Operation: MEDIUM - Design decision with tradeoffs, minimal version is safe

**Research date:** 2026-02-05
**Valid until:** 60 days (stable specification, unlikely to change)
