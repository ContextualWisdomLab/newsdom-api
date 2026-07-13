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
