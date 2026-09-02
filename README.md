# NewsDOM API

[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/ContextualWisdomLab/newsdom-api/badge)](https://securityscorecards.dev/viewer/?uri=github.com/ContextualWisdomLab/newsdom-api)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ContextualWisdomLab/newsdom-api)

**Turn PDFs into a stable, structured document tree that downstream systems can inspect instead of reverse-engineering parser output.**

NewsDOM API owns the HTTP, safety, normalization, and evidence boundary for PDF-to-DOM processing. It accepts a PDF, applies bounded admission and fail-closed request controls, and returns canonical JSON for pages, sections, headings, body blocks, images, captions, bounding boxes, and quality metadata.

The service is intentionally usable as a standalone FastAPI sidecar. A host application does not need to adopt NewsDOM's internal parser process, storage layout, or deployment model; it consumes the published HTTP/schema contract.

> **Commercial parser status:** the current source still contains a legacy MinerU adapter, but MinerU 3.x uses the MinerU Open Source License—Apache-2.0 plus additional commercial conditions. That runtime is **not an approved ContextualWisdomLab commercial dependency**. Do not treat MinerU installation, a customer-supplied MinerU binary, or `Dockerfile.nvidia` as an approved commercial deployment path. Issue [#671](https://github.com/ContextualWisdomLab/newsdom-api/issues/671) owns replacement with an unrestricted commercial-use parser boundary. NewsDOM's own source remains MIT-licensed.

## What NewsDOM owns

- A stable `POST /parse` contract for PDF input and normalized document-tree output.
- Language and parse-mode request validation, including `mode=auto`, `ocr`, and `txt` compatibility semantics while the legacy adapter remains present.
- Fail-closed bearer authentication for `/parse` in the production profile.
- Separate unauthenticated `/health` liveness and `/ready` traffic-readiness semantics.
- Bounded, non-waiting parser admission with `NEWSDOM_MAX_CONCURRENT_PARSES` and an explicit `429 Too Many Requests` overload response.
- Request-scoped temporary workspace handling, sanitized parser failures, schema validation, and synthetic fixture provenance.

NewsDOM does **not** make a third-party parser's license, model weights, OCR accuracy, or runtime availability part of its own MIT grant. It also does not turn `/health` into proof that parsing is ready.

## Quick start

### Install the repository-managed environment

NewsDOM source metadata currently requires Python `>=3.10,<3.14`.

```bash
uv sync --frozen --all-extras
```

`uv` creates the repository environment under `.venv`. On Windows the interpreter path is `.venv\Scripts\python.exe`; on macOS/Linux it is `.venv/bin/python`.

This command installs NewsDOM and its declared project dependencies only. It does **not** install the commercially restricted legacy MinerU runtime.

### Run the API shell

```bash
export NEWSDOM_AUTH_MODE=required
export NEWSDOM_RUNTIME_PROFILE=production
export NEWSDOM_API_TOKEN="$(openssl rand -hex 32)"
export NEWSDOM_MAX_CONCURRENT_PARSES=1
uv run uvicorn --app-dir src newsdom_api.main:app --reload
```

Check the two health levels independently:

```bash
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8000/ready
```

`/health` answers for process liveness. `/ready` is the routing gate and must remain unavailable when the configured parser runtime or required authentication state cannot accept traffic.

### Parse contract

Once an **organization-approved parser backend** is configured, the public request shape remains:

```bash
curl -F "file=@sample.pdf" \
  -H "Authorization: Bearer $NEWSDOM_API_TOKEN" \
  http://127.0.0.1:8000/parse
```

Optional compatibility fields are `language` and `mode`:

```bash
curl -F "file=@sample.pdf" -F "language=ch" -F "mode=auto" \
  -H "Authorization: Bearer $NEWSDOM_API_TOKEN" \
  http://127.0.0.1:8000/parse
```

An explicit OCR-mode request uses the same authenticated boundary:

```bash
curl -F "file=@sample.pdf" -F "language=korean" -F "mode=ocr" \
  -H "Authorization: Bearer $NEWSDOM_API_TOKEN" \
  http://127.0.0.1:8000/parse
```

The current source's legacy adapter may return `503 Service Unavailable` when no parser runtime is available. That is preferable to silently treating an unapproved runtime as production-ready.

## Capacity and failure behavior

`NEWSDOM_MAX_CONCURRENT_PARSES` is an integer from `1` through `128` and defaults to `1` per process. Authentication runs before admission. When all parser leases are occupied, the service returns `429 Too Many Requests` with `Retry-After: 1` and `Cache-Control: no-store` before multipart body processing, temporary-file allocation, PDF validation, or parser execution.

This is a last-resort per-process availability boundary, not a replacement for tenant-aware gateway limits or cluster resource quotas. Start with the conservative default, measure representative workloads, and scale replicas before raising per-process concurrency.

Expected malformed-document/parser failures are translated into bounded client-facing responses; unexpected server faults remain observable through the server-error path rather than being mislabeled as caller input.

## Containers

The default container is the supported repository image surface:

```bash
docker build -t newsdom-api .
docker run -p 8000:8000 \
  -e NEWSDOM_AUTH_MODE=required \
  -e NEWSDOM_RUNTIME_PROFILE=production \
  -e NEWSDOM_API_TOKEN="$NEWSDOM_API_TOKEN" \
  -e NEWSDOM_MAX_CONCURRENT_PARSES=1 \
  newsdom-api
```

The default image **ships the API service only** and **does not bundle the MinerU runtime**. It supports the repository's multi-architecture API shell, including Apple Silicon hosts running Linux containers, but `/ready` must stay fail-closed until an approved parser backend exists.

`Dockerfile.nvidia` is retained in current source history and tests as the existing NVIDIA/MinerU distribution path, but it is **commercially blocked under organization policy** and must not be built, published, recommended, or treated as a supported release profile until #671 replaces the restricted parser stack. The same restriction applies even on an NVIDIA host; moving the component into another image or process does not cure its license terms.

## Architecture and integration boundary

```text
client
  -> FastAPI request/auth boundary
  -> non-waiting parser admission
  -> bounded temporary PDF workspace
  -> parser adapter port
  -> NewsDOM normalization + schema validation
  -> canonical JSON response
```

The parser adapter is an implementation dependency. The stable product responsibility is the request, safety, evidence, and normalized-output contract around it. The replacement work in #671 should preserve that boundary rather than make downstream callers depend on another parser's internal types.

For deeper design and current-vs-target maturity, see [ARCHITECTURE.md](ARCHITECTURE.md), the [ADR index](docs/adr/README.md), and the canonical documentation under [`docs/`](docs/).

## Verification

Run the repository suite:

```bash
uv run pytest
```

The repository quality gate requires 100% configured source coverage and docstring audit coverage. Security, dependency, image, fuzzing, and package checks run independently in CI.

A local fuzzing smoke remains available against committed synthetic fixtures:

```bash
uv run python fuzzers/dom_builder_fuzzer.py --smoke tests/fixtures/mineru_sample.json
uv run python fuzzers/schema_response_fuzzer.py --smoke fuzzers/corpus/schema_response_fuzzer/valid_parse_response.json
uv run python fuzzers/equivalence_metrics_fuzzer.py --smoke fuzzers/corpus/equivalence_metrics_fuzzer/structural_metrics.json
```

The historical `mineru_sample.json` fixture name records parser provenance; it is not an instruction to install the MinerU runtime.

## Documentation

- [Public manual](manual/index.md) — product and integration entry point.
- [Architecture](ARCHITECTURE.md) — system ownership and current/target boundaries.
- [Security](SECURITY.md) — vulnerability reporting and security posture.
- [Contributing](CONTRIBUTING.md) — development and validation workflow.
- [Fixtures and provenance](tests/fixtures/README.md) — synthetic fixture source and regeneration rules.
- [Git flow](docs/workflow/git-flow.md) — repository branch workflow.
- [Changelog](CHANGELOG.md) — source change history; not release evidence by itself.
- [Commercial parser replacement #671](https://github.com/ContextualWisdomLab/newsdom-api/issues/671) — current parser-license blocker and acceptance contract.

GitHub Pages source lives under `manual/`. A source commit is not proof that the public site deployed; publication requires the Pages workflow to finish and the live HTTPS content to be re-read.

## Status

`pyproject.toml` currently records NewsDOM source version `0.2.0`. Source metadata, an open PR, or a passing check is not by itself a published-release or commercial-readiness claim. Consult [GitHub Releases](https://github.com/ContextualWisdomLab/newsdom-api/releases) for immutable published release evidence.

The current parser-license blocker means the repository must not be represented as commercially complete even when NewsDOM-owned tests are green.

## License

NewsDOM API original source and documentation are licensed under the [MIT License](LICENSE). Third-party packages, parser runtimes, model weights, container bases, fonts, datasets, and other external assets retain their own licenses and distribution terms.

The MIT grant does not relicense the legacy MinerU runtime. Under current ContextualWisdomLab policy, that runtime is outside the approved commercial inbound baseline and remains blocked by #671.
