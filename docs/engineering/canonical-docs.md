# Canonical docs map

Use this index to decide which repository document is authoritative for a given question. When two sources disagree, prefer the narrower source that is demonstrably current with protected code/evidence, then repair the drift rather than leaving competing truths.

## Product and user-facing truth

- `README.md` — public overview, quickstart, release summary, and repository layout
- `manual/index.md` and the rest of `manual/` — published user manual
- `CHANGELOG.md` — released and unreleased user-visible change history
- `docs/PRD.md` — product users, current protected claims, active-PR boundaries, accepted targets, non-goals, release outcomes

## Technical and architecture truth

- `ARCHITECTURE.md` — current runtime/module responsibilities and integration shape
- `docs/TRD.md` — technical invariants, failure/resource/persistence/version contracts
- `docs/UML.md` — current runtime plus explicitly labelled active-PR/accepted-target sequences and state/authority views
- `docs/ERD.md` — current no-durable-database truth plus explicitly labelled accepted-target logical persistence model
- `docs/THREAT_MODEL.md` — product assets, trust boundaries, abuse cases, active/target mitigations
- `docs/TEST_STRATEGY.md` — realistic validation, scientific/fidelity/performance, concurrency, security, durable-job and release evidence contracts
- `docs/OPERABILITY.md` — health levels, SLIs, incidents, capacity, recovery, durable-job/backup target and release operations
- `docs/TRACEABILITY.md` — requirement/decision → source/evidence → maturity mapping
- `docs/adr/README.md` — durable architecture decisions and their Accepted/Proposed status

## Maintainer workflow truth

- `CONTRIBUTING.md` — maintainer setup, local verification, fixture policy, and documentation split
- `SECURITY.md` — reporting path and supported security branches
- `docs/workflow/git-flow.md` — branch model and merge targets
- `docs/workflow/pr-continuity.md` — canonical PR selection and stacked-PR handling
- `docs/workflow/one-day-delivery-plan.md` — default close-the-loop execution model

## Engineering control truth

- `AGENTS.md` — repository-local execution bootstrap
- `docs/agents/README.md` — agent-specific read order and local execution context
- `docs/coderabbit/review-commands.md` — supported review-bot control commands
- `docs/engineering/execution-policy.md` — task selection and execution behavior
- `docs/engineering/acceptance-criteria.md` — completion bar
- `docs/engineering/review-policy.md` — human + automation review expectations
- `docs/engineering/runtime-data-policy.md` — synthetic fixtures, private references, logs, secrets, and temp handling
- `docs/engineering/harness-engineering.md` — local and live verification harnesses
- `docs/engineering/skills-subagents-mcp.md` — subagent/MCP defaults
- `docs/security/api-security-checklist.md` — FastAPI API hardening baseline
- `docs/operations/deploy-runbook.md` — current deployment/release commands and runtime provisioning checks

## Planning truth

- `docs/plans/` — task-by-task implementation and design notes; planning is not protected product maturity
- `docs/adr/` — decisions intended to survive beyond one PR

## Maturity truth

The canonical product/architecture documents use explicit maturity instead of turning plans into shipped claims:

- protected implementation such as the current synchronous parser is labelled implemented/current;
- PR #539 authentication/readiness and PR #548 process-local parser admission remain active-PR until integrated;
- durable async jobs, tenant-scoped idempotency/fencing/replay and NewsDOM-owned job persistence remain accepted-target until source/migrations/evidence exist;
- `/health` is process liveness and must not be described as parser readiness;
- an active PR, local-only run, queued check, predecessor-head result, plan or diagram cannot promote maturity by itself.
