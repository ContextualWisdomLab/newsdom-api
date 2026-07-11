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

## Security gates and `.trivyignore`

- The blocking `trivy-fs` PR check is not defined in this repository. It is
  part of the central "Security Scan" required workflow
  (`ContextualWisdomLab/.github`, `.github/workflows/security-scan.yml`),
  which runs `trivy fs .` repo-wide and fails on fixable
  CRITICAL/HIGH/MEDIUM findings. Do not reintroduce a repo-local copy.
- When `trivy-fs` fails, read the "Print Trivy findings that failed the
  gate" step in the job log (it lists severity, rule id, file, and message)
  or the `trivy-fs` SARIF in code scanning. Never guess at what Trivy found.
- The gate scans the PR head repo-wide, so stale branches inherit findings
  that are already fixed on `develop`. Rebase or merge `develop` first;
  only treat a finding as real if it reproduces on top of current `develop`.
- Remediation order: bump the vulnerable dependency
  (`uv lock --upgrade-package <name>` plus lockfile commit) or fix the
  misconfiguration. `.trivyignore` is the last resort, only for findings the
  repository genuinely cannot fix, and every entry must follow the documented
  format (id, affected artifact, why unfixable here, revisit condition —
  enforced by `tests/test_fuzzing_integration.py`). Trivy reads the plain
  `.trivyignore` at the repo root automatically; no workflow wiring needed.
- Anti-pattern (2026-07-09, PR #315): automation added Go-ecosystem
  CVE-2021-4238/CVE-2022-26945 to `.trivyignore` in this Go-free Python
  repository while the real blocker was DS-0002 on a stale PR base. Ignore
  entries that do not correspond to a reproduced finding are forbidden.

## Safety rules

- Keep synthetic fixtures public and private reference inputs
  local-only.
- Do not commit secrets, credentials, or copyrighted source
  newspaper material.
- Prefer durable evidence in tracked docs, tests, workflow runs,
  PR comments, and release assets over scratch notes.
