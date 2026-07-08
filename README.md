# NewsDOM API

[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/Seongho-Bae/newsdom-api/badge)](https://securityscorecards.dev/viewer/?uri=github.com/Seongho-Bae/newsdom-api)

NewsDOM API parses scanned Japanese newspaper PDFs into DOM-like article trees.

## Features

- Primary engine: `MinerU` pipeline backend
- Service wrapper: FastAPI
- Output: canonical JSON with pages, articles, headlines, body
  blocks, images, captions, and quality metadata

## Quickstart

### Install

Install `uv` first if it is not already available in your `PATH`, then sync the
repository-managed virtual environment:

```bash
uv sync --frozen --all-extras
```

To enable real parsing with MinerU, install the MinerU CLI separately in the
same `.venv` that `uv sync` created:

```bash
uv pip install --python .venv/bin/python "mineru[pipeline]==3.4.0"
```

On Windows, replace `.venv/bin/python` with `.venv\Scripts\python.exe`.

### Run

```bash
uv run uvicorn --app-dir src newsdom_api.main:app --reload
```

### Docker

```bash
docker build -t newsdom-api .
docker run -p 8000:8000 newsdom-api
```

The default image exposes the REST API on port `8000` as a multi-arch service
image. It is suitable for `linux/amd64` and `linux/arm64`, including Apple
Silicon hosts running the API service inside Docker.

The default image ships the API service only and does not bundle the MinerU runtime.
`/parse` requires a compatible MinerU runtime to be available inside the container image or exposed through `NEWSDOM_MINERU_BIN`.

For heavier parsing deployments, build the optional NVIDIA-oriented variant:

```bash
docker build -f Dockerfile.nvidia -t newsdom-api:nvidia .
docker run --gpus all -p 8000:8000 newsdom-api:nvidia
```

`Dockerfile.nvidia` is intended for Linux/NVIDIA environments and is
`linux/amd64`-only. Apple Silicon can run the lean API image, but Docker
Desktop does not expose Apple GPU acceleration to Linux containers, so real
GPU-accelerated parsing should stay on a native Apple Silicon path instead of
the containerized runtime.

The NVIDIA variant is `linux/amd64`-only and is meant for hosts that can
provide the CUDA user-space/runtime stack required by MinerU.

### Parse a PDF

```bash
curl -F "file=@sample.pdf" http://127.0.0.1:8000/parse
```

Each request is written to a request-scoped temporary directory before MinerU
runs, and those temporary files are removed after the response completes.
Sanitized parse failures return `503 MinerU runtime unavailable` when the
runtime cannot be executed and `502 MinerU output was incomplete` when MinerU
finishes without the required output artifacts.

### Run tests

```bash
uv run pytest
```

### Fuzzing smoke

```bash
uv run python fuzzers/dom_builder_fuzzer.py --smoke tests/fixtures/mineru_sample.json
uv run python fuzzers/schema_response_fuzzer.py --smoke fuzzers/corpus/schema_response_fuzzer/valid_parse_response.json
uv run python fuzzers/equivalence_metrics_fuzzer.py --smoke fuzzers/corpus/equivalence_metrics_fuzzer/structural_metrics.json
```

Every `fuzzers/*_fuzzer.py` target is coverage-guided under Atheris and is
picked up automatically by the ClusterFuzzLite workflow, which runs a bounded
budget on each pull request. Targets cover the untrusted-input boundaries: the
MinerU DOM normalizer (`build_dom`), the `ParseResponse` schema validator, and
the equivalence metrics normalizer. See `docs/papers/` for background.

The repository also enforces a `quality-gate` workflow with 100% source
coverage and docstring audit coverage.

## Fixtures and provenance

This repository ships only synthetic test fixtures and derived structural
baselines. For fixture provenance and regeneration notes, see
`tests/fixtures/README.md`.

## Development

Development setup, fixture handling rules, and local-only baseline
maintenance are documented in `CONTRIBUTING.md`.

Mechanical branch updates and merges are attributed to `github-actions[bot]`.
Scratch PoC files are not committed. Failed GitHub Checks are not reviewed as URL lists.
OpenCode Review, Strix Security Scan, and PR Review Merge Scheduler are
provided by the organization-level required workflows in
`ContextualWisdomLab/.github`, not copied into this repository.

Security reporting guidance is documented in `SECURITY.md`.
Version tags trigger a GitHub-native release workflow that builds
distribution artifacts, checksums, and provenance attestations.

Project history is tracked in `CHANGELOG.md`.

Repository branch workflow is documented in `docs/workflow/git-flow.md`.

## Repository layout

- `src/newsdom_api/`: API, MinerU wrapper, DOM builder, synthetic fixture generator
- `tests/`: unit tests and committed synthetic fixtures
- `tools/`: local maintenance utilities
