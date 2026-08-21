# ADR-0003: Bounded PDF upload transport

**Status:** Accepted
**Date:** 2026-08-21
**Decision owner:** NewsDOM maintainers
**Scope:** Authenticated `POST /parse` upload boundary
**Figma File ID:** N/A — sidecar API contract; no visual surface.

## Context

Naruon's direct PDF DOM upload contract is bounded at 64 MiB, but the owning
NewsDOM sidecar still rejected the same customer PDF above 20 MiB. That
cross-service mismatch made the equivalent email and manual workflows behave
differently and caused a customer-visible failure after the request crossed a
service boundary.

## Decision

Set `MAX_PARSE_UPLOAD_BYTES` to 64 MiB. Keep bearer authentication before
multipart body parsing, the streaming first-byte-over-limit check, PDF
signature validation, temporary-file cleanup, and the `413 Payload Too Large`
response unchanged.

Naruon remains the consumer-side owner of its signed persistence boundary. This
ADR only changes the sidecar's transport ceiling; parser runtime, concurrency,
storage quotas, and deployment capacity remain separate controls.

## Consequences

- Customers can use the same bounded 64 MiB expectation for direct and sidecar
  PDF DOM ingestion.
- A larger valid upload can reach the parser, so deployment capacity and parser
  timeout controls remain mandatory.
- No unbounded body read is introduced; the endpoint continues to stop on the
  first byte above the limit.

## References (APA 7th)

Internet Engineering Task Force. (2022). *HTTP semantics (RFC 9110).* RFC
  Editor. https://www.rfc-editor.org/rfc/rfc9110

National Institute of Standards and Technology. (2025). *Secure software
  development framework (SSDF) version 1.2* (NIST Special Publication 800-218
  Rev. 1, Initial Public Draft). https://doi.org/10.6028/NIST.SP.800-218r1.ipd
