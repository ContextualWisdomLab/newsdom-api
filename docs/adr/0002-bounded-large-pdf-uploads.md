# ADR-0002: Align the bounded PDF upload ceiling with Naruon

**Status:** Accepted  
**Date:** 2026-08-20  
**Decision owner:** NewsDOM maintainers
**Scope:** Authenticated `POST /parse` PDF uploads
**Figma File ID:** N/A — backend upload contract; no visual surface.

## Context

Naruon accepts signed email-import sources up to 64 MiB so that ordinary
customer mailbox exports and their attachments are not rejected at the former
20 MiB transport boundary. NewsDOM still rejected a PDF at 20 MiB before
MinerU, so a large PDF attachment could be stored by Naruon but fail during
deferred DOM recognition.

## Decision

Raise NewsDOM's bounded `/parse` upload ceiling to 64 MiB. Keep the existing
authentication-before-multipart boundary, five-byte PDF signature check,
streaming chunk accounting, temporary-file cleanup, parser timeout, and
`413 Payload Too Large` response for the first byte above the ceiling. The
ceiling is a transport/resource budget, not a guarantee that MinerU can
successfully recognize every PDF.

Tests use a 64-byte monkeypatched budget to prove both the exact boundary and
the first over-limit byte without allocating a production-sized fixture.

## Consequences

- Naruon and NewsDOM accept the same maximum source size for deferred PDF DOM
  recognition.
- A larger request can consume more temporary disk and MinerU CPU; deployment
  operators must retain the existing concurrency, timeout, and container
  resource controls.
- No raw PDF is returned in the response, and the upload is still removed after
  parsing or failure.

## Alternatives rejected

### Keep the 20 MiB ceiling

Rejected because it leaves a confirmed cross-service contract gap for customer
PDF attachments over 20 MiB.

### Remove the ceiling

Rejected because unbounded multipart input would make request memory, temporary
storage, and parser work attacker-controlled.

## References (APA 7th)

Internet Engineering Task Force. (2022). *HTTP semantics (RFC 9110).* RFC
  Editor. https://www.rfc-editor.org/rfc/rfc9110

RFC 9110 provides the HTTP semantics for reporting a request whose content
exceeds a server's permitted limit; NewsDOM preserves this as `413` while
keeping the limit explicit and bounded.

National Institute of Standards and Technology. (2025). *Secure software
  development framework (SSDF) version 1.2: Recommendations for mitigating the
  risk of software vulnerabilities* (NIST Special Publication 800-218 Rev. 1,
  Initial Public Draft). https://doi.org/10.6028/NIST.SP.800-218r1.ipd

The SSDF supports retaining auditable input bounds, regression evidence, and
operational controls when changing an untrusted-input boundary.

No source PDF is redistributed in this repository; the cited primary standards
are linked for consumers to retrieve from their authoritative publishers.
