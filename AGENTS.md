# AGENTS.md

## Project overview

- Repository: `newsdom-api`
- Product: FastAPI service that converts MinerU OCR output into
  canonical NewsDOM JSON.
- Primary branch model: manual Git Flow (`develop` integration,
  `main` stable).

## Authoritative docs

Read these first when making repository changes:

- `docs/engineering/canonical-docs.md`
- `docs/engineering/execution-policy.md`
- `docs/engineering/acceptance-criteria.md`
- `docs/engineering/harness-engineering.md`
- `docs/engineering/review-policy.md`
- `docs/engineering/runtime-data-policy.md`
- `docs/engineering/skills-subagents-mcp.md`
- `docs/workflow/git-flow.md`
- `docs/workflow/pr-continuity.md`
- `docs/workflow/one-day-delivery-plan.md`
- `docs/operations/deploy-runbook.md`
- `docs/security/api-security-checklist.md`
- `docs/coderabbit/review-commands.md`
- `ARCHITECTURE.md`

## Setup and verification defaults

- Install: `uv sync --frozen --all-extras`
- Test: `uv run pytest`
- Coverage gate:
  `uv run pytest --cov=src/newsdom_api --cov-branch --cov-report=term-missing --cov-fail-under=100`
- Docs build: `uv run mkdocs build --strict`
- Local API: `uv run uvicorn --app-dir src newsdom_api.main:app --reload`

## Delivery defaults

- Branch normal work from `develop` unless the task is a `main`-only
  release or hotfix path.
- Keep PR continuity explicit with `gh pr view` / `gh pr list` /
  `pr_continuity` before opening duplicates.
- Treat CodeRabbit as advisory automation; required human approvals
  still follow the repository ruleset.
- When PRs are blocked externally, continue local adjacent tasks
  instead of stopping.

## Safety rules

- Keep synthetic fixtures public and private reference inputs
  local-only.
- Do not commit secrets, credentials, or copyrighted source
  newspaper material.
- Prefer durable evidence in tracked docs, tests, workflow runs,
  PR comments, and release assets over scratch notes.

<!-- BEGIN cwl-agent-guidance -->
## Agent guidance (CWL governance)

This section distills ContextualWisdomLab org governance. Any agent
(Claude, Codex, Cursor, opencode, Jules, …) working in this repo must
follow it.

### Security & review gate

- Every PR runs a central **Security Scan** required gate:
  `osv-scan` + `dependency-review` (diff-scoped) and `trivy-fs`
  (repo-wide, CRITICAL/HIGH, fixable only). It runs against every PR
  base, **including stacked PRs**.
- A failing **`trivy-fs` is a REAL finding, not a flake.** Read the job
  log (it prints each finding's rule id / severity / file) or the run's
  SARIF results, then **remediate**: bump the offending dependency
  (this repo pins via `pyproject.toml` + `uv.lock` — run
  `uv lock --upgrade-package <name>`), fix the Dockerfile misconfig, or
  add a narrow, documented `.trivyignore.yaml` entry for a genuine
  false positive. **Never weaken or disable the gate.**
- A local scan with a stale DB misses findings. Run
  `trivy --download-db-only` first, then scan the **merge ref**, not
  just the PR head.
- **Worked example (currently blocking this repo's PRs):** DS-0002
  (Dockerfile missing a non-root `USER`) and DS-0026 (no `HEALTHCHECK`)
  in `Dockerfile.test` and `.clusterfuzzlite/Dockerfile`. The runtime
  `Dockerfile` already sets `USER newsdom`; mirror that pattern (add a
  non-root `USER` and a `HEALTHCHECK`) where it is safe, or record a
  scoped `.trivyignore.yaml` note for the build-only images that
  legitimately need root. There are no k8s manifests here — trivy
  findings are Dockerfile- or dependency-scoped.
- The org `code_scanning` ruleset is intentionally **CodeQL-only**
  (multiple code-scanning tools cannot converge on one PR ref). Gating
  is by the Security Scan **job result**, not the `code_scanning` rule
  — do **not** add tools to that rule.

### Code exploration

- There is no `.codegraph/` index in this repo, so use normal search
  (grep/find, ripgrep) to locate and understand code. If a `.codegraph/`
  index is later added at the repo root, prefer CodeGraph
  (`codegraph explore "<query>"`, or the code-review-graph MCP tools)
  BEFORE grep/find — it surfaces callers/callees/impact that text
  search misses.
<!-- END cwl-agent-guidance -->

