# NewsDOM product–technical gap baseline

Updated: 2026-09-12

## Current authority

- Protected branch: `develop@539528f9667524f6b65de0ee7b8b21fbdd97c380`
- Canonical dependency-security owner: PR #822
- Dependency candidate before this document update: `0a888dabfa36adb1973894453f61f80fa72b7656`
- Parser-auth candidate: PR #842
- Release state: not released; merge and immutable release evidence remain incomplete.

## Bounded context and ownership

NewsDOM owns document-ingestion and parsing truth, including the PDF parser version it executes on untrusted uploads, the parser authentication boundary, and the repository lock that CI installs and security scanners inspect. Dependency resolution is therefore part of the NewsDOM supply-chain boundary even when a dependency is development-only. Scanner policy remains owned by the repository and organization CI controls. Cross-cutting evidence is consolidated in this canonical baseline rather than copied into parallel feature branches.

The dependency invariant is that a future lock refresh must not select a version known vulnerable to a current finding. Scanner suppression is not an acceptable substitute for remediation. The authentication invariant is that `/parse` fails closed before multipart/body parsing and returns the existing fixed unauthorized response for invalid credentials.

## Active gap: atomic dependency-security lock

PR #822 began as the canonical pypdf advisory-floor repair. Current primary advisory data establishes these pypdf patch boundaries:

- CVE-2026-84309 / GHSA-jp53-mhqp-8xcg: affected `<6.16.0`, fixed in 6.16.0;
- CVE-2026-84310 / GHSA-23w6-3w8w-8484: affected `<6.16.1`, fixed in 6.16.1;
- CVE-2026-84311 / GHSA-763m-79hh-57f2: affected `<6.16.1`, fixed in 6.16.1.

The direct pypdf compatibility floor is therefore `pypdf>=6.16.1,<7.0`, with the current candidate lock resolving pypdf 6.18.0.

After the pypdf-only tree was non-force restacked onto protected `develop@539528f...`, the exact-head Security Scan failed in the filesystem/Trivy lane while OSV and scorecard jobs in the same workflow passed. That RED demonstrated that a pypdf-only lock could not satisfy the repository's whole-tree security gate: the same lock still contained the older HTTPX2 family. The repair must therefore be atomic at the dependency-lock boundary rather than split into mutually blocking PRs.

The upstream HTTPX2 advisories establish:

- CVE-2026-84378 / GHSA-f2fp-rgf2-35cp: SSE quadratic CPU denial of service, fixed in HTTPX2 2.10.0;
- CVE-2026-84379 / GHSA-h4x7-gw46-3wm6: multipart part-header injection, fixed in HTTPX2 2.11.0;
- CVE-2026-84380 / GHSA-pf96-p4fj-6566: conflicting request-framing headers, fixed in HTTPX2 2.11.0;
- CVE-2026-84381 / GHSA-7mj9-2mp8-4m2p: `wss://` over SOCKS could omit TLS, fixed in HTTPX2 and httpcore2 2.10.0;
- CVE-2026-84382 / GHSA-8xx6-hgc6-gc2m: streaming decompression amplification, fixed in HTTPX2 2.12.0.

The strongest current HTTPX2 floor is 2.12.0. PR #822 therefore declares `httpx2>=2.12.0` and `httpcore2>=2.12.0` in the development/TestClient dependency set and resolves both to 2.12.0. The lock and direct metadata were taken from an already resolver-generated repository generation that also preserved `pypdf>=6.16.1,<7.0`; source, form-field, auth, and generated Sentinel changes from that historical generation were not adopted.

This does not assert that every HTTPX2 advisory is reachable through NewsDOM production traffic. It removes known-vulnerable artifacts from the exact lock that tests and scanners consume, which is required by the existing whole-tree gate.

### RED and repair lineage

1. Intervening descendants repeatedly mixed route-level `Form(max_length=50)`, generic Sentinel doctrine, unrelated dependency churn, and deletion of this baseline into the pypdf owner.
2. Ordinary descendant `d9d48ec43918931e995fc1a8bacac3ddc1d568f6` re-adopted the reviewed pypdf tree without history rewrite.
3. PR #759 then normally merged into protected `develop`; #822 adopted the new protected base through non-force merge descendant `c6153f707fd770a4e0191763d7b7681d47034d28` and remained `behind=0`.
4. The exact `c6153f7...` Security Scan produced a terminal filesystem/Trivy failure while pypdf tests were GREEN. This is the realistic RED for the remaining lock vulnerability.
5. Test-only descendant `5b4f05c80fd2f936460ab3efbcd0c5367b3caff4` added a regression requiring HTTPX2/httpcore2 2.12.0.
6. Production descendant `836a7ee2921d79ee5da590e19b3019e282af6dbf` raised the direct development floors and adopted the resolver-generated 2.12.0 lock without importing unrelated historical source changes.
7. This baseline, the dependency doctoring record, and CHANGELOG are updated as ordinary descendants; predecessor GREEN or review receipts are not transferred to the new exact head.

### GREEN acceptance

1. `pyproject.toml` and `uv.lock` agree on `pypdf>=6.16.1,<7.0`; the resolved pypdf artifact is >=6.16.1 and currently 6.18.0.
2. The development/TestClient set declares `httpx2>=2.12.0` and `httpcore2>=2.12.0`, and the generated lock resolves both to >=2.12.0.
3. `tests/test_pypdf_security_floor.py` and `tests/test_httpx2_security_floor.py` reject weaker declaration/lock states.
4. `CHANGELOG.md` and `docs/doctoring/dependency-security-baseline.md` describe the same current floors and advisory boundaries.
5. Complete tests, 100% owned production statement/branch coverage and docstring gates, package/docs builds, Security Scan, SAST, repository CodeQL, central CodeQL, container, fuzz, and scorecard evidence reach terminal success on the same SHA.
6. Security Scan reports none of CVE-2026-84309/84310/84311/84378/84379/84380/84381/84382 without suppression.
7. Independent current-head review has no unresolved valid finding.
8. Merge is a normal protected-branch merge. Dependent parser/auth lanes then adopt the resulting protected base through non-force descendants and obtain fresh exact-head evidence.

## Active gap: parser Bearer timing hardening

Python documents `hmac.compare_digest()` as the preferred secret-comparison primitive and notes that differing input lengths or types can theoretically reveal length/type information through timing. PR #842 narrows the unequal-length Bearer path so it performs an expected-token-length dummy comparison before returning the same unauthorized response. This is defense-in-depth hardening; no remotely exploitable severity, token-recovery feasibility, or risk-reduction percentage is asserted without representative timing distributions and an explicit attack model.

Authentication lanes must not own dependency-lock changes. They should adopt the dependency-security foundation only after it is normally merged to protected `develop`, then rerun their complete exact-head checks and independent review.

### GREEN acceptance

- missing, malformed, duplicated, oversized, non-ASCII, wrong-length, and wrong-value credentials preserve the fixed fail-closed unauthorized contract;
- invalid authentication is rejected before multipart/body parsing;
- unequal-length and equal-length mismatch paths execute the intended comparison operands without wall-clock threshold tests pretending to prove constant time;
- exact-head pytest/100% coverage, Security Scan, SAST, CodeQL and independent review are terminal GREEN;
- no dependency lock, generic security doctrine, or parser-temporary-file behavior is owned by the auth PR.

## Active gap: multipart ingress memory boundary

A route-level `Form(max_length=50)` rejects overlong values only after the framework has parsed multipart form data. It therefore does not by itself prove a pre-handler memory bound against oversized multipart fields. The previously mixed change was removed from #822.

A valid repair must place the bound at the parser/transport ingress actually responsible for buffering, include hostile multipart cases that measure or deterministically bound bytes before route execution, preserve supported language/mode values and normal upload semantics, and demonstrate failure behavior without relying on synthetic route validation as the security oracle.

## Evidence policy and release gate

Queued, pending, cancelled, action-required, or unavailable checks are incomplete evidence, not success. Predecessor receipts, synthetic statuses, source-neutral retriggers, scanner suppression, and weakened gates are not acceptance substitutes. No release is claimed until one protected exact generation has version/CHANGELOG/tag or package, immutable release, SBOM/provenance, reproducibility and rollback evidence.

## Standards and traceability

The normative secure-development reference remains NIST SP 800-218, SSDF Version 1.1. NIST published SP 800-218 Rev. 1 / SSDF Version 1.2 as an Initial Public Draft on December 17, 2025; the NIST CSRC publication index marks Rev. 1 as Draft. This baseline therefore treats SSDF 1.2 as informative draft material rather than final normative authority.

### References

National Institute of Standards and Technology. (2022). *Secure software development framework (SSDF) version 1.1: Recommendations for mitigating the risk of software vulnerabilities* (NIST Special Publication 800-218). https://doi.org/10.6028/NIST.SP.800-218

National Institute of Standards and Technology. (2025). *Secure software development framework (SSDF) version 1.2: Recommendations for mitigating the risk of software vulnerabilities* (NIST Special Publication 800-218 Rev. 1, Initial Public Draft). https://doi.org/10.6028/NIST.SP.800-218r1.ipd

Open Source Vulnerabilities. (2026a). *GHSA-jp53-mhqp-8xcg (CVE-2026-84309)*. Retrieved September 8, 2026, from https://osv.dev/vulnerability/GHSA-jp53-mhqp-8xcg

Open Source Vulnerabilities. (2026b). *GHSA-23w6-3w8w-8484 (CVE-2026-84310)*. Retrieved September 8, 2026, from https://osv.dev/vulnerability/GHSA-23w6-3w8w-8484

Open Source Vulnerabilities. (2026c). *GHSA-763m-79hh-57f2 (CVE-2026-84311)*. Retrieved September 8, 2026, from https://osv.dev/vulnerability/GHSA-763m-79hh-57f2

Pydantic. (2026a). *Quadratic SSE line buffering can cause CPU denial of service* (GHSA-f2fp-rgf2-35cp). https://github.com/pydantic/httpx2/security/advisories/GHSA-f2fp-rgf2-35cp

Pydantic. (2026b). *Multipart part header injection via unvalidated file Content-Type and custom headers* (GHSA-h4x7-gw46-3wm6). https://github.com/pydantic/httpx2/security/advisories/GHSA-h4x7-gw46-3wm6

Pydantic. (2026c). *Conflicting Content-Length and Transfer-Encoding headers can be auto-generated* (GHSA-pf96-p4fj-6566). https://github.com/pydantic/httpx2/security/advisories/GHSA-pf96-p4fj-6566

Pydantic. (2026d). *Secure WebSocket traffic sent without TLS through SOCKS proxies* (GHSA-7mj9-2mp8-4m2p). https://github.com/pydantic/httpx2/security/advisories/GHSA-7mj9-2mp8-4m2p

Pydantic. (2026e). *Streaming response decompression does not bound peak memory* (GHSA-8xx6-hgc6-gc2m). https://github.com/pydantic/httpx2/security/advisories/GHSA-8xx6-hgc6-gc2m

Python Software Foundation. (2026). *hmac — Keyed-Hashing for Message Authentication*. Python 3.14 documentation. https://docs.python.org/3/library/hmac.html#hmac.compare_digest
