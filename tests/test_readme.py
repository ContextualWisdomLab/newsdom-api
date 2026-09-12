from pathlib import Path


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


def test_central_required_pr_workflows_are_not_duplicated_locally():
    for workflow_name in [
        "dependency-review.yml",
        "quality-gate.yml",
    ]:
        assert not Path(".github/workflows", workflow_name).exists()

    assert Path(".github/workflows/codeql.yml").exists()
    assert Path(".github/workflows/scorecards.yml").exists()

    text = Path("README.md").read_text(encoding="utf-8")
    normalized_text = " ".join(text.split())
    assert "769691526f8c73cf714de8fe8ba51ae6cfa2901a" in text
    assert "`pytest` is the sole repository-local required check" in normalized_text
