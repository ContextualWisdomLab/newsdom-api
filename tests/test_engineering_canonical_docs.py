from pathlib import Path

REQUIRED_CANONICAL_DOCS = [
    "AGENTS.md",
    "ARCHITECTURE.md",
    "docs/PRD.md",
    "docs/TRD.md",
    "docs/UML.md",
    "docs/ERD.md",
    "docs/THREAT_MODEL.md",
    "docs/TEST_STRATEGY.md",
    "docs/OPERABILITY.md",
    "docs/TRACEABILITY.md",
    "docs/adr/README.md",
    "docs/adr/0002-external-parser-and-liveness.md",
    "docs/adr/0003-authentication-before-body-and-readiness.md",
    "docs/adr/0004-process-local-parser-admission.md",
    "docs/adr/0005-durable-async-jobs-and-idempotency.md",
    "docs/agents/README.md",
    "docs/coderabbit/review-commands.md",
    "docs/engineering/acceptance-criteria.md",
    "docs/engineering/canonical-docs.md",
    "docs/engineering/execution-policy.md",
    "docs/engineering/harness-engineering.md",
    "docs/engineering/review-policy.md",
    "docs/engineering/runtime-data-policy.md",
    "docs/engineering/skills-subagents-mcp.md",
    "docs/operations/deploy-runbook.md",
    "docs/security/api-security-checklist.md",
    "docs/workflow/git-flow.md",
    "docs/workflow/one-day-delivery-plan.md",
    "docs/workflow/pr-continuity.md",
]


def _read(path: str) -> str:
    """Return one canonical repository document as UTF-8 text."""

    return Path(path).read_text(encoding="utf-8")


def _traceability_row(marker: str) -> str:
    """Return the Markdown traceability row containing ``marker``."""

    for line in _read("docs/TRACEABILITY.md").splitlines():
        if line.startswith("|") and marker in line:
            return line
    raise AssertionError(f"missing traceability row containing {marker!r}")


def test_repository_ships_engineering_canonical_docs() -> None:
    missing = [path for path in REQUIRED_CANONICAL_DOCS if not Path(path).exists()]
    assert not missing, f"missing canonical engineering docs: {missing}"


def test_repo_local_agents_doc_points_to_authoritative_sources() -> None:
    text = _read("AGENTS.md")
    for expected in (
        "docs/engineering/canonical-docs.md",
        "docs/engineering/execution-policy.md",
        "docs/engineering/acceptance-criteria.md",
        "docs/workflow/git-flow.md",
        "docs/workflow/pr-continuity.md",
        "docs/operations/deploy-runbook.md",
    ):
        assert expected in text


def test_architecture_doc_describes_runtime_modules() -> None:
    text = _read("ARCHITECTURE.md")
    for expected in (
        "src/newsdom_api/main.py",
        "src/newsdom_api/service.py",
        "src/newsdom_api/mineru_runner.py",
        "src/newsdom_api/dom_builder.py",
        "tests/fixtures",
    ):
        assert expected in text


def test_canonical_docs_index_maps_existing_truth_sources() -> None:
    text = _read("docs/engineering/canonical-docs.md")
    for expected in (
        "README.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CHANGELOG.md",
        "docs/PRD.md",
        "docs/TRD.md",
        "docs/UML.md",
        "docs/ERD.md",
        "docs/THREAT_MODEL.md",
        "docs/TEST_STRATEGY.md",
        "docs/OPERABILITY.md",
        "docs/TRACEABILITY.md",
        "docs/adr/README.md",
        "docs/agents/README.md",
        "docs/coderabbit/review-commands.md",
        "docs/security/api-security-checklist.md",
        "docs/workflow/git-flow.md",
        "manual/index.md",
        "docs/plans/",
    ):
        assert expected in text
        assert Path(expected).exists(), f"canonical truth source missing: {expected}"


def test_product_docs_keep_liveness_weaker_than_readiness() -> None:
    """Prevent `/health` from becoming a false parser-readiness claim."""

    prd = _read("docs/PRD.md")
    trd = _read("docs/TRD.md")
    uml = _read("docs/UML.md")
    adr = _read("docs/adr/0002-external-parser-and-liveness.md")
    assert "/health" in prd and "liveness" in prd
    assert "must not represent `/health` as parser traffic readiness" in trd
    assert "/health — protected-develop liveness" in uml
    assert "`/health` means process liveness only" in adr


def test_active_auth_and_admission_work_is_not_promoted() -> None:
    """Keep PR #539/#548 as active work until protected integration."""

    prd = _read("docs/PRD.md")
    canonical = _read("docs/engineering/canonical-docs.md")
    auth_row = _traceability_row("fail-closed production auth before body allocation")
    admission_row = _traceability_row("non-waiting process-local parser admission")
    assert "PR #539 — active-PR" in prd
    assert "PR #548 — active-PR and stacked" in prd
    assert auth_row.rstrip().endswith("| active-PR |")
    assert "#539" in auth_row
    assert admission_row.rstrip().endswith("| active-PR-stacked |")
    assert "#548" in admission_row
    assert "PR #539 authentication/readiness and PR #548 process-local parser admission remain active-PR" in canonical


def test_erd_does_not_invent_current_durable_newsdom_database() -> None:
    """Keep durable job persistence labelled as accepted target only."""

    erd = _read("docs/ERD.md")
    trd = _read("docs/TRD.md")
    durable_row = _traceability_row("durable async parse lifecycle")
    assert "does **not** own durable parse-job" in erd
    assert "Accepted-target durable job model — not implemented" in erd
    assert "Current protected runtime owns no application database" in trd
    assert durable_row.rstrip().endswith("| accepted-target |")


def test_adr_index_preserves_current_and_proposed_decisions() -> None:
    """Require runtime and future-job decisions to remain indexed with maturity."""

    index = _read("docs/adr/README.md")
    for expected in (
        "0002-external-parser-and-liveness.md",
        "0003-authentication-before-body-and-readiness.md",
        "0004-process-local-parser-admission.md",
        "0005-durable-async-jobs-and-idempotency.md",
        "Proposed — PR #539",
        "Proposed — PR #548",
        "Proposed target",
    ):
        assert expected in index
    assert "**Status:** Accepted" in _read("docs/adr/0002-external-parser-and-liveness.md")
    assert "**Status:** Proposed" in _read("docs/adr/0003-authentication-before-body-and-readiness.md")
    assert "**Status:** Proposed" in _read("docs/adr/0004-process-local-parser-admission.md")
    assert "**Status:** Proposed" in _read("docs/adr/0005-durable-async-jobs-and-idempotency.md")


def test_runtime_data_policy_protects_private_inputs() -> None:
    text = _read("docs/engineering/runtime-data-policy.md")
    for expected in (
        "synthetic fixtures",
        "private reference",
        "tmp/",
        "logs",
        "do not commit secrets",
    ):
        assert expected in text


def test_review_policy_covers_review_expectations() -> None:
    text = _read("docs/engineering/review-policy.md").lower()
    for expected in (
        "human review",
        "coderabbit",
        "required checks",
        "resolve review comments",
        "stale-review dismissal",
    ):
        assert expected in text


def test_review_policy_documents_single_maintainer_exception() -> None:
    text = _read("docs/engineering/review-policy.md").lower()
    for expected in (
        "single-maintainer",
        "reviewer capacity",
        "required checks",
        "re-tighten",
    ):
        assert expected in text


def test_api_security_checklist_scopes_live_endpoints() -> None:
    text = _read("docs/security/api-security-checklist.md")
    for expected in (
        "/health",
        "/docs",
        "/redoc",
        "/parse",
        "content-type",
        "synthetic fixtures",
    ):
        assert expected in text.lower()


def test_contributing_maps_new_canonical_docs() -> None:
    text = _read("CONTRIBUTING.md")
    for expected in (
        "manual/",
        "docs/agents/README.md",
        "docs/coderabbit/review-commands.md",
    ):
        assert expected in text


def test_deploy_runbook_matches_release_trigger_and_assets() -> None:
    runbook_text = _read("docs/operations/deploy-runbook.md")
    release_workflow = _read(".github/workflows/release.yml")

    assert "push:" in release_workflow and "tags:" in release_workflow
    assert "workflow_dispatch:" in release_workflow
    assert "tag push" in runbook_text.lower()
    assert "manual dispatch" in runbook_text.lower()
    assert "release pr lands on `main`" not in runbook_text.lower()
    for expected in ("SHA256SUMS.txt", "release-manifest.json", "*.intoto.jsonl"):
        assert expected in runbook_text


def test_deploy_runbook_describes_current_runtime_and_probe_contract() -> None:
    text = _read("docs/operations/deploy-runbook.md")

    for expected in (
        "default image ships the API service only",
        "does not bundle the MinerU runtime",
        "`NEWSDOM_MINERU_BIN`",
        "`/health` proves the API process is serving but does not validate a full `/parse` round-trip",
        "no in-tree Kubernetes manifests",
    ):
        assert expected in text
