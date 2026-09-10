# NewsDOM product–technical gap baseline

## API documentation execution boundary

PR #835 repairs the development documentation surface without weakening the default API response policy. The protected comparison baseline is `develop@e06b1f3fb10903569124af011da213951e6e2473`.

### Problem and constraints

FastAPI's stock Swagger UI helper emits an external JavaScript resource plus inline initialization script. Its ReDoc helper emits an external JavaScript resource and inline style, and can additionally load Google Fonts. A strict `default-src 'none'` policy therefore prevents the stock documentation pages from rendering. The previous branch response widened `script-src` with `'unsafe-inline'` and applied the relaxed policy to `/openapi.json` and the OAuth redirect path as well, even though those resources do not need the same execution permissions.

The service authenticates `/parse` with HTTP Bearer rather than an OAuth browser redirect. Documentation compatibility must therefore not become a reason to expose an unnecessary OAuth redirect execution surface.

### Current repair

- Automatic FastAPI documentation routes are disabled and `/docs` and `/redoc` are registered explicitly.
- Each documentation HTML request receives a fresh cryptographic nonce. Every script tag emitted by the FastAPI helper is bound to that nonce, and `script-src` no longer contains `'unsafe-inline'`.
- `/openapi.json` retains the strict API CSP rather than inheriting the HTML documentation exception.
- `/docs/oauth2-redirect` is not registered because this service's documented authentication boundary is HTTP Bearer.
- ReDoc is generated with Google Fonts disabled, removing the fonts.googleapis.com/fonts.gstatic.com dependency.
- Existing API responses continue to receive `default-src 'none'; frame-ancestors 'none'; base-uri 'none'`.

### Executable acceptance

`tests/test_docs_csp.py` requires two `/docs` responses to use different nonces, requires every emitted script tag to carry the matching response nonce, rejects `'unsafe-inline'` from `script-src`, applies the same script rule to ReDoc, verifies that ReDoc does not depend on Google Fonts, and verifies strict CSP on `/openapi.json` and the disabled OAuth redirect path.

A PR is not release-ready until the exact head passes the repository test/security generation and an independent review confirms the rendered documentation still works in a real browser. The tests establish the server-side contract; they do not substitute for browser execution evidence.

### Remaining buyer-visible gap

Swagger UI and ReDoc still require inline style compatibility, so their HTML-specific policies retain `style-src 'unsafe-inline'`. Swagger UI and ReDoc JavaScript/CSS are also still fetched from the FastAPI helper's CDN defaults. For a higher-assurance production documentation profile, move those assets to an immutable, version-pinned local distribution or another integrity-verifiable delivery path, then remove the remaining inline-style exception if the chosen renderer permits it. Do not claim that script nonces alone complete the entire browser supply-chain boundary.

### Decision record

**Rejected:** relaxing `script-src` with `'unsafe-inline'` for all documentation-related paths. It restores rendering by granting more execution authority than the HTML pages require and leaves inline script execution broadly permitted.

**Selected:** explicit documentation routes plus request-bound nonces for executable script. This preserves the strict policy for machine-readable OpenAPI and unrelated endpoints while making the unavoidable FastAPI helper scripts explicit and testable.

**Deferred:** self-hosting/version-pinning the documentation assets and removing `style-src 'unsafe-inline'`. This needs an asset ownership/versioning decision and browser evidence; it is not necessary to repair the immediate script-execution boundary.

## Traceability

FastAPI. (2026). *Custom Docs UI Static Assets*. FastAPI documentation. https://fastapi.tiangolo.com/how-to/custom-docs-ui-assets/

FastAPI. (2026). *fastapi.openapi.docs*. FastAPI reference. https://fastapi.tiangolo.com/reference/openapi/docs/

Mozilla Developer Network. (2026). *Content-Security-Policy (CSP)*. https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP

Mozilla Developer Network. (2026). *script-src directive*. https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/script-src
