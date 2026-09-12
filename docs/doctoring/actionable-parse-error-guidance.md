# Actionable `/parse` error guidance

## Status

Active pull-request evidence. This document does not describe protected-`develop` truth until the owning pull request is integrated.

## Buyer and API contract

NewsDOM's headless API is itself a customer-facing interface. For two input failures that callers can correct immediately, the public `detail` value should tell the caller both what failed and what to do next without echoing uploaded bytes, filenames, parser diagnostics, filesystem paths, credentials, or other sensitive input.

The bounded contract is:

- HTTP 415: `Only structurally valid PDF files are accepted. Upload a valid PDF and try again.`
- HTTP 413: `File exceeds the 20 MiB upload limit. Choose a smaller PDF and try again.`

The 20 MiB wording is dimensionally exact because the implementation ceiling is `20 * 1024 * 1024` bytes. It deliberately does not call that value `20 MB`, which denotes a decimal multiple rather than the implemented binary multiple.

## Standards basis

RFC 9110 defines HTTP 413 `Content Too Large` for content larger than the server is willing or able to process and HTTP 415 `Unsupported Media Type` for content whose format is not supported by the target resource. The response remains bound to those status codes; the human-facing detail adds a concrete recovery action rather than changing HTTP semantics.

OpenAPI 3.2.0 continues to require a response description for each Response Object. NewsDOM currently emits OpenAPI 3.1 through FastAPI, so this slice does not claim or force an OpenAPI-dialect upgrade. The shared constants continue to feed the generated response descriptions and runtime error detail.

NIST distinguishes decimal SI prefixes from IEC binary prefixes and identifies `MiB` as `2^20` bytes. That makes `20 MiB` the truthful unit for the existing byte ceiling.

## Security and privacy boundary

These responses are fixed product copy. They never interpolate a caller filename, claimed content type, observed file size, parser exception, local path, or dependency error. More detailed diagnostics remain server-side evidence. Authentication and readiness failures retain their existing nondisclosing contracts.

## Verification

`tests/test_api_error_guidance.py` exercises the public HTTP 415 path and the pre-read HTTP 413 size-metadata path. The oversized test uses a fake upload whose `read()` fails the test if invoked, proving that an already-known oversize request is rejected without consuming body bytes.

Existing parser tests continue to verify the same status-code boundaries and structural PDF rejection paths. Exact-current-head repository and organization CI, coverage, security, SAST, package, and review evidence remain authoritative before integration.

## Rollback

Rollback the two public constants, this doctoring record, its focused regression, and the matching changelog entry together. Do not roll back the underlying 20 MiB resource ceiling or PDF structural validation merely to restore shorter copy.

## References

Fielding, R. T., Nottingham, M., & Reschke, J. (2022). *HTTP semantics* (RFC 9110). RFC Editor. https://doi.org/10.17487/RFC9110

National Institute of Standards and Technology. (2025, August 18). *SP 330—Section 3: Decimal multiples and sub-multiples of SI units*. https://www.nist.gov/pml/special-publication-330/sp-330-section-3

OpenAPI Initiative. (2025, September 19). *OpenAPI specification (Version 3.2.0)*. https://spec.openapis.org/oas/v3.2.0.html
