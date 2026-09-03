"""Regression contracts for test-owned global state restoration."""

from __future__ import annotations

import ast
from pathlib import Path


_PARSE_ENDPOINT_TEST = Path(__file__).with_name("test_parse_endpoint.py")


def test_parse_endpoint_test_never_clears_all_dependency_overrides() -> None:
    """A focused test must not erase dependency overrides installed by other fixtures."""

    source = _PARSE_ENDPOINT_TEST.read_text(encoding="utf-8")
    tree = ast.parse(source)

    destructive_clear_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "clear"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "dependency_overrides"
    ]

    assert destructive_clear_calls == []
