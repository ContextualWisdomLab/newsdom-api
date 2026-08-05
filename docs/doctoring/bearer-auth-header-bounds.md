# Bearer authentication header bounds

## Decision

NewsDOM limits the application-visible `Authorization` value to **8,192 UTF-8 bytes**. The configured token is limited so that the complete `Bearer ` credential also fits the same bound. Values outside the bound, malformed Unicode, missing credentials, and mismatches all produce the same fixed `401 Unauthorized` response with `WWW-Authenticate: Bearer`.

The check is deliberately two-stage:

1. reject a value whose Python character count already exceeds the byte budget, avoiding an unnecessary large encoding allocation;
2. encode with strict UTF-8 and reject encoding failures or byte-length overflow before calling `hmac.compare_digest`.

Only bounded byte strings reach the constant-time comparison. Authentication failure happens before PDF validation, temporary-file creation, or MinerU execution.

## Standards rationale

HTTP does not prescribe one universal field-value limit. RFC 9110 permits implementations to choose limits and requires a server that receives fields larger than it wishes to process to return an appropriate 4xx response rather than silently ignore them. The 8 KiB value is therefore a documented NewsDOM resource budget, not a claimed protocol-wide constant.

NewsDOM uses the `Authorization: Bearer` transport shape and returns the bearer challenge on authentication failure. RFC 6750 defines this header form and the `WWW-Authenticate: Bearer` response convention. NewsDOM's current shared-token mode is not presented as a complete OAuth 2.0 resource-server implementation.

The endpoint retains `401` for oversized credentials so every authentication failure has one stable public response and does not reveal whether a configured secret or supplied credential exceeded an internal limit. Upstream HTTP servers and gateways may enforce smaller aggregate or per-field limits before a request reaches the application.

## Verification contract

The merge gate covers:

- a valid complete authorization value of exactly 8,192 UTF-8 bytes;
- an 8,193-character value rejected before parser execution;
- a configured token whose complete bearer credential exceeds the budget;
- a string below the character limit but above the UTF-8 byte limit;
- an unpaired surrogate that cannot be encoded as strict UTF-8;
- non-ASCII header octets producing the fixed 401 response rather than a 500;
- ordinary missing, invalid, and valid credentials;
- the unauthenticated `/health` contract;
- 100% production statement and branch coverage plus production docstrings.

## MSA boundary

This is a leaf-service defense-in-depth limit. A naruon gateway, ingress controller, service mesh, or API management layer may impose a lower header budget, but must not assume the NewsDOM process accepts values larger than this contract. The service remains independently deployable and does not require gateway-specific code.

## Rollback

A rollback may change `MAX_AUTHORIZATION_HEADER_BYTES` only together with boundary tests, operational documentation, and a security review. Removing both the character and encoded-byte checks is prohibited because it would restore attacker-controlled comparison and allocation work without an application budget.

## References

Fielding, R. T., Nottingham, M., & Reschke, J. (2022). *HTTP semantics* (RFC 9110). RFC Editor. https://doi.org/10.17487/RFC9110

Jones, M., & Hardt, D. (2012). *The OAuth 2.0 authorization framework: Bearer token usage* (RFC 6750). RFC Editor. https://doi.org/10.17487/RFC6750
