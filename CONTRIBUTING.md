# Contributing

## Development setup

Install `uv` first if it is not already available in your `PATH`, then sync the
repository-managed virtual environment:

```bash
uv sync --frozen --all-extras
```

Install the parser stack only when you need live MinerU execution:

```bash
uv pip install --python .venv/bin/python "mineru[pipeline]==3.0.9"
```

On Windows, replace `.venv/bin/python` with `.venv\Scripts\python.exe`.

## Test commands

```bash
uv run pytest
PYTHONWARNINGS=error uv run pytest
uv run pytest --cov=src/newsdom_api --cov-branch --cov-report=term-missing --cov-fail-under=100
```

CI installs dependencies from `uv.lock`, and workflow actions are
pinned by immutable commit SHA. Keep both policies intact when editing
`.github/` automation.

CircleCI parity is defined in `.circleci/config.yml` and mirrors the
same uv-locked warnings-as-errors and 100% coverage quality gate.

## Documentation build

The GitHub Pages workflow installs documentation tooling from
`uv.lock` via the optional `docs` extra. For local maintainer work,
sync all extras so the docs build does not drop the test toolchain
from the active environment.

The supported docs toolchain stays on the MkDocs 1.x line for now.
Keep `mkdocs<2.0` and `mkdocs-material<9.7` in place until the
upstream Material team publishes a workable migration path or this
repository validates a replacement docs stack. `uv.lock` is the source
of truth for the currently supported docs build.

```bash
uv sync --frozen --all-extras
uv run mkdocs build --strict
```

Use markdownlint for `AGENTS.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`,
and `docs/**/*.md`. The sweep excludes only the legacy
`git-flow-design`, `git-flow`, `newsdom-design`,
`newsdom-implementation`, `quality-gate-design`, and `quality-gate`
planning notes that predate the current markdown style policy.

Tagged releases use `.github/workflows/release.yml` to build
artifacts, generate SHA256 checksums, emit a JSON manifest, export
`*.intoto.jsonl` provenance bundles, and publish a GitHub Release with
provenance attestation.

For full OpenSSF Scorecard branch-protection visibility against
classic GitHub branch protection rules, set a repository secret named
`SCORECARD_TOKEN` with the fine-grained administration-read scope
recommended by the Scorecard Action documentation. Without that
secret, Scorecard still runs but may report the Branch-Protection
check as inconclusive.

## Fixture policy

This project intentionally separates public test artifacts from
private validation material.

Allowed in the repository:

- synthetic PDFs
- synthetic sidecar JSON
- derived, non-expressive structural metrics

Not allowed in the repository:

- copyrighted source newspaper PDFs
- OCR text copied from private reference pages
- image crops extracted from private reference pages

## Private baseline refresh

If you maintain a private reference page locally, refresh only the
derived structural baseline:

```bash
python tools/derive_private_baseline.py tests/fixtures/private_page_baseline.json
```

The source page must remain local.

## Documentation split

- `AGENTS.md`: repository-local execution bootstrap for autonomous
  maintenance
- `ARCHITECTURE.md`: runtime structure and module boundaries
- `README.md`: user-facing overview and quickstart
- `CONTRIBUTING.md`: maintainer workflow and safety rules
- `SECURITY.md`: vulnerability reporting and supported-branch policy
- `manual/`: published end-user manual rendered by MkDocs
- `docs/agents/README.md`: agent-specific read order and
  repository-local behavior notes
- `docs/coderabbit/review-commands.md`: supported CodeRabbit review
  commands used in PRs
- `docs/engineering/`: canonical maintainer policies and acceptance criteria
- `docs/operations/`: delivery and verification runbooks
- `docs/security/api-security-checklist.md`: API hardening checklist
  for FastAPI surface changes
- `docs/workflow/git-flow.md`: canonical branch workflow
- `docs/workflow/pr-continuity.md`: canonical PR-selection and
  stacked-PR guidance
- `tests/fixtures/README.md`: fixture provenance and regeneration notes
- `docs/plans/`: design and implementation planning notes

## Branch workflow

This repository uses a manual Git Flow model.

- Branch normal work from `develop`
- Open feature/fix/chore pull requests into `develop`
- Use `release/*` and `hotfix/*` only when stabilizing or patching production history

See `docs/workflow/git-flow.md` for the full branch model.
