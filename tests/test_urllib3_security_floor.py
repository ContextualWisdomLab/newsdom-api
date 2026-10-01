"""Regression contract for the urllib3 security floor."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PATCHED_URLLIB3_VERSION = "2.8.0"
_CURRENT_URLLIB3_ADVISORIES = (
    "CVE-2026-97687",
    "CVE-2026-97688",
    "CVE-2026-97689",
)


def test_project_and_lock_require_patched_urllib3() -> None:
    """Prevent lock refreshes from restoring the vulnerable 2.7.0 release."""

    project_text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    lock_text = (PROJECT_ROOT / "uv.lock").read_text(encoding="utf-8")

    assert '"urllib3>=2.8.0,<3.0"' in project_text
    assert re.search(
        rf'\[\[package\]\]\nname = "urllib3"\nversion = "{_PATCHED_URLLIB3_VERSION}"',
        lock_text,
    )
    assert '{ name = "urllib3", specifier = ">=2.8.0,<3.0" },' in lock_text


def test_urllib3_advisories_remain_visible_and_documented() -> None:
    """Keep Trivy findings unsuppressed and operator evidence reconstructable."""

    ignore_text = (PROJECT_ROOT / ".trivyignore.yaml").read_text(encoding="utf-8")
    doctoring = (
        PROJECT_ROOT / "docs/doctoring/dependency-security-baseline.md"
    ).read_text(encoding="utf-8")
    changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    for advisory_id in _CURRENT_URLLIB3_ADVISORIES:
        assert advisory_id not in ignore_text
        assert advisory_id in doctoring
        assert advisory_id in changelog

    assert "urllib3 2.8.0" in doctoring
    assert "urllib3 2.8.0" in changelog
