# Swagger UI authorization persistence boundary

## Decision

NewsDOM treats Swagger UI authorization persistence as an authentication-lifetime decision, not as presentation-only developer experience configuration.

For the protected/default `production` runtime profile, `persistAuthorization` is `false`. After a browser refresh or close, a developer must enter the Bearer token again. For the explicit `development` runtime profile, `persistAuthorization` may be `true` so local development can retain authorization across refreshes without extending the production credential lifetime.

The API authentication boundary itself is unchanged: `AuthenticationMode.REQUIRED` still requires the configured Bearer token, and the existing unauthenticated bypass remains legal only when `AuthenticationMode.DISABLED` is paired with `RuntimeProfile.DEVELOPMENT`.

## Buyer and operator behavior

Protected environments fail closed. The `/docs` description tells the operator the next action directly: **Re-enter your Bearer token after refreshing this page.** Development-profile documentation states that retention is confined to the explicit development profile.

This is a vendor-owned Swagger UI surface rather than a custom NewsDOM web component. The repository has no Storybook, custom design-system, or Figma implementation for this surface; therefore this change does not introduce a parallel visual component contract. The security setting and explanatory OpenAPI copy are the authoritative product behavior.

## Verification contract

`tests/test_swagger_authorization_persistence.py` pins both branches of the policy:

- production profile → `persistAuthorization` is `false` and the next-action copy is visible in the FastAPI description;
- development profile → `persistAuthorization` is `true` and the description explicitly identifies the development-only boundary.

The repair was test-first: commit `7b7bf73deae5b56995218532038d155231007c11` introduced the failing production assertion against the prior unconditional `true` behavior; the production repair followed in commit `8cf68cec6cb6187aa41d9eb026c0e6a1266df40c`.

## Rollback and security assumptions

A rollback must not restore unconditional authorization persistence. If the development convenience is removed, the safe rollback is `persistAuthorization=false` for every profile. Any future expansion beyond the explicit development profile requires a new security review because it changes how long browser-held authorization data survives.

The upstream Swagger UI configuration reference defines `persistAuthorization` with a default of `false` and states that setting it to `true` preserves authorization data across browser close or refresh. That upstream default is the baseline for protected NewsDOM profiles.

## Traceability

- PR: `ContextualWisdomLab/newsdom-api#674`
- RED test commit: `7b7bf73deae5b56995218532038d155231007c11`
- GREEN implementation commit: `8cf68cec6cb6187aa41d9eb026c0e6a1266df40c`
- Runtime authority: `src/newsdom_api/main.py`
- Test authority: `tests/test_swagger_authorization_persistence.py`

## Reference

SmartBear Software. (n.d.). *Configuration*. Swagger Docs. Retrieved August 28, 2026, from https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
