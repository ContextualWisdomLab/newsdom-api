"""Regression contract for the Starlette TestClient dependency security floors."""

from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_dependencies_require_fixed_transport_floors() -> None:
    """Keep async and TestClient transports above current advisory floors."""

    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"anyio>=4.14.2,<4.15"' in pyproject
    assert '"httpx2>=2.12.0"' in pyproject
    assert '"httpcore2>=2.12.0"' in pyproject


def test_lock_resolves_current_patched_transport_versions() -> None:
    """Keep the generated lock aligned with the reviewed security resolution."""

    lock = (PROJECT_ROOT / "uv.lock").read_text(encoding="utf-8")

    for dependency_name, resolved_version in (
        ("anyio", "4.14.2"),
        ("httpx2", "2.13.0"),
        ("httpcore2", "2.13.0"),
    ):
        assert re.search(
            rf'\[\[package\]\]\nname = "{dependency_name}"\n'
            rf'version = "{re.escape(resolved_version)}"',
            lock,
        )
