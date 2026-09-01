"""Regression tests for explanatory docstrings in shipped Python modules."""

from __future__ import annotations

import ast
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_MODULE = REPOSITORY_ROOT / "src" / "newsdom_api" / "synthetic.py"


def _single_line_docstring_owners(source_text: str) -> list[str]:
    """Collect definitions whose docstrings contain no explanatory second line.

    The quality contract intentionally treats a syntactically valid one-line
    docstring as insufficient documentation for shipped production behavior.
    """

    syntax_tree = ast.parse(source_text)
    offenders: list[str] = []

    module_docstring = ast.get_docstring(syntax_tree, clean=False)
    if module_docstring is None or "\n" not in module_docstring.strip("\n"):
        offenders.append("<module>")

    for node in ast.walk(syntax_tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        docstring = ast.get_docstring(node, clean=False)
        if docstring is None or "\n" not in docstring.strip("\n"):
            offenders.append(node.name)

    return sorted(offenders)


def test_synthetic_fixture_module_has_explanatory_docstrings() -> None:
    """Reject missing or single-line docstrings in the shipped fixture builder.

    Keeping the rule executable prevents a nominal 100% docstring-presence
    score from passing terse documentation that does not explain responsibility.
    """

    source_text = SYNTHETIC_MODULE.read_text(encoding="utf-8")

    assert _single_line_docstring_owners(source_text) == []
