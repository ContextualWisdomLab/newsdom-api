# Canonical docs map

Use this index to decide which repository document is authoritative
for a given question.

## Product and user-facing truth

- `README.md` — public overview, quickstart, release summary, and
  repository layout
- `manual/index.md` and the rest of `manual/` — published user
  manual
- `CHANGELOG.md` — released and unreleased user-visible change history

## Maintainer workflow truth

- `CONTRIBUTING.md` — maintainer setup, local verification,
  fixture policy, and documentation split
- `SECURITY.md` — reporting path and supported security branches
- `docs/workflow/git-flow.md` — branch model and merge targets
- `docs/workflow/pr-continuity.md` — canonical PR selection and
  stacked-PR handling
- `docs/workflow/one-day-delivery-plan.md` — default
  close-the-loop execution model

## Engineering control truth

- `AGENTS.md` — repository-local execution bootstrap
- `ARCHITECTURE.md` — runtime structure and module responsibilities
- `docs/agents/README.md` — agent-specific read order and local
  execution context
- `docs/coderabbit/review-commands.md` — supported review-bot control
  commands
- `docs/engineering/execution-policy.md` — task selection and
  execution behavior
- `docs/engineering/acceptance-criteria.md` — completion bar
- `docs/engineering/review-policy.md` — human + automation review
  expectations
- `docs/engineering/runtime-data-policy.md` — synthetic fixtures,
  logs, secrets, and tmp handling
- `docs/engineering/harness-engineering.md` — local and live verification harnesses
- `docs/engineering/skills-subagents-mcp.md` — subagent/MCP defaults
- `docs/security/api-security-checklist.md` — API hardening baseline
  for FastAPI surface changes
- `docs/doctoring/` — standards, papers, and APA 7th citations that
  justify runtime boundaries (authentication, isolated PDF validation)

## Planning truth

- `docs/plans/` — task-by-task implementation and design notes
- `docs/adr/` — decisions that should survive beyond a single PR

When two sources disagree, prefer the narrower and more recently
verified source, then repair the drift.
