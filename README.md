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
- Language-agnostic: `language` defaults to `auto` detection (any MinerU
  language code is accepted; `japan` remains available)
- Parsing `mode` defaults to `auto` so born-digital text PDFs skip forced OCR
- Optional bearer auth on `/parse`; unauthenticated `/health` liveness probe

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

> Readiness caveat: `/health` reports process liveness only. Because the
> default image does not bundle MinerU, a container can report a green
> `/health` while `/parse` still returns `503` until a MinerU runtime is
> reachable. Treat MinerU availability as a separate readiness concern when
> wiring this sidecar into a larger system.

#### docker compose

A `docker-compose.yml` is provided for standalone/sidecar use. Its healthcheck
targets the unauthenticated `/health` endpoint:

```bash
docker compose up --build
```

Uncomment `NEWSDOM_MINERU_BIN` (path to a MinerU executable) and/or
`NEWSDOM_API_TOKEN` (bearer secret) in the compose `environment:` block to make
`/parse` functional and/or protected.

#### Building a MinerU-bundled image

To ship an image where `/parse` works behind a green `/health`, bundle a MinerU
runtime. Either build the NVIDIA variant below, or extend the default image and
install MinerU into the same virtualenv, for example:

```dockerfile
FROM newsdom-api:latest
USER root
RUN uv pip install --python /app/.venv/bin/python "mineru[pipeline]==3.4.0"
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
curl -F "file=@sample.pdf" http://127.0.0.1:8000/parse
```

`/parse` accepts `multipart/form-data` with a required `file` part
(`application/pdf`) and two optional form fields:

| Field | Default | Values | Maps to |
| ----- | ------- | ------ | ------- |
| `language` | `auto` | any MinerU language code (`auto`, `en`, `japan`, `korean`, `ch_server`, …) | MinerU `-l` |
| `mode` | `auto` | `auto`, `ocr`, `txt` | MinerU `-m` |

`mode=auto` lets born-digital (text-layer) PDFs skip forced OCR; `ocr` forces
optical recognition and `txt` extracts only the embedded text layer. Invalid
values return `422`. The previous Japanese-newspaper behavior is still available
explicitly:

```bash
curl -F "file=@sample.pdf" -F "language=japan" -F "mode=ocr" \
  http://127.0.0.1:8000/parse
```

#### Authentication

`/parse` is unauthenticated by default (development). Set the sidecar's own
`NEWSDOM_API_TOKEN` environment variable to require a bearer token:

```bash
NEWSDOM_API_TOKEN=$(openssl rand -hex 32) \
  uv run uvicorn --app-dir src newsdom_api.main:app
curl -F "file=@sample.pdf" -H "Authorization: Bearer $NEWSDOM_API_TOKEN" \
  http://127.0.0.1:8000/parse
```

Requests without a matching `Authorization: Bearer <token>` header receive
`401`. `/health` stays unauthenticated so orchestrators can always probe it.
Supply the token from your deployment's secret store rather than committing it.

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
```

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
