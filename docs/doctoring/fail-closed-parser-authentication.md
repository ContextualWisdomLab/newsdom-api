# Fail-closed parser authentication and readiness

## Decision

NewsDOM 0.3.0 changes the parser boundary from **default-open** to
**default-required** authentication. `NEWSDOM_AUTH_MODE` defaults to `required`,
`NEWSDOM_RUNTIME_PROFILE` defaults to `production`, and the application freezes
those values when one FastAPI application instance is created. A missing
`NEWSDOM_API_TOKEN` does not stop process liveness, but it prevents traffic
readiness and blocks `/parse` before multipart upload parsing or MinerU work.

The only unauthenticated parser bypass is the explicit pair
`NEWSDOM_AUTH_MODE=disabled` and `NEWSDOM_RUNTIME_PROFILE=development`.
Attempting to disable authentication under another profile raises a deterministic
configuration error. The bypass emits one startup warning and never logs a
secret or reversible derivative.

## Failure domains

### Caller authentication failure

A required-mode service with a configured token returns one fixed `401`
response for a missing, malformed, incorrect, non-ASCII, oversized, or duplicated
Authorization header. The response includes `WWW-Authenticate: Bearer`, while
its body contains only `{"detail":"Unauthorized"}`. Raw ASGI header bytes are
compared in constant time against the UTF-8 encoded expected bearer value.

### Service configuration failure

A required-mode service without a configured token returns the fixed
`503 Service Unavailable` response from `/parse` before the request body is read.
This is not represented as a caller error because no credential can satisfy an
invalid server configuration. `/ready` reports the same non-sensitive status.

### Liveness

`GET /health` proves only that the API process can answer HTTP. It remains
unauthenticated even when authentication or MinerU configuration is unavailable.
Liveness must not cause an orchestrator to restart a healthy process merely
because the service is intentionally refusing traffic.

### Readiness

`GET /ready` succeeds only when authentication configuration is valid and the
configured MinerU executable is available. Kubernetes removes a pod from Service
endpoints after readiness failure, so this probe prevents traffic from reaching
a process that cannot safely authorize or parse documents.

### Development bypass

The development-only bypass exists for isolated local work where no production
or shared traffic can reach the service. It is never the rollback for a missing
production token. Production rollback restores the previous application release
or secret injection; it does not set `NEWSDOM_AUTH_MODE=disabled`.

### Standalone and gateway ownership

The leaf service owns its immutable authentication mode, readiness result, and
constant-time bearer comparison. A naruon or shared API gateway may add stronger
identity, rate limiting, or tenant policy, but the standalone parser still fails
closed if the gateway is bypassed or misconfigured. Gateway health does not
replace the leaf `/ready` contract.

## Security and operational rationale

Bearer possession grants access, so RFC 6750 requires protected resources to
support the Authorization header and to return a Bearer challenge when
credentials are absent. Duplicate or malformed credential transport is rejected
rather than normalized. The fixed public responses minimize configuration and
secret disclosure.

OWASP classifies broken authentication and unrestricted resource consumption as
major API risks. NewsDOM invokes a comparatively expensive document pipeline;
a missing secret therefore creates both an identity failure and an avoidable
compute-cost/denial-of-service boundary.

Kubernetes distinguishes liveness from readiness: failed readiness removes a pod
from matching Service endpoints while allowing the process to remain alive for
recovery. NewsDOM follows that distinction and does not claim formal compliance
with OWASP, Kubernetes, or OAuth certification programs.

## Compatibility and release

The previous default-open behavior is intentionally not preserved. Because the
project remains pre-1.0, the breaking operational default is scheduled for
version **0.3.0** rather than a 1.0 major release. Operators upgrading from 0.2.x
must provision a token, set the explicit production mode/profile, and route
traffic only after `/ready` succeeds.

## Verification contract

- required mode with one exact bearer header reaches the parser;
- hostile credential variants return fixed 401 before parser work;
- a missing required token returns fixed 503 before any body read;
- disabled mode is accepted only for development and warns once;
- settings cannot switch after application creation, including under concurrent
  requests;
- `/health` and `/ready` remain semantically distinct;
- container and Kubernetes examples bind production mode to a secret reference;
- OpenAPI, logs, errors, and object representations contain no bearer secret;
- production statement and branch coverage remain 100%.

## References

Jones, M., & Hardt, D. (2012). *The OAuth 2.0 authorization framework: Bearer
token usage* (RFC 6750). RFC Editor. https://doi.org/10.17487/RFC6750

Kubernetes Authors. (2025). *Liveness, readiness, and startup probes*.
Kubernetes Documentation. https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/

OWASP Foundation. (2023). *OWASP API Security Top 10—2023*.
https://owasp.org/API-Security/editions/2023/en/0x11-t10/
