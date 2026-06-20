# OCR Accuracy Program Follow-through Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restore page-aware MinerU structure on the fresh `develop` baseline, add sanitized `/parse` runtime failure handling, reconcile runtime/Kubernetes/manual drift, and record redacted local-only OCR evidence while keeping the GitHub OCR issue/PR program coherent.

**Architecture:** First add failing synthetic regressions for the page-collapse root cause and implement the minimal schema/service/builder changes needed to pass them. Then add failing runtime-error regressions that require typed MinerU failure handling and sanitized `502`/`503` API responses, followed by docs/runtime reconciliation, local-only redacted evidence collection, and GitHub issue/PR continuity updates for adjacent follow-up work.

**Tech Stack:** FastAPI, Pydantic, pytest, uv, MinerU CLI, MkDocs, GitHub issues/PRs/milestones

---

### Task 1: Add failing page-aware normalization regressions

**Files:**
- Modify: `tests/test_dom_builder.py`
- Modify: `tests/test_service.py`
- Create: `tests/fixtures/mineru_multi_page_sample.json`
- Create: `tests/fixtures/mineru_multi_page_model.json`

**Step 1: Write the failing test**

Add a new regression in `tests/test_dom_builder.py` that proves:

- `build_dom(...)` emits multiple pages from a synthetic multi-page fixture
- page width/height come from `model[*].page_info`
- `header`, `footer`, and `page_number` stay at page scope
- `chart` blocks remain preserved media
- image/table/chart caption and footnote metadata survive normalization
- blocks with missing `page_idx` create warnings instead of silent wrong
  assignment

Also update `tests/test_service.py` so `parse_pdf_bytes(...)` must pass both
`content_list` and `model` to `build_dom(...)`.

**Step 2: Create the synthetic fixtures**

Create:

- `tests/fixtures/mineru_multi_page_sample.json`
- `tests/fixtures/mineru_multi_page_model.json`

Include exactly enough fixture structure to cover:

- two pages (`0`, `1`)
- header/footer/page-number per page
- image + chart + table metadata with caption/footnote cases
- page-info width/height values

**Step 3: Run test to verify it fails**

Run:

```bash
uv run pytest tests/test_dom_builder.py tests/test_service.py -q
```

Expected: FAIL because the current builder collapses everything into one page
and the current service discards `model`.

**Step 4: Re-run the exact failing cases**

Run:

```bash
uv run pytest tests/test_dom_builder.py::test_build_dom_preserves_multi_page_structure_and_page_scoped_metadata tests/test_service.py::test_parse_pdf_bytes_writes_temp_file_and_builds_dom -q
```

Expected: FAIL for the intended page-aware behavior gap.

**Step 5: Commit**

```bash
git add tests/test_dom_builder.py tests/test_service.py tests/fixtures/mineru_multi_page_sample.json tests/fixtures/mineru_multi_page_model.json
git commit -m "test: add page-aware MinerU regressions"
```

### Task 2: Implement the page-aware `#62` core

**Files:**
- Modify: `src/newsdom_api/dom_builder.py`
- Modify: `src/newsdom_api/service.py`
- Modify: `src/newsdom_api/schemas.py`

**Step 1: Write the minimal implementation**

Update the code so that:

- `build_dom(...)` accepts `model: list[dict[str, Any]] | None = None`
- page indices are derived from `content_list.page_idx` and
  `model[*].page_info.page_no`
- pages are emitted in deterministic sorted order
- page width/height are preserved
- headers, footers, page numbers, and ads remain page-scoped
- chart/image/table caption and footnote metadata are preserved
- `ParseQuality.warnings` is populated for ambiguous page assignment or
  content/model divergence
- `parse_pdf_bytes(...)` forwards `mineru_output.get("model")`

**Step 2: Run test to verify it passes**

Run:

```bash
uv run pytest tests/test_dom_builder.py tests/test_service.py -q
```

Expected: PASS.

**Step 3: Run the broader parser subset**

Run:

```bash
uv run pytest tests/test_dom_builder.py tests/test_service.py tests/test_mineru_runner_paths.py tests/test_parse_endpoint.py tests/test_parse_endpoint_success.py -q
```

Expected: PASS.

**Step 4: Run targeted coverage on touched parser modules**

Run:

```bash
uv run pytest tests/test_dom_builder.py tests/test_service.py tests/test_mineru_runner_paths.py tests/test_parse_endpoint.py tests/test_parse_endpoint_success.py --cov=src/newsdom_api.dom_builder --cov=src/newsdom_api.service --cov=src/newsdom_api.schemas --cov-branch --cov-report=term-missing
```

Expected: PASS with strong signal for the touched parser modules.

**Step 5: Commit**

```bash
git add src/newsdom_api/dom_builder.py src/newsdom_api/service.py src/newsdom_api/schemas.py
git commit -m "feat: preserve multi-page MinerU structure in NewsDOM"
```

### Task 3: Add failing runtime-safe `/parse` regressions

**Files:**
- Modify: `tests/test_mineru_runner_paths.py`
- Modify: `tests/test_parse_endpoint.py`
- Modify: `tests/test_parse_endpoint_success.py`

**Step 1: Write the failing runner tests**

Extend `tests/test_mineru_runner_paths.py` so it requires:

- `run_mineru(...)` wraps `CalledProcessError` in a typed sanitized runtime
  exception
- missing executable failures are wrapped in the same runtime-unavailable class
- missing `ocr/`, `*_content_list.json`, or `*_model.json` become a typed
  incomplete-output exception
- runtime exceptions retain internal debug metadata (`returncode`, `stdout`,
  `stderr`) without exposing unsafe public strings

**Step 2: Write the failing API tests**

Extend parse endpoint tests so `/parse` returns:

- `503` with sanitized detail when MinerU is unavailable or crashes
- `502` with sanitized detail when MinerU outputs are incomplete

Also assert that temp directories and private-looking paths are absent from the
public detail string.

**Step 3: Run test to verify it fails**

Run:

```bash
uv run pytest tests/test_mineru_runner_paths.py tests/test_parse_endpoint.py tests/test_parse_endpoint_success.py -q
```

Expected: FAIL because the current code still raises raw subprocess/file
exceptions.

**Step 4: Re-run the exact new failures**

Run:

```bash
uv run pytest tests/test_mineru_runner_paths.py::test_run_mineru_wraps_called_process_error tests/test_parse_endpoint.py::test_parse_endpoint_returns_503_for_mineru_runtime_failure tests/test_parse_endpoint.py::test_parse_endpoint_returns_502_for_incomplete_mineru_output -q
```

Expected: FAIL for the intended runtime translation gap.

**Step 5: Commit**

```bash
git add tests/test_mineru_runner_paths.py tests/test_parse_endpoint.py tests/test_parse_endpoint_success.py
git commit -m "test: add MinerU runtime failure regressions"
```

### Task 4: Implement typed MinerU runtime/output errors and API mapping

**Files:**
- Create: `src/newsdom_api/errors.py`
- Modify: `src/newsdom_api/mineru_runner.py`
- Modify: `src/newsdom_api/main.py`
- Modify: `src/newsdom_api/service.py`
- Modify: `ARCHITECTURE.md`

**Step 1: Write the minimal implementation**

Create explicit exception types for:

- runtime/unavailable MinerU execution failure
- incomplete MinerU output artifacts

**Step 2: Update runner and endpoint wiring**

Change `src/newsdom_api/mineru_runner.py` so it:

- wraps `CalledProcessError` and missing executable failures in the runtime
  exception
- raises the incomplete-output exception when required MinerU artifacts are
  absent
- avoids path-bearing public exception strings

Change `src/newsdom_api/main.py` so `/parse` maps exceptions to:

- `503 Service Unavailable`
- `502 Bad Gateway`

Keep `src/newsdom_api/service.py` changes minimal and focused on exception flow
only if required.

Update `ARCHITECTURE.md` to document page-aware normalization plus typed runtime
failure handling.

**Step 3: Run test to verify it passes**

Run:

```bash
uv run pytest tests/test_mineru_runner_paths.py tests/test_parse_endpoint.py tests/test_parse_endpoint_success.py -q
```

Expected: PASS.

**Step 4: Run the parser regression subset again**

Run:

```bash
uv run pytest tests/test_dom_builder.py tests/test_service.py tests/test_mineru_runner_paths.py tests/test_parse_endpoint.py tests/test_parse_endpoint_success.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/newsdom_api/errors.py src/newsdom_api/mineru_runner.py src/newsdom_api/main.py src/newsdom_api/service.py ARCHITECTURE.md
git commit -m "fix: sanitize MinerU runtime failures"
```

### Task 5: Reconcile runtime/manual/Kubernetes contract drift

**Files:**
- Modify: `README.md`
- Modify: `manual/api-reference.md`
- Modify: `docs/operations/deploy-runbook.md`
- Modify: `AGENTS.md` (only if canonical execution guidance materially changes)
- Modify: `ARCHITECTURE.md` (if needed beyond Task 4)

**Step 1: Write the failing documentation expectations**

Add or extend the narrowest existing doc/manual/governance tests so they require
the docs to match the actual runtime contract:

- default image includes MinerU runtime path
- `/parse` failure semantics are described honestly
- temp-file handling and `/health` expectations are current
- Kubernetes/runtime considerations match the current delivery path

**Step 2: Run test to verify it fails**

Run the smallest relevant existing test file(s) for the changed docs.

Expected: FAIL until stale wording is removed.

**Step 3: Write the minimal doc updates**

Align all touched docs with the actual code and delivery contract.

**Step 4: Run docs verification**

Run:

```bash
uv run mkdocs build --strict
```

Expected: PASS.

**Step 5: Commit**

```bash
git add README.md manual/api-reference.md docs/operations/deploy-runbook.md AGENTS.md ARCHITECTURE.md
git commit -m "docs: align OCR runtime contract"
```

### Task 6: Record redacted local-only OCR evidence

**Files:**
- Modify: `docs/plans/2026-04-23-ocr-accuracy-program-followthrough-design.md`
- Modify: `docs/plans/2026-04-23-ocr-accuracy-program-followthrough.md`
- Modify: issue/PR comments only when durable blocker evidence is required

**Step 1: Run a local-only private-fixture check**

Use one PDF from `/Users/seonghobae/Documents/newsdom-api/tests/copyrighted_fixtures_for_realities` and capture only:

- page count
- block count
- success/failure state
- warning categories
- sanitized runtime summary

Do not store raw OCR output or extracted text in the repo.

**Step 2: Record only redacted durable evidence**

Append the redacted evidence summary to the plan/design docs or another durable
repo doc using counts/categories only.

Recorded 2026-04-23 local-only evidence:

- input fixture: `content_file_3998.pdf`
- page count: 16
- block count: unavailable because the parser did not produce a DOM
- success/failure state: failure
- warning categories: none observed before failure
- sanitized runtime summary: `MinerU runtime unavailable`

**Step 3: Re-check follow-up issue readiness**

Re-evaluate `#60`, `#63`, and `#64` against the new evidence and current code.
If external blockers remain, record them in issue/PR comments with sanitized
evidence.

Current local-only readiness readout:

- `#60`: still externally blocked for real-document benchmarking until a local or
  container runtime with the MinerU executable is available
- `#63`: runtime-sanitization work remains evidenced as correct for the observed
  failure path because the branch surfaced only `MinerU runtime unavailable`
- `#64`: no new docs blocker from this snapshot; the remaining blocker is runtime
  availability, not public-contract wording

**Step 4: Commit**

```bash
git add docs/plans/2026-04-23-ocr-accuracy-program-followthrough-design.md docs/plans/2026-04-23-ocr-accuracy-program-followthrough.md
git commit -m "docs: record redacted OCR follow-through evidence"
```

### Task 7: Repair GitHub issue/PR continuity and follow-up wiring

**Files:**
- Modify: GitHub issue/PR metadata and comments only

**Step 1: Re-check live GitHub state**

Verify:

- `#61` sub-issue tree remains intact
- milestone membership for `#60-#64`
- open PRs `#57`, `#58`, `#51` for missing milestone or issue linkage
- current branch PR continuity before creating a new PR

**Step 2: Apply the minimal metadata fixes**

Examples:

- add/update issue references in related PR bodies/comments
- attach milestone when current-code evidence justifies it
- create only genuinely missing follow-up/blocker issues, rooted under `#61`
- keep adjacent non-core PRs as related follow-ups, not duplicates

**Step 3: Draft or update the canonical PR**

Create a draft PR for this branch if none exists, using the issue program as the
summary spine. Ensure the PR body references `#61` and the exact implemented
issue(s).

**Step 4: Re-check continuity after creation/update**

Run PR continuity again and confirm there is one canonical PR for the branch.

**Step 5: Commit**

No git commit for metadata-only GitHub changes.

### Task 8: Run full acceptance verification and continue delivery

**Files:**
- Modify: only files required by verification feedback

**Step 1: Run the full test suite**

Run:

```bash
uv run pytest
```

Expected: PASS.

**Step 2: Run the repository coverage gate**

Run:

```bash
uv run pytest --cov=src/newsdom_api --cov-branch --cov-report=term-missing --cov-fail-under=100
```

Expected: PASS with 100% coverage.

**Step 3: Re-run docs build if public docs changed**

Run:

```bash
uv run mkdocs build --strict
```

Expected: PASS.

**Step 4: Run targeted delivery smoke checks**

Run the applicable smokes for changed parser/delivery paths, for example:

```bash
uv run python fuzzers/dom_builder_fuzzer.py --smoke tests/fixtures/mineru_sample.json
```

Add container/runtime smokes if those paths changed.

**Step 5: Continue PR/merge/deploy follow-through**

After fresh verification, continue through:

- pushing the branch
- draft PR → ready-for-review transition when evidence is complete
- robot-review evidence collection
- merge path execution when checks and current-head review evidence allow it
- deploy/release verification or durable blocker capture
- follow-up issue execution if a separate adjacent task becomes the next highest
  executable item

**Step 6: Commit verification-driven fixes**

```bash
git add <only-the-files-required-by-verification-feedback>
git commit -m "fix: address OCR follow-through verification feedback"
```
