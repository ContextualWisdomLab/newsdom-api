# Design: OCR accuracy program follow-through on fresh develop baseline

## Context

- This worktree is `feature/ocr-accuracy-program-followthrough-3`, created from
  the latest `origin/develop` reference (`27d0c05`).
- Fresh baseline verification already passed in this worktree:
  - `uv sync --frozen --all-extras`
  - `uv run pytest` → `139 passed`
- Current `develop` still has the page-collapse root cause:
  - `src/newsdom_api/service.py` forwards only `content_list`
  - `src/newsdom_api/dom_builder.py` hardcodes one page and ignores MinerU
    `model` metadata
  - `src/newsdom_api/schemas.py` exposes richer structures than the builder
    actually populates
- Current runtime/docs state is still partially inconsistent:
  - `Dockerfile` installs MinerU in the default image
  - `README.md` and `manual/api-reference.md` still contain stale runtime/run
    contract wording
  - deploy docs verify `/health` but do not meaningfully exercise `/parse`
- Current GitHub OCR program already has a canonical hierarchy and milestone:
  - milestone `v0.2.0 OCR accuracy and runtime readiness`
  - meta issue `#61`
  - sub-issues `#60`, `#62`, `#63`, `#64`
- Current open PR topology relevant to this work:
  - `#57` MinerU/mkdocs-material/pyinstaller dependency bump, milestone-linked but
    not linked to `#60-#64` in body/title
  - `#58` GitHub Actions dependency bump, no milestone/issue linkage
  - `#51` pypdf dependency bump, no milestone/issue linkage
- Local-only private OCR inputs exist at
  `/Users/seonghobae/Documents/newsdom-api/tests/copyrighted_fixtures_for_realities`
  as five flat PDF files with no adjacent redacted outputs or sidecars.

## Constraints

- Never commit copyrighted source PDFs, OCR text, rendered crops, or secrets.
- Durable evidence must be redacted and structural only: counts, warning types,
  status, sanitized summaries, and synthetic fixtures are allowed.
- Repository-local policy requires:
  - branch from `develop`, target `develop`
  - TDD for every behavior change
  - explicit GitHub issue/PR/workflow state checks before acting
- Acceptance still requires:
  - `uv run pytest`
  - `uv run pytest --cov=src/newsdom_api --cov-branch --cov-report=term-missing --cov-fail-under=100`
  - `uv run mkdocs build --strict` when user-facing docs change
  - targeted smoke checks for changed delivery paths
- API hardening remains in scope because `/parse` is an externally exposed OCR
  path:
  - do not leak private paths or raw subprocess errors
  - document and test sanitized failure behavior
  - keep abuse/rate/resource implications visible even if not fully solved in
    this slice
- Kubernetes/runtime concerns stay in scope for docs, smoke evidence, and deploy
  readiness even if the first implementation slice is application-level.
- Non-interactive default applies: do not stop for human review; use robot review
  and recorded evidence instead.

## Approaches considered

### 1. Start with private-fixture runtime debugging

- Pros:
  - immediately attacks the real-document runtime uncertainty
  - may surface host/container/runtime blockers early
- Cons:
  - leaves the already-proven page-collapse bug unfixed
  - depends on environment-specific runtime state before the deterministic code
    root cause is repaired
  - makes later benchmark interpretation noisier
- Verdict: useful follow-up, not the first implementation slice.

### 2. Restore page-aware normalization first, then sanitize runtime and docs (recommended)

- Pros:
  - fixes the known root cause described by `#62`
  - keeps the first change set deterministic and testable
  - allows real-document evidence and engine comparisons to run against the right
    DOM contract
  - fits the existing issue hierarchy in `#61`
- Cons:
  - runtime-safe failure handling and docs drift still need additional steps
  - requires schema/doc updates to keep the public contract honest
- Verdict: recommended.

### 3. Bundle normalization, runtime failure mapping, docs reconciliation, and benchmark workflow in one large change

- Pros:
  - one branch can narrate the whole OCR/runtime program
  - fewer rebases between related tasks
- Cons:
  - larger review and verification blast radius
  - mixes deterministic unit-testable work with environment-sensitive
    investigation and GitHub topology maintenance
- Verdict: acceptable as a branch-level sequence, not as one undivided task.

## Recommended design

Execute the program in five layers:

1. **Restore page-aware NewsDOM normalization (`#62`)**
2. **Add sanitized runtime/output failure handling for `/parse`**
3. **Reconcile runtime/manual/Kubernetes contract drift (`#64`)**
4. **Capture redacted local-only OCR evidence and benchmark prerequisites (`#60`, `#63`)**
5. **Refresh GitHub issue/PR continuity for adjacent open PRs and follow-up tasks**

### Layer 1: Page-aware normalization contract

- Update `src/newsdom_api/service.py` so `build_dom(...)` receives both
  `content_list` and `model`.
- Update `src/newsdom_api/dom_builder.py` to:
  - group blocks by `page_idx`
  - use `model[*].page_info.page_no`, width, and height when present
  - preserve deterministic page order
  - keep `header`, `footer`, `page_number`, and `ad` as page-scoped metadata
  - preserve caption/footnote/media metadata for image/table/chart blocks
  - emit quality warnings when page assignment is ambiguous or content/model
    structure diverges
- Expand `src/newsdom_api/schemas.py` only as far as required to represent the
  preserved data truthfully.

### Layer 2: Sanitized runtime failure handling

- Introduce typed MinerU runtime/output exceptions.
- `src/newsdom_api/mineru_runner.py` should wrap:
  - missing executable failures
  - `subprocess.CalledProcessError`
  - incomplete output artifact cases
- `src/newsdom_api/main.py` should map them to stable sanitized API responses:
  - `503` for runtime/unavailable parser failures
  - `502` for incomplete parser outputs
- Keep private file paths and raw stderr out of public responses.

### Layer 3: Runtime/manual/Kubernetes contract reconciliation

- Align these truth sources with the actual code path:
  - `README.md`
  - `manual/api-reference.md`
  - `docs/operations/deploy-runbook.md`
  - any touched architecture/agent docs when the runtime contract changes
- Document default image behavior, temp-storage expectations, `/health`, and any
  relevant CPU/GPU or multi-arch delivery caveats.
- Add or extend smoke evidence so `/parse` contract drift is harder to miss.

### Layer 4: Local-only OCR evidence and benchmark prerequisites

- Run at least one private PDF through the updated branch.
- Store only redacted durable evidence:
  - page counts
  - block counts
  - success/failure state
  - warning categories
  - sanitized runtime summary if failure remains
- Use that evidence to support the next actions for `#60` and `#63`.

#### 2026-04-23 local-only evidence snapshot

- Input class: single private PDF fixture from
  `/Users/seonghobae/Documents/newsdom-api/tests/copyrighted_fixtures_for_realities`
  (`content_file_3998.pdf`)
- Structural source evidence:
  - page count: 16
  - PDF encryption: yes
- Current-branch local-only parse result:
  - state: failure
  - block count: unavailable because MinerU runtime did not start and no DOM was
    produced
  - warning categories: none observed before failure
  - sanitized runtime summary: `MinerU runtime unavailable`
- Readiness implication:
  - `#60` remains blocked on a host or container environment that actually has
    the MinerU executable available for private-fixture benchmarking
  - `#63` can still use this snapshot as proof that the remaining gap is runtime
    availability rather than additional unredacted output handling

### Layer 5: GitHub topology continuity

- Preserve `#61` as the O1 canonical program anchor.
- Keep `#60`, `#62`, `#63`, `#64` as the active O2 task set.
- Treat open PRs as follows:
  - `#57`: related OCR/runtime follow-up PR; keep milestone and add explicit
    issue linkage if missing
  - `#58`: delivery-governance follow-up; classify as adjacent/non-core
  - `#51`: PDF-dependency follow-up; classify as adjacent and only milestone-link
    if current-code evidence justifies it
- Do not create duplicate PRs for the same branch; use PR continuity before
  opening a new PR.

## Data flow

1. `POST /parse` receives an uploaded PDF.
2. `src/newsdom_api/service.py` writes a sanitized temporary filename.
3. `src/newsdom_api/mineru_runner.py` invokes MinerU and returns structured data
   or raises a typed sanitized exception.
4. `src/newsdom_api/dom_builder.py` constructs a multi-page NewsDOM response from
   `content_list` plus `model`.
5. `src/newsdom_api.main` returns a `ParseResponse` or a stable sanitized HTTP
   error.
6. Local-only private-fixture reruns produce only redacted structural evidence.

## Error handling

- Parser runtime failures must not leak temp paths or raw subprocess details.
- Incomplete MinerU output is a typed backend failure, not a raw file error.
- Page-structure mismatches that still permit normalization belong in
  `ParseQuality.warnings`, not HTTP errors.
- Stale docs that overpromise schema/runtime behavior are acceptance failures.

## Testing strategy

- **TDD layer 1**
  - failing synthetic multi-page regressions in `tests/test_dom_builder.py` and
    `tests/test_service.py`
- **TDD layer 2**
  - failing runner/error-path regressions in `tests/test_mineru_runner_paths.py`
    and parse endpoint tests
- **Docs/runtime alignment**
  - existing docs/manual/governance tests where applicable
  - `uv run mkdocs build --strict`
- **Repository gates**
  - `uv run pytest`
  - `uv run pytest --cov=src/newsdom_api --cov-branch --cov-report=term-missing --cov-fail-under=100`
- **Targeted smokes**
  - parser-related smoke for changed delivery paths
  - local-only private fixture rerun with redacted evidence only

## Decisions

- Prioritize the deterministic `#62` root-cause fix before broader OCR engine or
  environment benchmarking.
- Keep runtime failures explicit and sanitized rather than silent or generic.
- Treat docs/Kubernetes/runtime reconciliation as part of the OCR delivery path,
  not optional cleanup.
- Preserve the existing `#61` hierarchy and repair adjacent PR linkage rather
  than reshaping the issue tree unnecessarily.
