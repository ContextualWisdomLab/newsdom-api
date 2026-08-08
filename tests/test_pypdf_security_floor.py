from __future__ import annotations

from pathlib import Path
import re


_REQUIRED_PYPDF_VERSION = (6, 15, 0)
_CURRENT_PYPDF_CVES = ("CVE-2026-71852", "CVE-2026-71870")


def _locked_pypdf_version() -> tuple[int, ...]:
    """Return the pypdf version resolved in the project lock file."""

    lock_text = Path("uv.lock").read_text(encoding="utf-8")
    match = re.search(
        r'\[\[package\]\]\nname = "pypdf"\nversion = "([^"]+)"',
        lock_text,
    )
    assert match is not None, "pypdf is missing from uv.lock"
    return tuple(int(part) for part in match.group(1).split("."))


def test_project_declares_current_pypdf_security_floor() -> None:
    """Prevent future lock refreshes from selecting the vulnerable 6.14.x line."""

    project_text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert '"pypdf>=6.15.0,<7.0"' in project_text


def test_lock_uses_current_pypdf_security_release() -> None:
    """Require the resolved parser used by CI and production to be remediated."""

    assert _locked_pypdf_version() >= _REQUIRED_PYPDF_VERSION


def test_current_pypdf_findings_are_not_suppressed() -> None:
    """Keep current pypdf vulnerability findings visible to the Trivy gate."""

    ignore_text = Path(".trivyignore").read_text(encoding="utf-8")
    for cve_id in _CURRENT_PYPDF_CVES:
        assert cve_id not in ignore_text
