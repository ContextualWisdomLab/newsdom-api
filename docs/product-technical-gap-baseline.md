# NewsDOM product–technical gap baseline

Updated: 2026-09-08

## Current authority

- Protected branch: `develop@e06b1f3fb10903569124af011da213951e6e2473`
- Dependency-security repair lane: PR #822
- Current candidate before this document: `941263754627c6d0189e84b14c5be37fe3851543`
- Release state: not released; merge and immutable release evidence remain incomplete.

## Bounded context and ownership

NewsDOM owns document-ingestion and parsing truth, including the PDF parser version it executes on untrusted uploads. Dependency resolution is part of the NewsDOM runtime/supply-chain boundary; scanner policy remains owned by the repository and organization CI controls. This repair does not change the `/parse` API contract, MinerU invocation, authentication policy, or document-domain schema.

The relevant invariant is that a future lock refresh must not be allowed to select a pypdf version that is known vulnerable to any of the three current parser findings tracked by this lane. Scanner suppression is not an acceptable substitute for remediation.

## Active gap: pypdf advisory floor

Current primary advisory data establishes different patch boundaries:

- CVE-2026-84309 / GHSA-jp53-mhqp-8xcg: affected `<6.16.0`, fixed in 6.16.0;
- CVE-2026-84310 / GHSA-23w6-3w8w-8484: affected `<6.16.1`, fixed in 6.16.1;
- CVE-2026-84311 / GHSA-763m-79hh-57f2: affected `<6.16.1`, fixed in 6.16.1.

Therefore the direct compatibility floor that excludes all three vulnerable ranges is `pypdf>=6.16.1,<7.0`. The current generated lock resolves pypdf 6.18.0 with hashes. `pyproject.toml`, editable-project metadata in `uv.lock`, regression tests, `CHANGELOG.md`, and `docs/doctoring/dependency-security-baseline.md` must agree on that floor.

## RED and repair lineage

The branch had two independent problems. First, operator-facing evidence and the security regression still admitted or described 6.16.0/6.15.0 even though two current advisories require 6.16.1. Second, an intervening descendant reintroduced `Form(max_length=50)` changes and synthetic endpoint tests under an OOM claim that route-field validation had not demonstrated: multipart parsing occurs before route-field validation, so that delta did not establish the claimed pre-handler memory bound.

The repair preserves the valid dependency-security delta and restores the unrelated Form/OOM source, endpoint test, and branch-local Sentinel file from protected `develop` by ordinary non-force descendants. The security regression now requires 6.16.1 in the declaration, lock metadata, resolved artifact, and operator-facing evidence.

## GREEN acceptance

The dependency lane is GREEN only when one exact head demonstrates all of the following:

1. `pyproject.toml` and `uv.lock` both declare `pypdf>=6.16.1,<7.0`, with a hash-locked resolved pypdf version >=6.16.1.
2. `tests/test_pypdf_security_floor.py` passes and rejects weaker declaration, lock metadata, resolved artifact, stale documentation, and scanner suppression.
3. `CHANGELOG.md` and `docs/doctoring/dependency-security-baseline.md` distinguish the 6.16.0 and 6.16.1 advisory boundaries and describe the current 6.18.0 lock accurately.
4. Complete tests, 100% owned production statement/branch coverage and docstring gates, package/docs builds, Security Scan, SAST, CodeQL, container, fuzz, and scorecard evidence reach terminal success on that same SHA.
5. Security Scan reports none of CVE-2026-84309, CVE-2026-84310, or CVE-2026-84311 without suppression.
6. Independent current-head review has no unresolved valid finding.
7. Merge is a normal protected-branch merge. Dependent #823/#826 then restack as non-force descendants and acquire fresh exact-head evidence.

Queued, pending, cancelled, action-required, or unavailable checks are incomplete evidence, not success. Predecessor receipts, synthetic statuses, source-neutral retriggers, and weakened gates are not acceptance substitutes.

## Standards and traceability

The normative secure-development reference remains NIST SP 800-218, SSDF Version 1.1. NIST published SP 800-218 Rev. 1 / SSDF Version 1.2 as an Initial Public Draft on December 17, 2025; the current NIST CSRC publication index still marks Rev. 1 as Draft, with the public-comment period closed January 30, 2026. This baseline therefore treats SSDF 1.2 as informative draft material rather than final normative authority.

### References

National Institute of Standards and Technology. (2022). *Secure software development framework (SSDF) version 1.1: Recommendations for mitigating the risk of software vulnerabilities* (NIST Special Publication 800-218). https://doi.org/10.6028/NIST.SP.800-218

National Institute of Standards and Technology. (2025). *Secure software development framework (SSDF) version 1.2: Recommendations for mitigating the risk of software vulnerabilities* (NIST Special Publication 800-218 Rev. 1, Initial Public Draft). https://doi.org/10.6028/NIST.SP.800-218r1.ipd

Open Source Vulnerabilities. (2026a). *GHSA-jp53-mhqp-8xcg (CVE-2026-84309)*. Retrieved September 8, 2026, from https://osv.dev/vulnerability/GHSA-jp53-mhqp-8xcg

Open Source Vulnerabilities. (2026b). *GHSA-23w6-3w8w-8484 (CVE-2026-84310)*. Retrieved September 8, 2026, from https://osv.dev/vulnerability/GHSA-23w6-3w8w-8484

Open Source Vulnerabilities. (2026c). *GHSA-763m-79hh-57f2 (CVE-2026-84311)*. Retrieved September 8, 2026, from https://osv.dev/vulnerability/GHSA-763m-79hh-57f2
