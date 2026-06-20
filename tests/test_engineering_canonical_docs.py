from pathlib import Path

REQUIRED_CANONICAL_DOCS = [
    "AGENTS.md",
    "ARCHITECTURE.md",
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


def test_repository_ships_engineering_canonical_docs() -> None:
    missing = [path for path in REQUIRED_CANONICAL_DOCS if not Path(path).exists()]
    assert not missing, f"missing canonical engineering docs: {missing}"


def test_repo_local_agents_doc_points_to_authoritative_sources() -> None:
    text = Path("AGENTS.md").read_text(encoding="utf-8")
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
    text = Path("ARCHITECTURE.md").read_text(encoding="utf-8")
    for expected in (
        "src/newsdom_api/main.py",
        "src/newsdom_api/service.py",
        "src/newsdom_api/mineru_runner.py",
        "src/newsdom_api/dom_builder.py",
        "tests/fixtures",
    ):
        assert expected in text


def test_canonical_docs_index_maps_existing_truth_sources() -> None:
    text = Path("docs/engineering/canonical-docs.md").read_text(encoding="utf-8")
    for expected in (
        "README.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CHANGELOG.md",
        "docs/agents/README.md",
        "docs/coderabbit/review-commands.md",
        "docs/security/api-security-checklist.md",
        "docs/workflow/git-flow.md",
        "manual/index.md",
        "docs/plans/",
    ):
        assert expected in text
        assert Path(expected).exists(), f"canonical truth source missing: {expected}"


def test_runtime_data_policy_protects_private_inputs() -> None:
    text = Path("docs/engineering/runtime-data-policy.md").read_text(encoding="utf-8")
    for expected in (
        "synthetic fixtures",
        "private reference",
        "tmp/",
        "logs",
        "do not commit secrets",
    ):
        assert expected in text


def test_review_policy_covers_review_expectations() -> None:
    text = Path("docs/engineering/review-policy.md").read_text(encoding="utf-8").lower()
    for expected in (
        "human review",
        "coderabbit",
        "required checks",
        "resolve review comments",
        "stale-review dismissal",
    ):
        assert expected in text


def test_review_policy_documents_single_maintainer_exception() -> None:
    text = Path("docs/engineering/review-policy.md").read_text(encoding="utf-8").lower()
    for expected in (
        "single-maintainer",
        "reviewer capacity",
        "required checks",
        "re-tighten",
    ):
        assert expected in text


def test_api_security_checklist_scopes_live_endpoints() -> None:
    text = Path("docs/security/api-security-checklist.md").read_text(encoding="utf-8")
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
    text = Path("CONTRIBUTING.md").read_text(encoding="utf-8")
    for expected in (
        "manual/",
        "docs/agents/README.md",
        "docs/coderabbit/review-commands.md",
    ):
        assert expected in text


def test_deploy_runbook_matches_release_trigger_and_assets() -> None:
    runbook_text = Path("docs/operations/deploy-runbook.md").read_text(encoding="utf-8")
    release_workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "push:" in release_workflow and "tags:" in release_workflow
    assert "workflow_dispatch:" in release_workflow
    assert "tag push" in runbook_text.lower()
    assert "manual dispatch" in runbook_text.lower()
    assert "release pr lands on `main`" not in runbook_text.lower()
    for expected in ("SHA256SUMS.txt", "release-manifest.json", "*.intoto.jsonl"):
        assert expected in runbook_text


def test_deploy_runbook_describes_current_runtime_and_probe_contract() -> None:
    text = Path("docs/operations/deploy-runbook.md").read_text(encoding="utf-8")

    for expected in (
        "default image already includes the MinerU runtime",
        "`NEWSDOM_MINERU_BIN=mineru`",
        "`/health` proves the API process is serving but does not validate a full `/parse` round-trip",
        "no in-tree Kubernetes manifests",
    ):
        assert expected in text
