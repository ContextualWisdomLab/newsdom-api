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

### Config & secrets (KV, not env)

- Org rule: do **not** read config/secrets via `os.getenv()` / raw
  environment variables at runtime. Read them from a KV / credential
  registry. Org Actions secrets (e.g. `OPENAI_API_KEY`) flow **into**
  the KV via a bootstrap/CI step; runtime reads from the KV — env is
  only transport into the KV, never the runtime source. Reference
  implementation: xtrmLLMBatchPython's pgcrypto-encrypted Postgres
  credential registry (`get_credential(name)`); reuse that pattern (a
  DB-backed KV is fine) unless a dedicated KV is adopted.
- **This repo today:** no runtime secrets or credentials — it holds no
  API keys, no DB creds, and makes no authenticated external calls (it
  shells out to a local MinerU binary). CI secrets are only the
  standard `GITHUB_TOKEN` / `SCORECARD_TOKEN`, which are build-time,
  not runtime app secrets.
- **Known deviation to migrate:** `mineru_runner._resolve_mineru_bin`
  reads `os.environ.get("NEWSDOM_MINERU_BIN")` (a local executable-path
  override) at runtime. This is a deployment knob, not a secret, so it
  is low-risk — but it is the one raw-env read here. The moment this
  service gains a real secret, credential, DB URL, or external endpoint,
  route it through the KV pattern above rather than adding more
  `os.getenv` reads.

### This repo's role in the ecosystem

- **This repo (`newsdom-api`):** a PDF -> DOM structure recognition
  sidecar (MinerU-based), generalized beyond Japanese newspapers to
  arbitrary PDFs; consumed by **naruon**.
- **The ecosystem:** CWL is an ecosystem built around **naruon** — the
  hub: an email/PIM system that DOM-decomposes emails and files into a
  persisted knowledge graph. Each component is a standalone program that
  must ALSO work as a git submodule, grown separately and together:
  - `wardnet` — WAF / IDS / AI SOC / load balancer / API management.
  - `clearfolio` — document viewer.
  - `pg-erd-cloud` — ERD tool.
  - `contextual-orchestrator` — LLM cost/perf/upstream-LB gateway
    (beyond LiteLLM).
  - `codec-carver` — STT / omni-modal speech-video codec.
  - `fast-mlsirm` — LLM-as-a-Judge calibration + evaluation-item quality
    (uses aFIPC FIPC + kaefa item-fit).
  - `feelanet-adfs` — passwordless SSO (OIDC/SCIM/ADFS/LDAP/FIDO2/
    OAuth2.1; eliminate passwords).
  - `newsdom-api` — PDF -> DOM sidecar (this repo).
  - `semantic-data-portal` — upper-ontology / catalog / governance plane
    with its own graph engine.

### Research grounding (attach paper PDFs)

- Org rule: substantive feature or process PRs should find the relevant
  academic papers and **commit their PDFs into the PR** (e.g. a
  `docs/papers/` or `references/` directory) with full citations,
  respecting copyright — attach the PDF only when redistribution is
  permissible; otherwise cite + link + summarize.
- Domain example for this repo: attach the document layout-analysis /
  DOM structure-recognition papers underpinning a MinerU/PDF change
  (e.g. layout detection, reading-order recovery, table structure
  recognition).
<!-- END cwl-agent-guidance -->
