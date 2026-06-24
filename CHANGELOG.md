# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-04-24

### Added

- Added `benchmark_ocr.py` tool to measure OCR engine performance and structural accuracy on private datasets.
- Deployed a GHCR prebuilt CI container image (`ghcr.io/seongho-bae/newsdom-api/ci-env`) to stabilize test environments and resolve timeout/dependency installation issues.

### Changed

- Updated `dom_builder.py` to preserve multi-page MinerU structure instead of collapsing multi-page outputs into a single page.
- Adjusted the `/parse` endpoint to return specific HTTP error codes (`502` and `503`) mapped to `MineruIncompleteOutputError` and `MineruRuntimeUnavailableError` rather than raw `500` errors.

### Fixed

- Mitigated infinite hang issues when processing specific PDFs by enforcing a strict timeout (300 seconds) in the `mineru` subprocess runner.
- Resolved permission (`EACCES`) issues in GitHub Actions by running tests locally instead of inside a non-root container context for GitHub's restricted runner environment.


## [0.1.1] - 2026-04-11

### Added

- GHCR-ready multi-arch API image delivery, ClusterFuzzLite coverage, and exported `*.intoto.jsonl` provenance bundles for stable releases
- Verified `/docs` and `/redoc` manual screenshots plus canonical engineering policy docs that describe the live repository workflow

### Changed

- Protected-branch governance documentation now reflects the current single-maintainer exception while preserving required checks and history protections
- Public setup guidance, docs-toolchain policy, and markdownlint scope now match the merged `develop` / `main` delivery paths

### Fixed

- Patched `pypdf` lockfile coverage to `6.10.0` for GHSA-3crg-w4f6-42mx / CVE-2026-40260

## [0.1.0] - 2026-04-09

### Added

- MinerU-backed DOM parsing API for scanned Japanese newspaper PDFs
- Synthetic newspaper fixture generation and structural equivalence checks
- Protected-branch CI, security gates, release provenance workflow, and Git Flow documentation

[Unreleased]: https://github.com/Seongho-Bae/newsdom-api/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Seongho-Bae/newsdom-api/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/Seongho-Bae/newsdom-api/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Seongho-Bae/newsdom-api/releases/tag/v0.1.0
