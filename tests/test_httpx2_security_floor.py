"""Regression contract for the Starlette TestClient HTTPX2 security floor."""

from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_dev_dependencies_require_fixed_httpx2_family_floor() -> None:
    """Keep the TestClient transport above the currently remediated advisory floors."""

    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"httpx2>=2.12.0"' in pyproject
    assert '"httpcore2>=2.12.0"' in pyproject


def test_lock_resolves_httpx2_family_to_2_12_0() -> None:
    """Keep the generated lock aligned with the declared HTTPX2 security floor."""

    lock = (PROJECT_ROOT / "uv.lock").read_text(encoding="utf-8")

    assert re.search(
        r'\[\[package\]\]\nname = "httpx2"\nversion = "2\.12\.0"',
        lock,
    )
    assert re.search(
        r'\[\[package\]\]\nname = "httpcore2"\nversion = "2\.12\.0"',
        lock,
    )
