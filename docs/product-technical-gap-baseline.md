# NewsDOM product–technical gap baseline

Updated: 2026-09-11

## Current authority

- Protected branch: `develop@e06b1f3fb10903569124af011da213951e6e2473`
- Canonical dependency-security/baseline owner: PR #822
- pypdf candidate: `8595855f358009583d396a8908e290c9e863feb7` before this document update
- parser-auth candidate: PR #842 at `d8c1b7357f251b70d936df715c7448fb36f50dcb`
- Release state: not released; merge and immutable release evidence remain incomplete.

## Bounded context and ownership

NewsDOM owns document-ingestion and parsing truth, including the PDF parser version it executes on untrusted uploads and the parser authentication boundary. Dependency resolution is part of the NewsDOM runtime/supply-chain boundary; scanner policy remains owned by the repository and organization CI controls. Cross-cutting evidence is consolidated in this canonical baseline rather than copied into parallel feature branches.

The dependency invariant is that a future lock refresh must not select a version known vulnerable to a current parser finding. Scanner suppression is not an acceptable substitute for remediation. The authentication invariant is that `/parse` fails closed before multipart/body parsing and returns the existing fixed unauthorized response for invalid credentials.

## Active gap: pypdf advisory floor

Current primary advisory data establishes different patch boundaries:

- CVE-2026-84309 / GHSA-jp53-mhqp-8xcg: affected `<6.16.0`, fixed in 6.16.0;
- CVE-2026-84310 / GHSA-23w6-3w8w-8484: affected `<6.16.1`, fixed in 6.16.1;
- CVE-2026-84311 / GHSA-763m-79hh-57f2: affected `<6.16.1`, fixed in 6.16.1.

Therefore the direct compatibility floor that excludes all three vulnerable ranges is `pypdf>=6.16.1,<7.0`. The generated lock on the dependency candidate resolves pypdf 6.18.0 with hashes. `pyproject.toml`, editable-project metadata in `uv.lock`, regression tests, `CHANGELOG.md`, and `docs/doctoring/dependency-security-baseline.md` must agree on that floor.

### RED and repair lineage

The branch had two independent problems. First, operator-facing evidence and the security regression admitted or described weaker pypdf floors even though two current advisories require 6.16.1. Second, intervening descendants repeatedly mixed route-level `Form(max_length=50)`, generic Sentinel doctrine, unrelated dependency churn, and deletion of this canonical baseline into the pypdf repair. Those changes were restored by ordinary non-force descendants; current pypdf scope is limited to the dependency/security contract and its evidence.

### GREEN acceptance

1. `pyproject.toml` and `uv.lock` both declare `pypdf>=6.16.1,<7.0`, with a hash-locked resolved pypdf version >=6.16.1.
2. `tests/test_pypdf_security_floor.py` rejects weaker declaration, lock metadata, resolved artifact, stale documentation, and scanner suppression.
3. `CHANGELOG.md` and `docs/doctoring/dependency-security-baseline.md` distinguish the 6.16.0 and 6.16.1 advisory boundaries and describe the current 6.18.0 lock accurately.
4. Complete tests, 100% owned production statement/branch coverage and docstring gates, package/docs builds, Security Scan, SAST, CodeQL, container, fuzz, and scorecard evidence reach terminal success on the same SHA.
5. Security Scan reports none of CVE-2026-84309, CVE-2026-84310, or CVE-2026-84311 without suppression.
6. Independent current-head review has no unresolved valid finding.
7. Merge is a normal protected-branch merge. Dependent #823/#826 then restack as non-force descendants and acquire fresh exact-head evidence.

## Active gap: parser Bearer timing hardening

Python documents `hmac.compare_digest()` as the preferred secret-comparison primitive and notes that differing input lengths or types can theoretically reveal length/type information through timing. PR #842 narrows the unequal-length Bearer path so it performs an expected-token-length dummy comparison before returning the same unauthorized response. This is defense-in-depth hardening; no remotely exploitable severity, token-recovery feasibility, or risk-reduction percentage is asserted without representative timing distributions and an explicit attack model.

Intervening descendants on #842 deleted the dedicated comparison-contract regression, reintroduced temporary-file creation before PDF magic-byte rejection, and mixed unrelated lock/formatting changes. Those deltas were removed by an ordinary descendant; #842 now differs from protected `develop` only in `src/newsdom_api/main.py` and `tests/test_auth_compare_length_contract.py`.

### GREEN acceptance

- missing, malformed, duplicated, oversized, non-ASCII, wrong-length, and wrong-value credentials preserve the fixed fail-closed unauthorized contract;
- invalid authentication is rejected before multipart/body parsing;
- unequal-length and equal-length mismatch paths execute the intended comparison operands without wall-clock threshold tests pretending to prove constant time;
- exact-head pytest/100% coverage, Security Scan, SAST, CodeQL and independent review are terminal GREEN;
- no dependency lock, generic security doctrine, or parser-temporary-file behavior is owned by the auth PR.

## Active gap: unused `httpx2` development dependency

Protected `develop` still declares `httpx2>=2.4.0` in the `dev` extra. Repository history (#518) found no NewsDOM source/test import of `httpx2` and previously proposed removing it and its orphaned `httpcore2`/`truststore` lock entries. Recent auth descendants instead refreshed the lock to a newer `httpx2`, but that does not establish a product need for the dependency and is not an acceptable side effect of an authentication change.

The canonical repair should either remove the unused dependency with a resolver-generated lock or, if an actual consumer is demonstrated, declare the necessary supported floor and verify it in its own dependency-security lane. Authentication PRs must not own this lock delta. Exact install, tests, vulnerability scanning, SBOM and rollback evidence are required before merge.

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

Python Software Foundation. (2026). *hmac — Keyed-Hashing for Message Authentication*. Python 3.14 documentation. https://docs.python.org/3/library/hmac.html#hmac.compare_digest
