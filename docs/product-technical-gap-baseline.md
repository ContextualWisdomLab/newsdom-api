# Product / Technical Gap Baseline

This document records code-current buyer and operator gaps for NewsDOM API, the language-agnostic PDF-to-DOM parser API built on MinerU. It is not release evidence; protected integration and exact-head acceptance remain authoritative.

## Current decision: Swagger authorization persistence

### Problem

The current candidate enables Swagger UI `persistAuthorization` whenever `RuntimeProfile.DEVELOPMENT` is selected. Swagger UI documents `persistAuthorization` as `false` by default and states that enabling it keeps authorization data across browser close/refresh. A NewsDOM development profile is an application/runtime mode, not proof that the browser is private, loopback-only, or acceptable for persistent credential storage. Development can also run with `AuthenticationMode.REQUIRED` and a real API token.

### Constraints and ownership

- NewsDOM owns its runtime configuration, parser API authentication boundary, and generated Swagger UI configuration.
- Swagger UI owns the browser-side persistence behavior; NewsDOM must consume that behavior explicitly rather than redefining it.
- `AuthenticationMode` and authentication readiness remain independent from developer-documentation convenience.
- Production must not acquire browser credential persistence through an implicit profile default.

### Alternatives considered

1. **Profile-only enablement** — rejected. `development` does not authorize persistent browser storage.
2. **Disable persistence everywhere** — safe but unnecessarily removes the local developer convenience that motivated the change.
3. **Explicit, default-off development-only opt-in** — selected. It preserves the convenience while making credential persistence an operator decision and keeps production fail closed.

### TDD / acceptance

Test-first RED commit `89e343be5bd345d34ca77a5af0b6aa90c409ddad` requires:

- development defaults to no authorization persistence;
- development can enable persistence only through an explicit setting;
- production rejects a persistence request;
- the operator environment boundary exposes the opt-in explicitly;
- existing authentication readiness and unrelated Swagger UI parameters remain unchanged.

The expected source GREEN is a default-off immutable runtime setting (operator environment name: `NEWSDOM_SWAGGER_PERSIST_AUTHORIZATION`) consumed by `create_app()`. `true` is valid only for the development profile. Production `true` fails configuration validation rather than silently broadening the browser credential boundary.

### Risk and follow-up

Browser persistence increases the lifetime of authorization material on the client. Operator documentation must state that authorization data survives browser close/refresh and that the opt-in is unsuitable for shared or remote development browsers unless the operator has independently accepted that storage boundary. After source GREEN, regenerate exact-head tests, coverage, Security/SAST/CodeQL/container/fuzz evidence and re-read review/governance state before Ready or merge.

### Traceability

- PR: `ContextualWisdomLab/newsdom-api#795`
- TDD RED: `89e343be5bd345d34ca77a5af0b6aa90c409ddad`
- Runtime authority: `src/newsdom_api/config.py`
- Swagger composition: `src/newsdom_api/main.py`
- Regression: `tests/test_fastapi_dx.py`
- Primary vendor documentation: Swagger UI, *Configuration — Authorization / persistAuthorization*, https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/ (reviewed 2026-09-05).
