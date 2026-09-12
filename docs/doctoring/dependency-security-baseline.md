# Dependency security baseline

## Decision record

This record documents the security and supply-chain basis for dependency-only
remediation in NewsDOM. The change does not alter the NewsDOM API, response
schema, MinerU invocation contract, or runtime authorization behavior. It raises
vulnerable direct and resolved dependencies, preserves bounded version ranges,
synchronizes `pyproject.toml` with `uv.lock`, and requires the ordinary
current-head test, coverage, package, container, SAST, dependency, and independent
review gates before merge.

The adopted floors are:

- `setuptools>=83` for the build backend;
- `Pillow>=12.3,<13.0` for image parsing on the untrusted document-ingestion path;
- `pypdf>=6.16.1,<7.0` for PDF parsing;
- `httpx2>=2.12.0` and `httpcore2>=2.12.0` in the development/TestClient dependency
  set;
- `mkdocs-material>=9.7,<9.8`, allowing `pymdown-extensions>=11` while the MkDocs
  core remains on the supported 1.x line.

The generated lock resolves Click 8.4.2, setuptools 83.0.0, Pillow 12.3.0,
pypdf 6.18.0, HTTPX2 2.12.0, httpcore2 2.12.0, mkdocs-material 9.7.7, and
pymdown-extensions 11.0.1. Direct floors prevent a later lock refresh from
silently selecting known-vulnerable ranges again.

## Threat and impact rationale

NewsDOM accepts untrusted PDF uploads. A parser denial of service is therefore a
runtime availability risk rather than an abstract transitive-dependency finding.
The pypdf advisory boundary is not one version for all current findings:

- CVE-2026-84309 / GHSA-jp53-mhqp-8xcg affects pypdf before 6.16.0 and is fixed
  in 6.16.0;
- CVE-2026-84310 / GHSA-23w6-3w8w-8484 affects pypdf before 6.16.1 and is fixed
  in 6.16.1;
- CVE-2026-84311 / GHSA-763m-79hh-57f2 affects pypdf before 6.16.1 and is fixed
  in 6.16.1.

Because one direct compatibility floor must exclude all three vulnerable ranges,
NewsDOM requires `pypdf>=6.16.1,<7.0`. The generated lock currently resolves
pypdf 6.18.0 with hashes. The repository does not suppress these findings in
`.trivyignore`; scanner success must come from a remediated artifact.

The exact-head filesystem scan also exposed the TestClient HTTPX2 family as a
separate current lock vulnerability. The upstream HTTPX2 advisories establish
these patch boundaries:

- CVE-2026-84378 / GHSA-f2fp-rgf2-35cp: quadratic SSE line buffering is fixed in
  HTTPX2 2.10.0;
- CVE-2026-84379 / GHSA-h4x7-gw46-3wm6: multipart part-header injection is fixed
  in HTTPX2 2.11.0;
- CVE-2026-84380 / GHSA-pf96-p4fj-6566: conflicting `Content-Length` and
  `Transfer-Encoding` auto-generation is fixed in HTTPX2 2.11.0;
- CVE-2026-84381 / GHSA-7mj9-2mp8-4m2p: `wss://` traffic through SOCKS could omit
  TLS; HTTPX2 and httpcore2 2.10.0 are the fixed boundary;
- CVE-2026-84382 / GHSA-8xx6-hgc6-gc2m: streaming decompression could create an
  unbounded intermediate allocation and is fixed in HTTPX2 2.12.0.

The strongest current HTTPX2 boundary is therefore 2.12.0. NewsDOM declares both
`httpx2>=2.12.0` and `httpcore2>=2.12.0` in its development/TestClient dependency
set and resolves both to 2.12.0. This does not claim that every advisory is
reachable through NewsDOM production traffic; it removes known-vulnerable
artifacts from the repository's tested and scanned lock without weakening the
whole-tree security gate.

CVE-2026-59890 affects setuptools versions before 83.0.0. On
normalization-preserving macOS filesystems, specially named files could bypass
`MANIFEST.in` exclusion matching and enter a source distribution. Although this
is a build-time rather than request-time issue, it can compromise release
contents, so the build-system floor is raised to 83.0.0.

Pillow, pypdf, HTTPX2, and httpcore2 release artifacts are distributed through
PyPI with published cryptographic file digests. Those artifacts and digests
provide provenance inputs; they do not by themselves establish that a package is
safe. Repository scans, hash-locked resolution, current-head tests, and
independent review remain mandatory.

## Secure-development and provenance controls

The normative control basis remains the final NIST Secure Software Development
Framework (SSDF) Version 1.1, SP 800-218. NIST published SP 800-218 Rev. 1 / SSDF
Version 1.2 as an Initial Public Draft on December 17, 2025. NIST's current CSRC
publication index still classifies Rev. 1 as **Draft**; its public-comment period
closed January 30, 2026. Therefore this decision uses SSDF 1.1 normatively and
SSDF 1.2 only as informative draft material.

The lock and release evidence also align with the intent of modern package
provenance practices:

1. dependencies are resolved into one reviewable lock with cryptographic hashes;
2. declared direct floors and generated metadata are tested for consistency;
3. security scanners run on the exact pull-request head;
4. the build and wheel smoke tests execute from the locked environment;
5. a release is not created from this dependency PR alone; default-branch
   verification and the repository's normal release process remain required.

This record does not claim formal NIST, SLSA, or PyPI-attestation conformance for
NewsDOM. It records the evidence and boundaries used for this specific decision.

## Verification contract

Before merge, the exact current head must prove all of the following:

- complete repository tests pass;
- production statement and branch coverage remain 100%;
- the production docstring gate passes;
- `pyproject.toml` and `uv.lock` contain the same `pypdf>=6.16.1,<7.0` direct
  floor and the resolved pypdf artifact is at least 6.16.1;
- the development/TestClient set declares `httpx2>=2.12.0` and
  `httpcore2>=2.12.0`, and the lock resolves both to at least 2.12.0;
- CVE-2026-84309, CVE-2026-84310, CVE-2026-84311, CVE-2026-84378,
  CVE-2026-84379, CVE-2026-84380, CVE-2026-84381, and CVE-2026-84382 are absent
  from the dependency/filesystem scan without suppression;
- dependency, filesystem, container, CodeQL, Semgrep, fuzzing, and scorecard
  checks complete successfully on the same head;
- no unresolved valid review thread remains;
- an independent current-head reviewer approves;
- the generated lock contains no scanner-reported known vulnerability at the
  repository's enforced severity threshold.

If hosted Actions reports `action_required`, queued, cancelled, or unavailable,
that state is not treated as success. The pull request remains unmerged until a
fresh current-head run supplies the required evidence.

## Residual risk

Version upgrades do not prove that every malformed PDF, multipart request, or
HTTP response is safe to process. NewsDOM still requires bounded upload size,
parser timeouts, concurrency limits, resource isolation, readiness reporting,
and production telemetry. The current change removes identified dependency
vulnerabilities; it does not replace those runtime controls or a corpus-based
parser accuracy and resilience program.

## References

National Institute of Standards and Technology. (2022). *Secure software
development framework (SSDF) version 1.1: Recommendations for mitigating the
risk of software vulnerabilities* (NIST Special Publication 800-218).
https://doi.org/10.6028/NIST.SP.800-218

National Institute of Standards and Technology. (2025). *Secure software
development framework (SSDF) version 1.2: Recommendations for mitigating the
risk of software vulnerabilities* (NIST Special Publication 800-218 Rev. 1,
Initial Public Draft). https://doi.org/10.6028/NIST.SP.800-218r1.ipd

Open Source Vulnerabilities. (2026a). *GHSA-jp53-mhqp-8xcg (CVE-2026-84309)*.
Retrieved September 8, 2026, from
https://osv.dev/vulnerability/GHSA-jp53-mhqp-8xcg

Open Source Vulnerabilities. (2026b). *GHSA-23w6-3w8w-8484 (CVE-2026-84310)*.
Retrieved September 8, 2026, from
https://osv.dev/vulnerability/GHSA-23w6-3w8w-8484

Open Source Vulnerabilities. (2026c). *GHSA-763m-79hh-57f2 (CVE-2026-84311)*.
Retrieved September 8, 2026, from
https://osv.dev/vulnerability/GHSA-763m-79hh-57f2

Pydantic. (2026a). *Quadratic SSE line buffering can cause CPU denial of service*
(GHSA-f2fp-rgf2-35cp). GitHub Security Advisory.
https://github.com/pydantic/httpx2/security/advisories/GHSA-f2fp-rgf2-35cp

Pydantic. (2026b). *Multipart part header injection via unvalidated file
Content-Type and custom headers* (GHSA-h4x7-gw46-3wm6). GitHub Security Advisory.
https://github.com/pydantic/httpx2/security/advisories/GHSA-h4x7-gw46-3wm6

Pydantic. (2026c). *Conflicting Content-Length and Transfer-Encoding headers can
be auto-generated* (GHSA-pf96-p4fj-6566). GitHub Security Advisory.
https://github.com/pydantic/httpx2/security/advisories/GHSA-pf96-p4fj-6566

Pydantic. (2026d). *Secure WebSocket traffic sent without TLS through SOCKS
proxies* (GHSA-7mj9-2mp8-4m2p). GitHub Security Advisory.
https://github.com/pydantic/httpx2/security/advisories/GHSA-7mj9-2mp8-4m2p

Pydantic. (2026e). *Streaming response decompression does not bound peak memory*
(GHSA-8xx6-hgc6-gc2m). GitHub Security Advisory.
https://github.com/pydantic/httpx2/security/advisories/GHSA-8xx6-hgc6-gc2m

Python Packaging Authority. (2026a). *Digital attestations*. PyPI Docs.
Retrieved August 4, 2026, from https://docs.pypi.org/attestations/

Python Packaging Authority. (2026b). *Pillow 12.3.0*. Python Package Index.
Retrieved August 4, 2026, from https://pypi.org/project/pillow/12.3.0/

Python Packaging Authority. (2026c). *pypdf 6.18.0*. Python Package Index.
Retrieved September 8, 2026, from https://pypi.org/project/pypdf/6.18.0/

Python Packaging Authority. (2026d). *setuptools 83.0.0*. Python Package Index.
Retrieved August 4, 2026, from https://pypi.org/project/setuptools/83.0.0/
