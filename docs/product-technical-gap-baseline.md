# Product–technical gap baseline

This baseline records buyer-visible product gaps against the current protected `develop` generation. It is evidence, not a release claim. A capability remains open until its implementation, tests, review, security gates, and release evidence refer to the same exact protected generation.

## Parser authentication timing boundary

**Problem.** NewsDOM authenticates `/parse` with a repository-owned bearer token before multipart parsing. The protected implementation uses `hmac.compare_digest(credentials, expected_token)`. Python documents `compare_digest()` as avoiding content-based short-circuiting, while noting that different operand lengths can theoretically reveal type or length information. The protected path therefore preserves value-comparison resistance but does not structurally equalize operand lengths for a wrong-length credential.

**Constraint.** The service must continue to reject malformed or incorrect credentials before reading the request body, preserve the fixed `401` response, and avoid weakening the standalone parser boundary. This change does not assert that HTTP request handling is end-to-end constant-time; parsing, transport, scheduling, and middleware introduce unrelated timing variance.

**Decision.** For a syntactically valid Bearer credential whose byte length differs from the configured token, execute one `compare_digest()` call using two equal-length copies of the expected token and return the same unauthorized response. For equal-length credentials, compare the candidate and expected token normally. This keeps every syntactically valid credential comparison on equal-sized operands without changing authorization semantics.

**RED acceptance.** Instrument `hmac.compare_digest` at the application boundary and submit shorter and longer Bearer credentials. The protected base `e06b1f3fb10903569124af011da213951e6e2473` calls the comparator with unequal operand lengths, so the structural regression fails.

**GREEN acceptance.** On the candidate exact head, the same shorter and longer credentials return `401`, never reach parser work, and the comparator receives two operands whose bytes and lengths both equal the expected token for the mismatch branch. Existing exact-token and hostile-credential tests remain green. Security/review evidence must refer to the same head before merge.

**Risk and follow-up.** Equalizing comparator operands addresses only the documented length distinction at the comparison boundary. It does not prove remotely measurable token-length confidentiality and is not, by itself, evidence for a MEDIUM-severity vulnerability. A stronger severity or exploitability claim requires a threat model and repeatable timing experiment that separates network/runtime noise from the comparison signal. Token rotation, entropy, storage, rate limiting, and gateway policy remain separate controls.

## Release gap

The authentication work remains Unreleased. A release-ready protected generation must align package/OpenAPI versions, CHANGELOG, immutable image/package identity, SBOM, provenance, reproducibility evidence, and rollback instructions. Until that generation exists, deployment examples must not advertise an unreleased version as available.

## Traceability

- Protected base reviewed: `e06b1f3fb10903569124af011da213951e6e2473`
- Candidate PR: `#826`
- Production boundary: `src/newsdom_api/main.py::_parse_access_failure`
- Regression: `tests/test_auth_timing_contract.py`
- Authentication decision record: `docs/doctoring/fail-closed-parser-authentication.md`
- Python comparison contract: Python Software Foundation. (2026). *hmac — Keyed-hashing for message authentication* (Python 3.14.7 documentation). https://docs.python.org/3/library/hmac.html
