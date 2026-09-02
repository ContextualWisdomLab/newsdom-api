from pathlib import Path

CENTRAL_DEPENDENCY_REVIEW_WORKFLOW_SHA = "0bcd22d8bb07650aafb0a8f116e4c2bbb8744f03"


def test_readme_points_to_user_and_maintainer_docs():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "fixtures and provenance" in text.lower()
    assert "contributing.md" in text.lower()
    assert "docs/workflow/git-flow.md" in text


def test_readme_includes_scorecard_badge():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "securityscorecards.dev" in text


def test_contributing_mentions_develop_branch():
    text = Path("CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "develop" in text


def test_readme_uses_uv_sync_for_repo_setup():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "uv sync --frozen --all-extras" in text
    assert 'pip install -e ".[dev]"' not in text
    assert "python3.10 -m venv .venv" not in text


def test_contributing_uses_uv_sync_for_repo_setup():
    text = Path("CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "uv sync --frozen --all-extras" in text
    assert 'pip install -e ".[dev]"' not in text


def test_readme_documents_uv_run_entrypoints():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "uv run uvicorn --app-dir src newsdom_api.main:app --reload" in text
    assert "uv run pytest" in text
    assert (
        "uv run python fuzzers/dom_builder_fuzzer.py --smoke tests/fixtures/mineru_sample.json"
        in text
    )


def test_readme_parse_examples_export_and_send_bearer_token():
    text = Path("README.md").read_text(encoding="utf-8")

    assert 'export NEWSDOM_API_TOKEN="$(openssl rand -hex 32)"' in text
    assert text.count('-H "Authorization: Bearer $NEWSDOM_API_TOKEN"') >= 3


def test_repo_docs_note_windows_uv_python_path_equivalent():
    for path in [Path("README.md"), Path("CONTRIBUTING.md")]:
        text = path.read_text(encoding="utf-8")
        assert ".venv\\Scripts\\python.exe" in text, path


def test_pull_request_template_exists():
    assert Path(".github/pull_request_template.md").exists()


def test_security_workflows_exist():
    assert Path(".github/workflows/scorecards.yml").exists()
    assert Path(".github/workflows/codeql.yml").exists()
    assert Path(".github/workflows/dependency-review.yml").exists()


def test_dependency_review_uses_immutable_central_workflow():
    workflow = Path(".github/workflows/dependency-review.yml").read_text(encoding="utf-8")
    expected = (
        "ContextualWisdomLab/.github/.github/workflows/dependency-review.yml@"
        f"{CENTRAL_DEPENDENCY_REVIEW_WORKFLOW_SHA}"
    )

    assert expected in workflow
    assert "dependency-review.yml@main" not in workflow
    assert "fail_on_severity: low" in workflow
    assert 'allow_ghsas: "GHSA-69w3-r845-3855"' in workflow


def test_quality_gate_workflow_exists():
    assert Path(".github/workflows/quality-gate.yml").exists()
