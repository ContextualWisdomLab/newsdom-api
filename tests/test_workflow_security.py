import re
from pathlib import Path

import yaml

PINNED_ACTION_RE = re.compile(r"(?:-\s+)?uses:\s+[\w./-]+@[0-9a-f]{40}")


def _iter_workflow_paths(workflow_dir: Path | None = None) -> list[Path]:
    workflow_dir = workflow_dir or Path(".github/workflows")
    return sorted([*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")])


def _is_pinned_action_line(line: str) -> bool:
    candidate = line.split("#", 1)[0].rstrip()
    if candidate.startswith("uses: ./") or candidate.startswith("- uses: ./"):
        return True
    return bool(PINNED_ACTION_RE.fullmatch(candidate))


def _has_pull_request_branch_filter(text: str) -> bool:
    in_pull_request = False
    pull_request_indent = None

    for line in text.splitlines():
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        if stripped.startswith("pull_request:"):
            in_pull_request = True
            pull_request_indent = indent
            continue

        if in_pull_request:
            if stripped and indent <= (pull_request_indent or 0):
                in_pull_request = False
                pull_request_indent = None
                continue

            if stripped.startswith("branches:") or stripped.startswith(
                "branches-ignore:"
            ):
                return True

    return False


def test_workflow_actions_are_pinned_by_sha():
    for workflow_path in _iter_workflow_paths():
        text = workflow_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("uses:") or stripped.startswith("- uses:"):
                assert _is_pinned_action_line(stripped), (
                    f"unpinned action in {workflow_path}: {stripped}"
                )


def test_ci_workflows_do_not_use_pip_install_commands():
    for workflow_name in ["tests.yml", "quality-gate.yml"]:
        text = Path(f".github/workflows/{workflow_name}").read_text(encoding="utf-8")
        assert not re.search(r"\b(?:python\s+-m\s+)?pip3?\s+install\b", text)


def test_ci_workflows_run_pytest_through_uv():
    tests_text = Path(".github/workflows/tests.yml").read_text(encoding="utf-8")
    quality_text = Path(".github/workflows/quality-gate.yml").read_text(
        encoding="utf-8"
    )
    assert "uv run pytest" in tests_text
    assert (
        "uv run pytest --cov=src/newsdom_api --cov-branch --cov-report=term-missing --cov-fail-under=100"
        in quality_text
    )


def test_uv_lock_exists_for_ci_reproducibility():
    assert Path("uv.lock").exists()


def test_coverage_config_enables_branch_coverage():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "branch = true" in text


def test_ci_workflows_run_for_all_pull_requests():
    for workflow_path in _iter_workflow_paths():
        text = workflow_path.read_text(encoding="utf-8")
        assert not _has_pull_request_branch_filter(text), (
            f"pull_request branch filter blocks stacked PR checks in {workflow_path}"
        )


def test_docs_workflow_uses_least_privilege_pages_permissions():
    text = Path(".github/workflows/gh-pages.yml").read_text(encoding="utf-8")
    assert "contents: write" not in text
    assert "pages: write" in text
    assert "id-token: write" in text


def test_codeql_workflow_scopes_security_events_write_to_job_level():
    text = Path(".github/workflows/codeql.yml").read_text(encoding="utf-8")
    assert "actions: read" in text.split("jobs:", 1)[0]
    assert "contents: read" in text.split("jobs:", 1)[0]
    assert "security-events: write" not in text.split("jobs:", 1)[0]
    assert "security-events: write" in text.split("jobs:", 1)[1]


def test_docs_workflow_installs_docs_tooling_from_locked_uv_dependencies():
    text = Path(".github/workflows/gh-pages.yml").read_text(encoding="utf-8")
    assert not re.search(r"\b(?:python\s+-m\s+)?pip3?\s+install\b", text)
    assert "astral-sh/setup-uv@" in text
    assert "uv sync --frozen --extra docs" in text
    assert "uv run mkdocs build --strict" in text


def test_docs_workflow_uses_pages_artifact_deploy_path():
    text = Path(".github/workflows/gh-pages.yml").read_text(encoding="utf-8")
    assert "mkdocs gh-deploy" not in text
    assert "./.github/actions/upload-pages-artifact" in text
    assert "actions/upload-pages-artifact@" not in text
    assert "actions/deploy-pages@" in text


def test_local_pages_artifact_action_uses_node24_upload_artifact():
    text = Path(".github/actions/upload-pages-artifact/action.yml").read_text(
        encoding="utf-8"
    )
    assert "actions/upload-artifact@bbbca2ddaa5d8feaa63e36b76fdaad77386f024f" in text


def test_quality_gate_workflow_pins_uv_version():
    text = Path(".github/workflows/quality-gate.yml").read_text(encoding="utf-8")
    assert "astral-sh/setup-uv@" in text
    assert "version: '0.11.3'" in text


def test_tests_workflow_pins_uv_version():
    text = Path(".github/workflows/tests.yml").read_text(encoding="utf-8")
    assert "astral-sh/setup-uv@" in text
    assert "version: '0.11.3'" in text


def test_docs_workflow_paths_cover_lockfile_and_local_action_inputs():
    workflow = yaml.safe_load(
        Path(".github/workflows/gh-pages.yml").read_text(encoding="utf-8")
    )
    triggers = workflow.get("on", workflow.get(True))
    paths = triggers["push"].get("paths")

    assert paths is not None, "gh-pages push.paths must remain configured"
    assert "pyproject.toml" in paths
    assert "uv.lock" in paths
    assert ".github/actions/upload-pages-artifact/**" in paths


def test_iter_workflow_paths_includes_yaml_extension(tmp_path: Path):
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "alpha.yml").write_text("name: alpha\n", encoding="utf-8")
    (workflow_dir / "beta.yaml").write_text("name: beta\n", encoding="utf-8")

    assert [path.name for path in _iter_workflow_paths(workflow_dir)] == [
        "alpha.yml",
        "beta.yaml",
    ]


def test_is_pinned_action_line_rejects_sha_only_in_comment():
    assert not _is_pinned_action_line(
        "- uses: actions/checkout@v4 # 34e114876b0b11c390a56381ad16ebd13914f8d5"
    )
