# Dependency security baseline

## Decision record

This record documents the security and supply-chain basis for dependency-only remediation in NewsDOM. The change does not alter the NewsDOM API, response schema, MinerU invocation contract, or runtime authorization behavior. It raises vulnerable resolved dependencies, preserves bounded declared ranges, synchronizes `pyproject.toml` metadata with `uv.lock`, and requires ordinary current-head test, coverage, package, container, SAST, dependency, and independent-review gates before merge.

The declared dependency ranges are:

- `setuptools>=83` for the build backend;
- `Pillow>=12.3,<13.0` for image parsing on the untrusted document-ingestion path;
- `pypdf>=6.16.0,<7.0` for PDF parsing;
- `mkdocs-material>=9.7,<9.8`, allowing `pymdown-extensions>=11` while MkDocs core remains on the supported 1.x line.

The generated lock resolves Click 8.4.2, setuptools 83.0.0, Pillow 12.3.0, pypdf 6.18.0, mkdocs-material 9.7.7, and pymdown-extensions 11.0.1. The pypdf declaration and lock metadata remain aligned at `>=6.16.0,<7.0`, while repository acceptance additionally rejects any resolved pypdf version below 6.16.1. That second invariant is necessary because CVE-2026-84310 and CVE-2026-84311 were disclosed after the earlier 6.16.0 compatibility floor had been introduced.

## Threat and impact rationale

NewsDOM accepts untrusted PDF uploads, so parser denial of service is a runtime availability risk rather than an abstract transitive-dependency finding. The earlier baseline raised pypdf for CVE-2026-59935, CVE-2026-71852, and CVE-2026-71870. On September 8, 2026, the exact-head Trivy filesystem gate for PR #823 reported three additional MEDIUM pypdf findings against the protected-base lock: CVE-2026-84309, CVE-2026-84310, and CVE-2026-84311. No scanner suppression was added.

The pypdf maintainers document CVE-2026-84309 as an infinite-loop condition in `TreeObject.insert_child`, fixed in 6.16.0. They document CVE-2026-84310 as asymmetric resource consumption while retrieving outlines, fixed in 6.16.1. The companion XForm extraction issue, CVE-2026-84311, is likewise fixed in 6.16.1. Therefore 6.16.1 is the minimum acceptable resolved version for the currently known set, while this branch locks the signed 6.18.0 release published September 7, 2026.

The Form-field `max_length` change originally bundled into this branch is not treated as a pre-parser memory-exhaustion control. FastAPI validates route fields only after the multipart layer has materialized the form data needed for validation. The production route and generalized Sentinel doctrine are therefore restored to the protected branch; request-body admission remains a separate transport/runtime boundary.

CVE-2026-59890 affects setuptools versions before 83.0.0. On normalization-preserving macOS filesystems, specially named files could bypass `MANIFEST.in` exclusion matching and enter a source distribution. Although this is a build-time rather than request-time issue, it can compromise release contents, so the build-system floor remains 83.0.0.

Pillow and pypdf release artifacts are distributed through PyPI with cryptographic file digests. Those artifacts and digests are provenance inputs; they do not by themselves establish that a package is safe. Repository scans, hash-locked resolution, current-head tests, and independent review remain mandatory.

## Secure-development and provenance controls

The control set follows the outcomes of NIST SP 800-218 SSDF 1.1: identify and remediate vulnerabilities, protect software components, and retain evidence that acquirers can inspect. NIST's SSDF 1.2 revision remains informative for this decision rather than being claimed as a formal conformance target.

The lock and release evidence follow these rules:

1. dependencies resolve into one reviewable lock with cryptographic hashes;
2. declared direct ranges and generated lock metadata are tested for consistency;
3. the resolved pypdf artifact must be at least 6.16.1 even though the compatible declaration begins at 6.16.0;
4. security scanners run on the exact pull-request head and current CVE IDs remain unsuppressed;
5. build and wheel smoke tests execute from the locked environment;
6. a dependency PR alone does not create a release; protected-branch verification and the normal release process remain required.

This record does not claim formal NIST, SLSA, or PyPI-attestation conformance for NewsDOM. It records the evidence and boundaries used for this decision.

## Verification contract

Before merge, the exact current head must prove all of the following:

- complete repository tests pass;
- production statement and branch coverage remain 100%;
- the production docstring gate passes;
- `pyproject.toml` and `uv.lock` contain the same declared direct range;
- the resolved pypdf package is at least 6.16.1 and the current lock is 6.18.0;
- dependency, filesystem, container, CodeQL, Semgrep, fuzzing, and scorecard checks complete successfully;
- no unresolved review thread remains and an independent current-head reviewer approves;
- the generated lock contains no scanner-reported known vulnerability at the repository's enforced severity threshold.

If hosted Actions reports `action_required`, queued, cancelled, or unavailable, that state is not treated as success. The pull request remains unmerged until a fresh current-head run supplies the required evidence.

## Residual risk

Version upgrades do not prove that every malformed PDF is safe to process. NewsDOM still requires bounded upload size, parser timeouts, concurrency limits, resource isolation, readiness reporting, and production telemetry. The current change removes identified dependency vulnerabilities from the locked production generation; it does not replace those runtime controls or a corpus-based parser accuracy and resilience program.

The direct requirement still expresses compatibility from 6.16.0 while the lock acceptance rule requires 6.16.1 or newer. That distinction is deliberate and test-enforced in this generation. A future dependency-policy change may narrow the declared range as well, but it must update the generated lock metadata in the same commit rather than leaving `pyproject.toml` and `uv.lock` inconsistent.

## References

GitHub. (2026a). *pypdf: Possible infinite loop for TreeObject.insert_child* (GHSA-jp53-mhqp-8xcg; CVE-2026-84309). https://github.com/py-pdf/pypdf/security/advisories/GHSA-jp53-mhqp-8xcg

GitHub. (2026b). *pypdf: Possible long runtimes/large memory usage when retrieving outlines* (GHSA-23w6-3w8w-8484; CVE-2026-84310). https://github.com/py-pdf/pypdf/security/advisories/GHSA-23w6-3w8w-8484

GitHub. (2026c). *pypdf: Possible long runtimes/large memory usage when extracting XForm objects* (GHSA-763m-79hh-57f2; CVE-2026-84311). https://github.com/py-pdf/pypdf/security/advisories/GHSA-763m-79hh-57f2

GitHub. (2026d). *pypdf 6.18.0* [Software release]. https://github.com/py-pdf/pypdf/releases/tag/6.18.0

National Institute of Standards and Technology. (2022). *Secure software development framework (SSDF) version 1.1: Recommendations for mitigating the risk of software vulnerabilities* (NIST Special Publication 800-218). https://doi.org/10.6028/NIST.SP.800-218

Open Source Vulnerabilities. (2026a). *CVE-2026-59935*. https://osv.dev/vulnerability/CVE-2026-59935

Open Source Vulnerabilities. (2026b). *CVE-2026-59890*. https://osv.dev/vulnerability/CVE-2026-59890

Open Source Vulnerabilities. (2026c). *CVE-2026-71852*. https://osv.dev/vulnerability/CVE-2026-71852

Open Source Vulnerabilities. (2026d). *CVE-2026-71870*. https://osv.dev/vulnerability/CVE-2026-71870

Open Source Vulnerabilities. (2026e). *CVE-2026-84309*. https://osv.dev/vulnerability/CVE-2026-84309

Open Source Vulnerabilities. (2026f). *CVE-2026-84310*. https://osv.dev/vulnerability/CVE-2026-84310

Open Source Vulnerabilities. (2026g). *CVE-2026-84311*. https://osv.dev/vulnerability/CVE-2026-84311

Python Packaging Authority. (2026a). *Digital attestations*. PyPI Docs. https://docs.pypi.org/attestations/

Python Packaging Authority. (2026b). *Pillow 12.3.0*. Python Package Index. https://pypi.org/project/pillow/12.3.0/

Python Packaging Authority. (2026c). *pypdf 6.18.0*. Python Package Index. https://pypi.org/project/pypdf/6.18.0/

Python Packaging Authority. (2026d). *setuptools 83.0.0*. Python Package Index. https://pypi.org/project/setuptools/83.0.0/
