# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Start with AGENTS.md

`AGENTS.md` is the repository-local execution bootstrap for automated
agents. Read it first and follow the authoritative docs it lists —
especially `docs/engineering/canonical-docs.md` (the map of which
document is authoritative for a given question),
`docs/engineering/execution-policy.md`, and
`docs/engineering/acceptance-criteria.md`. `docs/agents/README.md`
defines the agent read order. This file complements those documents
with commands and an architecture orientation; if anything here
disagrees with them, they win.

## What this service is

`newsdom-api` is a FastAPI service that parses scanned Japanese
newspaper PDFs into DOM-like article trees: it runs the MinerU OCR
pipeline and converts its output into canonical NewsDOM JSON (pages,
articles, headlines, body blocks, images, captions, and quality
metadata).

## Common commands

```bash
# Install (uv-managed venv; uv.lock is the source of truth)
uv sync --frozen --all-extras

# Optional: real MinerU parsing in the same .venv
uv pip install --python .venv/bin/python "mineru[pipeline]==3.4.0"

# Run the API locally
uv run uvicorn --app-dir src newsdom_api.main:app --reload

# Tests
uv run pytest
uv run pytest tests/test_dom_builder.py            # single file
uv run pytest tests/test_health.py::test_healthcheck  # single test

# CI parity (quality-gate workflow + CircleCI run exactly these)
PYTHONWARNINGS=error uv run pytest
uv run pytest --cov=src/newsdom_api --cov-branch --cov-report=term-missing --cov-fail-under=100

# Docs (published manual under manual/, rendered by MkDocs)
uv run mkdocs build --strict

# Fuzzing smoke
uv run python fuzzers/dom_builder_fuzzer.py --smoke tests/fixtures/mineru_sample.json

# Container images
docker build -t newsdom-api .                              # lean API, multi-arch
docker build -f Dockerfile.nvidia -t newsdom-api:nvidia .  # GPU parsing, linux/amd64 only
```

Tests marked `integration` require the MinerU CLI and model cache
(see `[tool.pytest.ini_options]` markers in `pyproject.toml`).

## Architecture

`ARCHITECTURE.md` is the authoritative description. Short version:

- `src/newsdom_api/main.py` — FastAPI entrypoint exposing `/health`
  and `/parse`.
- `src/newsdom_api/service.py` — orchestrates PDF parsing,
  request-scoped temporary files, and response construction.
- `src/newsdom_api/mineru_runner.py` — shells out to the MinerU CLI
  (resolved via `NEWSDOM_MINERU_BIN` or PATH), collects JSON outputs,
  and raises typed sanitized exceptions.
- `src/newsdom_api/dom_builder.py` — normalizes MinerU
  `content_list` blocks plus page model metadata into the canonical
  NewsDOM response.
- `src/newsdom_api/schemas.py` — public Pydantic response schema.
- `src/newsdom_api/errors.py` — typed error definitions.
- `src/newsdom_api/synthetic.py` / `equivalence.py` — synthetic
  fixture generation and structural comparison.

Request flow: upload → temp workspace → MinerU run → DOM
normalization → typed JSON. MinerU runtime-unavailable failures map
to `503`; incomplete MinerU output maps to `502`. Error responses are
sanitized — no internal exception chains at the public boundary.

Supporting areas: `tests/fixtures/` (synthetic fixtures and
provenance notes), `tools/` (local CLI maintenance utilities such as
`parse_pdf.py`, `analyze_dom.py`, `validate_dom.py`), `fuzzers/`
(Atheris fuzzer run by ClusterFuzzLite), `manual/` (published
end-user manual, `mkdocs.yml` uses it as `docs_dir`), and
`scripts/release/` (release manifests and attestation export).

The default image ships the API only; `/parse` needs a MinerU runtime
in the container or via `NEWSDOM_MINERU_BIN`. `Dockerfile.nvidia` is
the heavy-parsing variant that bundles `mineru[pipeline]` on a CUDA
base for Linux/NVIDIA hosts.

## Branch model and conventions

- Manual Git Flow: `develop` is the default/integration branch;
  `main` is the stable release line. Branch `feature/*`, `fix/*`,
  `chore/*` from `develop` and target `develop`; `release/*` and
  `hotfix/*` target `main` and back-merge into `develop`. See
  `docs/workflow/git-flow.md` and `.github/pull_request_template.md`.
- TDD: write the failing test first, confirm the failure, then
  implement the minimal fix (`docs/engineering/execution-policy.md`).
- The quality gate is strict: 100% branch coverage over
  `src/newsdom_api`, warnings-as-errors pytest, and a docstring audit
  enforced by tests. New code without tests or docstrings fails CI.
- Docs are tested. Many tests (e.g. `tests/test_readme.py`,
  `tests/test_changelog.py`, `tests/test_workflows.py`,
  `tests/test_markdownlint_policy.py`) assert that README, CHANGELOG,
  workflows, and configs stay aligned — editing docs, Dockerfiles, or
  `.github/` automation can fail tests until the counterpart is
  updated.
- Fixture policy: only synthetic PDFs, synthetic sidecar JSON, and
  derived non-expressive structural metrics are committed. Never
  commit copyrighted newspaper PDFs, OCR text, or image crops from
  private reference pages (`CONTRIBUTING.md`).
- Supply-chain pins: CI installs from `uv.lock`, GitHub Actions are
  pinned by immutable commit SHA, and Docker base images are pinned
  by digest. Keep these policies intact when editing automation.
- Markdown style: markdownlint applies to `AGENTS.md`,
  `ARCHITECTURE.md`, `CONTRIBUTING.md`, and `docs/**/*.md`
  (config in `.markdownlint.jsonc` / `.markdownlint-cli2.jsonc`).
- Durable decisions go to `docs/adr/`; planning notes to
  `docs/plans/`. Prefer durable evidence (tests, docs, PR comments)
  over scratch notes.
