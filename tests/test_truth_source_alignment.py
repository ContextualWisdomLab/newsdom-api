from __future__ import annotations

import ast
import re
from pathlib import Path

import yaml

STALE_ISSUE_REFS = (re.compile(r"(?<!\d)#8(?!\d)"), re.compile(r"(?<!\d)#10(?!\d)"))


def _integration_marked_test_exists() -> bool:
    current_file = Path(__file__).resolve()
    for test_path in Path("tests").rglob("test_*.py"):
        if test_path.resolve() == current_file:
            continue
        text = test_path.read_text(encoding="utf-8")
        if _contains_integration_marker(text):
            return True
    return False


def _contains_stale_issue_reference(text: str) -> bool:
    return any(pattern.search(text) for pattern in STALE_ISSUE_REFS)


def _contains_integration_marker(text: str) -> bool:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False

    for node in tree.body:
        if _node_has_integration_marker(node):
            return True
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "pytestmark"
                for target in node.targets
            ):
                if _expr_contains_integration_mark(node.value):
                    return True
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "pytestmark":
                if node.value is not None and _expr_contains_integration_mark(
                    node.value
                ):
                    return True
    return False


def _node_has_integration_marker(node: ast.AST) -> bool:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if any(
            _is_integration_mark_expr(decorator) for decorator in node.decorator_list
        ):
            return True

    if isinstance(node, ast.ClassDef):
        return any(_node_has_integration_marker(child) for child in node.body)

    return False


def _expr_contains_integration_mark(node: ast.AST) -> bool:
    if _is_integration_mark_expr(node):
        return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return any(_expr_contains_integration_mark(element) for element in node.elts)
    return False


def _is_integration_mark_expr(node: ast.AST) -> bool:
    if isinstance(node, ast.Call):
        node = node.func
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "integration"
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "mark"
        and isinstance(node.value.value, ast.Name)
        and node.value.value.id == "pytest"
    )


def test_integration_marker_detector_accepts_list_style_pytestmark(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "test_list_style.py"
    candidate.write_text(
        "import pytest\n\npytestmark = [pytest.mark.integration]\n",
        encoding="utf-8",
    )

    assert _contains_integration_marker(candidate.read_text(encoding="utf-8"))


def test_integration_marker_detector_scans_nested_tests(
    monkeypatch, tmp_path: Path
) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    candidate = nested / Path(__file__).name
    candidate.write_text(
        "import pytest\n\npytestmark = [pytest.mark.integration]\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(Path, "rglob", lambda self, pattern: [candidate])

    assert _integration_marked_test_exists()


def test_integration_marker_detector_ignores_function_local_pytestmark(
    monkeypatch, tmp_path: Path
) -> None:
    candidate = tmp_path / "test_local_scope.py"
    candidate.write_text(
        "def helper():\n"
        "    pytestmark = [pytest.mark.integration]\n"
        "    return pytestmark\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(Path, "rglob", lambda self, pattern: [candidate])

    assert not _integration_marked_test_exists()


def test_integration_marker_detector_ignores_string_literal_matches(
    monkeypatch, tmp_path: Path
) -> None:
    candidate = tmp_path / "test_literal_only.py"
    candidate.write_text(
        'EXAMPLE = """\n@pytest.mark.integration\nDocumented here only.\n"""\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(Path, "rglob", lambda self, pattern: [candidate])

    assert not _integration_marked_test_exists()


def test_integration_marker_detector_finds_class_method_marks() -> None:
    text = (
        "import pytest\n\n"
        "class TestExample:\n"
        "    @pytest.mark.integration\n"
        "    def test_live(self):\n"
        "        assert True\n"
    )

    assert _contains_integration_marker(text)


def test_installation_manual_does_not_reference_empty_integration_marker() -> None:
    text = Path("manual/installation.md").read_text(encoding="utf-8")
    mentions_marker = (
        'pytest -m "integration"' in text or "pytest -m integration" in text
    )
    assert not mentions_marker or _integration_marked_test_exists()


def test_gh_pages_workflow_targets_supported_branches_only() -> None:
    workflow = yaml.safe_load(
        Path(".github/workflows/gh-pages.yml").read_text(encoding="utf-8")
    )
    triggers = workflow.get("on", workflow.get(True))
    branches = triggers["push"]["branches"]
    assert set(branches) == {"main", "develop"}


def test_adr_follow_up_drops_stale_issue_references() -> None:
    text = Path("docs/adr/0001-openssf-best-practices-badge.md").read_text(
        encoding="utf-8"
    )
    assert not _contains_stale_issue_reference(text)


def test_stale_issue_reference_detector_ignores_longer_issue_numbers() -> None:
    assert not _contains_stale_issue_reference(
        "Superseded by #100 and issue #101 in a later release plan."
    )


def test_main_stable_sync_plan_stays_tool_neutral() -> None:
    text = Path("docs/plans/2026-04-10-main-stable-sync.md").read_text(encoding="utf-8")
    assert "For Claude:" not in text
    assert "superpowers:executing-plans" not in text
