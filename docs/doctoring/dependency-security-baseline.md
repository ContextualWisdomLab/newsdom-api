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
- `mkdocs-material>=9.7,<9.8`, allowing `pymdown-extensions>=11` while the MkDocs
  core remains on the supported 1.x line.

The generated lock resolves Click 8.4.2, setuptools 83.0.0, Pillow 12.3.0,
pypdf 6.18.0, mkdocs-material 9.7.7, and pymdown-extensions 11.0.1. Direct
floors prevent a later lock refresh from silently selecting a known-vulnerable
range even when the current resolved artifact is already newer than the floor.

## Threat and impact rationale

NewsDOM accepts untrusted PDF uploads. Parser resource exhaustion is therefore a
runtime availability risk rather than an abstract transitive-dependency finding.
The current pypdf boundary is driven by three upstream advisories published in
August 2026:

- GHSA-jp53-mhqp-8xcg / CVE-2026-84309 affects pypdf versions before 6.16.0
  and is fixed in 6.16.0. The affected path can loop indefinitely while
  inserting a child into a crafted tree structure.
- GHSA-23w6-3w8w-8484 / CVE-2026-84310 affects versions before 6.16.1 and is
  fixed in 6.16.1. Crafted document outlines can cause excessive runtime and
  memory use.
- GHSA-763m-79hh-57f2 / CVE-2026-84311 affects versions before 6.16.1 and is
  fixed in 6.16.1. Crafted, repeatedly reused XForm objects can cause excessive
  iteration, runtime, and memory use during text extraction.

Because two of the three findings remain affected at 6.16.0, the direct
compatibility floor covering the complete current finding set is 6.16.1, not
6.16.0. The present lock resolves pypdf 6.18.0. Both the declared requirement
and generated editable-project metadata must carry the 6.16.1 floor so a future
lock refresh cannot select 6.16.0. No current pypdf finding is accepted through
`.trivyignore`.

CVE-2026-59890 affects setuptools versions before 83.0.0. On
normalization-preserving macOS filesystems, specially named files could bypass
`MANIFEST.in` exclusion matching and enter a source distribution. Although this
is a build-time rather than request-time issue, it can compromise release
contents, so the build-system floor is raised to 83.0.0.

Pillow 12.3.0 and pypdf release artifacts are distributed through PyPI with
published cryptographic file digests. Those artifacts and digests provide
provenance inputs; they do not by themselves establish that a package is safe.
Repository scans, hash-locked resolution, current-head tests, and independent
review remain mandatory. The project lock currently resolves pypdf 6.18.0; a
security floor is a compatibility constraint, not evidence that every later
release is vulnerability-free.

## Secure-development and provenance controls

The normative control set follows NIST Secure Software Development Framework
(SSDF) version 1.1, SP 800-218. NIST published the Initial Public Draft of
SP 800-218 Rev. 1 / SSDF version 1.2 on December 17, 2025; NIST's publication
catalog still lists that revision as Draft as of September 2026. Version 1.2 is
therefore informative for this record rather than the normative baseline.

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
- `pyproject.toml` and `uv.lock` contain the same pypdf direct floor;
- the resolved pypdf artifact is at least 6.16.1;
- CVE-2026-84309, CVE-2026-84310, and CVE-2026-84311 are not suppressed;
- dependency, filesystem, container, CodeQL, Semgrep, fuzzing, and scorecard
  checks complete successfully;
- no unresolved actionable review thread remains;
- an independent current-head reviewer approves;
- the generated lock contains no scanner-reported known vulnerability at the
  repository's enforced severity threshold.

If hosted Actions reports `action_required`, queued, cancelled, unavailable, or
failed, that state is not treated as success. The pull request remains unmerged
until a fresh current-head run supplies the required evidence.

## Residual risk

Version upgrades do not prove that every malformed PDF is safe to process.
NewsDOM still requires bounded upload size, parser timeouts, concurrency limits,
resource isolation, readiness reporting, and production telemetry. The current
change removes identified dependency vulnerabilities; it does not replace those
runtime controls or a corpus-based parser accuracy and resilience program.

## References

Booth, H., Ogata, M., Kent, K., Souppaya, M., & Dodson, D. (2025). *Secure
    software development framework (SSDF) version 1.2: Recommendations for
    mitigating the risk of software vulnerabilities* (NIST Special Publication
    800-218 Rev. 1, Initial Public Draft). National Institute of Standards and
    Technology. https://doi.org/10.6028/NIST.SP.800-218r1.ipd

National Institute of Standards and Technology. (2026). *Secure Software
    Development Framework: Publications*. Retrieved September 8, 2026, from
    https://csrc.nist.gov/projects/ssdf/publications

Scarfone, K., Souppaya, M., & Dodson, D. (2022). *Secure software development
    framework (SSDF) version 1.1: Recommendations for mitigating the risk of
    software vulnerabilities* (NIST Special Publication 800-218). National
    Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-218

py-pdf. (2026a, August 13). *Possible infinite loop when inserting a child into
    crafted tree structures* [Security advisory GHSA-jp53-mhqp-8xcg]. GitHub.
    https://github.com/py-pdf/pypdf/security/advisories/GHSA-jp53-mhqp-8xcg

py-pdf. (2026b, August 14). *Possible long runtimes/large memory usage when
    retrieving outlines* [Security advisory GHSA-23w6-3w8w-8484]. GitHub.
    https://github.com/py-pdf/pypdf/security/advisories/GHSA-23w6-3w8w-8484

py-pdf. (2026c, August 14). *Possible long runtimes/large memory usage when
    extracting XForm objects* [Security advisory GHSA-763m-79hh-57f2]. GitHub.
    https://github.com/py-pdf/pypdf/security/advisories/GHSA-763m-79hh-57f2

Open Source Vulnerabilities. (2026a). *CVE-2026-84309*. Retrieved September 8,
    2026, from https://osv.dev/vulnerability/CVE-2026-84309

Open Source Vulnerabilities. (2026b). *CVE-2026-84310*. Retrieved September 8,
    2026, from https://osv.dev/vulnerability/CVE-2026-84310

Open Source Vulnerabilities. (2026c). *CVE-2026-84311*. Retrieved September 8,
    2026, from https://osv.dev/vulnerability/CVE-2026-84311

Python Packaging Authority. (2026a). *Digital attestations*. PyPI Docs.
    Retrieved September 8, 2026, from https://docs.pypi.org/attestations/

Python Packaging Authority. (2026b). *Pillow 12.3.0*. Python Package Index.
    Retrieved September 8, 2026, from https://pypi.org/project/pillow/12.3.0/

Python Packaging Authority. (2026c). *pypdf 6.18.0*. Python Package Index.
    Retrieved September 8, 2026, from https://pypi.org/project/pypdf/6.18.0/

Python Packaging Authority. (2026d). *setuptools 83.0.0*. Python Package Index.
    Retrieved September 8, 2026, from https://pypi.org/project/setuptools/83.0.0/
