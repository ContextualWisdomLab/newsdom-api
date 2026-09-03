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

The generated lock additionally resolves Click 8.4.2, setuptools 83.0.0,
Pillow 12.3.0, pypdf 6.16.2, mkdocs-material 9.7.7, and
pymdown-extensions 11.0.1. Direct floors prevent a later lock refresh from
silently selecting known-vulnerable ranges again.

## Threat and impact rationale

NewsDOM accepts untrusted PDF uploads. A parser denial of service is therefore a
runtime availability risk rather than an abstract transitive-dependency finding.
The earlier baseline raised pypdf to 6.14.2 for CVE-2026-59935. On August 8,
2026, the repository's current Trivy filesystem gate began reporting two
additional MEDIUM findings, CVE-2026-71852 and CVE-2026-71870, against the locked
6.14.2 artifact. The same repository had already produced a hash-locked 6.15.0
resolution on an isolated branch; that exact head completed the Security Scan
successfully without suppressing either finding. The shared direct floor and lock
therefore move together to 6.15.0 rather than hiding the findings in
`.trivyignore`.

On September 3, 2026, an unrelated PR's `trivy-fs` gate reported three further
MEDIUM findings against the locked 6.15.0 artifact: CVE-2026-84309 (an attacker
-crafted PDF whose cyclic `/Next` outline-tree structure drives
`TreeObject.insert_child` into an infinite loop on a writing code path),
CVE-2026-84310 (unbounded entry-count and nesting-depth traversal in
`_get_outline` allowing long runtimes and large memory use), and CVE-2026-84311
(a reused-XObject form graph without a memoized/visited guard in
`PageObject._extract_text`/`extract_xform_text`, producing exponentially many
traversal paths). All three are availability risks directly on NewsDOM's
untrusted PDF-ingestion path and are fixed upstream in pypdf 6.16.0/6.16.1
respectively. The direct floor and lock move together to 6.16.1 (lock resolves
6.16.2, the latest compatible release at the time of this record) rather than
suppressing the findings.

CVE-2026-59890 affects setuptools versions before 83.0.0. On
normalization-preserving macOS filesystems, specially named files could bypass
`MANIFEST.in` exclusion matching and enter a source distribution. Although this
is a build-time rather than request-time issue, it can compromise release
contents, so the build-system floor is raised to 83.0.0.

Pillow 12.3.0 and pypdf release artifacts are distributed through PyPI with
published cryptographic file digests. Those artifacts and digests provide
provenance inputs; they do not by themselves establish that a package is safe.
Repository scans, hash-locked resolution, current-head tests, and independent
review remain mandatory. PyPI's official JSON metadata confirms the 6.16.2
release and the artifact hashes recorded in this repository's generated lock.

## Secure-development and provenance controls

The control set follows the outcomes of the final NIST Secure Software
Development Framework (SSDF) 1.1: identify and remediate vulnerabilities, protect
software components, and retain evidence that acquirers can inspect. NIST's SSDF
1.2 revision is still an initial public draft as of this record and is treated as
informative rather than normative.

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
- `pyproject.toml` and `uv.lock` contain the same direct floors;
- dependency, filesystem, container, CodeQL, Semgrep, fuzzing, and scorecard
  checks complete successfully;
- no unresolved review thread remains;
- an independent current-head reviewer approves;
- the generated lock contains no scanner-reported known vulnerability at the
  repository's enforced severity threshold.

If hosted Actions reports `action_required`, queued, cancelled, or unavailable,
that state is not treated as success. The pull request remains unmerged until a
fresh current-head run supplies the required evidence.

## Residual risk

Version upgrades do not prove that every malformed PDF is safe to process.
NewsDOM still requires bounded upload size, parser timeouts, concurrency limits,
resource isolation, readiness reporting, and production telemetry. The current
change removes identified dependency vulnerabilities; it does not replace those
runtime controls or a corpus-based parser accuracy and resilience program.

## References

National Institute of Standards and Technology. (2022). *Secure software
    development framework (SSDF) version 1.1: Recommendations for mitigating the
    risk of software vulnerabilities* (NIST Special Publication 800-218).
    https://doi.org/10.6028/NIST.SP.800-218

National Institute of Standards and Technology. (2025). *Secure software
    development framework (SSDF) version 1.2: Recommendations for mitigating the
    risk of software vulnerabilities* (NIST Special Publication 800-218 Rev. 1,
    Initial Public Draft). https://doi.org/10.6028/NIST.SP.800-218r1.ipd

National Institute of Standards and Technology. (2026a). *CVE-2026-59935*.
    National Vulnerability Database. Retrieved August 4, 2026, from
    https://nvd.nist.gov/vuln/detail/CVE-2026-59935

National Institute of Standards and Technology. (2026b). *CVE-2026-59890*.
    National Vulnerability Database. Retrieved August 4, 2026, from
    https://nvd.nist.gov/vuln/detail/CVE-2026-59890

Open Source Vulnerabilities. (2026a). *CVE-2026-59935*. Retrieved August 4,
    2026, from https://osv.dev/vulnerability/CVE-2026-59935

Open Source Vulnerabilities. (2026b). *CVE-2026-59890*. Retrieved August 4,
    2026, from https://osv.dev/vulnerability/CVE-2026-59890

Open Source Vulnerabilities. (2026c). *CVE-2026-71852*. Retrieved August 9,
    2026, from https://osv.dev/vulnerability/CVE-2026-71852

Open Source Vulnerabilities. (2026d). *CVE-2026-71870*. Retrieved August 9,
    2026, from https://osv.dev/vulnerability/CVE-2026-71870

Open Source Vulnerabilities. (2026e). *CVE-2026-84309*. Retrieved September 3,
    2026, from https://osv.dev/vulnerability/CVE-2026-84309

Open Source Vulnerabilities. (2026f). *CVE-2026-84310*. Retrieved September 3,
    2026, from https://osv.dev/vulnerability/CVE-2026-84310

Open Source Vulnerabilities. (2026g). *CVE-2026-84311*. Retrieved September 3,
    2026, from https://osv.dev/vulnerability/CVE-2026-84311

Python Packaging Authority. (2026a). *Digital attestations*. PyPI Docs.
    Retrieved August 4, 2026, from https://docs.pypi.org/attestations/

Python Packaging Authority. (2026b). *Pillow 12.3.0*. Python Package Index.
    Retrieved August 4, 2026, from https://pypi.org/project/pillow/12.3.0/

Python Packaging Authority. (2026c). *pypdf 6.15.0*. Python Package Index.
    Retrieved August 9, 2026, from https://pypi.org/project/pypdf/6.15.0/

Python Packaging Authority. (2026d). *setuptools 83.0.0*. Python Package Index.
    Retrieved August 4, 2026, from https://pypi.org/project/setuptools/83.0.0/

Python Packaging Authority. (2026e). *pypdf 6.16.2*. Python Package Index.
    Retrieved September 3, 2026, from https://pypi.org/project/pypdf/6.16.2/
