# NewsDOM API

[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/Seongho-Bae/newsdom-api/badge)](https://securityscorecards.dev/viewer/?uri=github.com/Seongho-Bae/newsdom-api)

NewsDOM API is a language-agnostic PDF-to-DOM sidecar. It converts any PDF
into a canonical JSON document tree — pages, sections, headings, body
blocks, images, captions, and bounding boxes — using MinerU. It runs as a
standalone FastAPI service and is designed to be embedded as a git
submodule / sidecar in a larger system.

## Features

- Primary engine: `MinerU` pipeline backend
- Service wrapper: FastAPI
- Output: canonical JSON with pages, sections, section headings, body
  blocks, images, captions, bounding boxes, and quality metadata
- Language-selectable: `language` defaults to MinerU's multilingual `ch` model;
  official language families and compatibility aliases such as `japan` remain
  available
- Parsing `mode` defaults to `auto` so born-digital text PDFs skip forced OCR
- Fail-closed bearer authentication on `/parse`; separate unauthenticated `/health` liveness and `/ready` traffic-readiness probes

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
uv pip install --python .venv/bin/python "mineru[pipeline]==3.4.4"
```

On Windows, replace `.venv/bin/python` with `.venv\Scripts\python.exe`.

### Run

```bash
export NEWSDOM_API_TOKEN="$(openssl rand -hex 32)"
uv run uvicorn --app-dir src newsdom_api.main:app --reload
```

### Docker

```bash
docker build -t newsdom-api .
docker run -e NEWSDOM_AUTH_MODE=required \
  -e NEWSDOM_RUNTIME_PROFILE=production \
  -e NEWSDOM_API_TOKEN="$NEWSDOM_API_TOKEN" \
  -e NEWSDOM_MAX_CONCURRENT_PARSES=1 \
  -p 8000:8000 newsdom-api
```

The default image exposes the REST API on port `8000` as a multi-arch service
image. It is suitable for `linux/amd64` and `linux/arm64`, including Apple
Silicon hosts running the API service inside Docker.

The default image ships the API service only and does not bundle the MinerU runtime.
`/parse` requires a compatible MinerU runtime to be available inside the container image or exposed through `NEWSDOM_MINERU_BIN`.

> `GET /health` reports process liveness only. `GET /ready` reports traffic
> readiness and remains unavailable until both fail-closed authentication and
> the MinerU runtime are configured. Orchestrators must route traffic by
> `/ready`, not by `/health`.

#### docker compose

A production-oriented `docker-compose.yml` is provided for standalone/sidecar
use. It requires `NEWSDOM_API_TOKEN` before startup and its healthcheck targets
`/ready`:

```bash
docker compose up --build
```

Export `NEWSDOM_API_TOKEN` from a secret store before running Compose. Mount or
bundle MinerU and set `NEWSDOM_MINERU_BIN` when using the API-only image. The
service remains live but not ready until both dependencies are valid.

#### Building a MinerU-bundled image

To ship an image where `/parse` works behind a green `/health`, bundle a MinerU
runtime. Either build the NVIDIA variant below, or extend the default image and
install MinerU into the same virtualenv, for example:

```dockerfile
FROM newsdom-api:latest
USER root
RUN uv pip install --python /app/.venv/bin/python "mineru[pipeline]==3.4.4"
USER newsdom
```

Alternatively mount a MinerU executable and point `NEWSDOM_MINERU_BIN` at it, so
`/parse` no longer returns `503` behind a healthy `/health`.

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
curl -F "file=@sample.pdf" \
  -H "Authorization: Bearer $NEWSDOM_API_TOKEN" \
  http://127.0.0.1:8000/parse
```

`/parse` accepts `multipart/form-data` with a required `file` part
(`application/pdf`) and two optional form fields:

| Field | Default | Values | Maps to |
| ----- | ------- | ------ | ------- |
| `language` | `ch` | MinerU 3.4.4 public family or alias (`ch`, `en`, `japan`, `korean`, `arabic`, `east_slavic`, `cyrillic`, `devanagari`, …) | MinerU `-l` |
| `mode` | `auto` | `auto`, `ocr`, `txt` | MinerU `-m` |

`mode=auto` lets born-digital (text-layer) PDFs skip forced OCR; `ocr` forces
optical recognition and `txt` extracts only the embedded text layer. Invalid
values return `422`. The previous Japanese-newspaper behavior is still available
explicitly:

```bash
curl -F "file=@sample.pdf" -F "language=japan" -F "mode=ocr" \
  -H "Authorization: Bearer $NEWSDOM_API_TOKEN" \
  http://127.0.0.1:8000/parse
```

The accepted language contract follows the official
[MinerU 3.4.4 CLI implementation](https://github.com/opendatalab/MinerU/blob/mineru-3.4.4-released/mineru/utils/ocr_language.py).
MinerU canonicalizes `en`, `japan`, `chinese_cht`, and `latin` to `ch`; this
sidecar performs the same normalization before launching the subprocess.

#### Authentication and readiness

Parser authentication is required by default. This replaces the previous
default-open behavior. Configure the explicit production contract and supply the
secret from the deployment secret store:

```bash
export NEWSDOM_AUTH_MODE=required
export NEWSDOM_RUNTIME_PROFILE=production
export NEWSDOM_API_TOKEN=$(openssl rand -hex 32)
export NEWSDOM_MAX_CONCURRENT_PARSES=1
uv run uvicorn --app-dir src newsdom_api.main:app
curl -F "file=@sample.pdf" -H "Authorization: Bearer $NEWSDOM_API_TOKEN" \
  http://127.0.0.1:8000/parse
```

Missing or invalid caller credentials receive a fixed `401`; a missing required
server token returns a fixed `503` before the upload body is processed. A
saturated replica returns a fixed `429` with `Retry-After: 1`. Wait one second
and retry; add replicas before raising `NEWSDOM_MAX_CONCURRENT_PARSES`. `GET
/health` remains unauthenticated liveness. `GET /ready` succeeds only when the
authentication configuration and MinerU runtime can accept traffic.

An isolated local development-only bypass is available only with the explicit
pair below:

```bash
NEWSDOM_AUTH_MODE=disabled \
NEWSDOM_RUNTIME_PROFILE=development \
  uv run uvicorn --app-dir src newsdom_api.main:app --reload
```

Do not use the development-only bypass as a production rollback. Restore a
working secret or the previous release instead.

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
