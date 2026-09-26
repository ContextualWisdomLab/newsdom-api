from __future__ import annotations

from pathlib import Path
import re

import yaml


_REQUIRED_PYPDF_VERSION = (6, 16, 1)
_LOCKED_PYPDF_VERSION = (6, 18, 0)
_CURRENT_PYPDF_ADVISORIES = (
    ("CVE-2026-84309", "GHSA-jp53-mhqp-8xcg", "6.16.0"),
    ("CVE-2026-84310", "GHSA-23w6-3w8w-8484", "6.16.1"),
    ("CVE-2026-84311", "GHSA-763m-79hh-57f2", "6.16.1"),
)
_LOCKED_PYPDF_REQUIREMENT = '{ name = "pypdf", specifier = ">=6.16.1,<7.0" },'


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
    """Prevent lock refreshes from selecting a version below the full advisory floor."""

    project_text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert '"pypdf>=6.16.1,<7.0"' in project_text


def test_lock_uses_current_pypdf_security_release() -> None:
    """Require the resolved parser used by CI and production to be remediated."""

    assert _locked_pypdf_version() == _LOCKED_PYPDF_VERSION


def test_lock_metadata_matches_current_pypdf_security_floor() -> None:
    """Keep uv's editable-project metadata aligned with the source requirement."""

    lock_text = Path("uv.lock").read_text(encoding="utf-8")
    assert _LOCKED_PYPDF_REQUIREMENT in lock_text


def test_current_pypdf_findings_are_not_suppressed() -> None:
    """Keep current pypdf vulnerability findings visible to the Trivy gate."""

    ignore_text = Path(".trivyignore.yaml").read_text(encoding="utf-8")
    for cve_id, ghsa_id, _fixed_version in _CURRENT_PYPDF_ADVISORIES:
        assert cve_id not in ignore_text
        assert ghsa_id not in ignore_text


def test_current_pypdf_advisories_and_floor_are_documented() -> None:
    """Keep operator-facing evidence aligned with the declared parser floor."""

    baseline = Path("docs/doctoring/dependency-security-baseline.md").read_text(
        encoding="utf-8"
    )
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")

    for cve_id, ghsa_id, fixed_version in _CURRENT_PYPDF_ADVISORIES:
        for document in (baseline, changelog):
            assert cve_id in document
            assert ghsa_id in document
        boundary = re.compile(
            rf"{re.escape(cve_id)}\s*/\s*{re.escape(ghsa_id)}.*?fixed\s+in\s+{re.escape(fixed_version)}",
            re.DOTALL,
        )
        assert boundary.search(baseline) is not None

    assert "`pypdf>=6.16.1,<7.0`" in changelog
    assert "`pypdf>=6.16.1,<7.0`" in baseline
    assert "pypdf 6.18.0" in changelog
    assert "pypdf 6.18.0" in baseline


def test_trivy_registry_exception_is_scoped_to_the_example_manifest() -> None:
    """A documentation exception must not suppress KSV-0125 repository-wide."""

    trivy_config = yaml.safe_load(Path("trivy.yaml").read_text(encoding="utf-8"))
    ignore_document = yaml.safe_load(
        Path(".trivyignore.yaml").read_text(encoding="utf-8")
    )
    exceptions = {
        entry["id"]: entry for entry in ignore_document["misconfigurations"]
    }

    assert trivy_config["ignorefile"] == ".trivyignore.yaml"
    assert exceptions["KSV-0125"]["paths"] == [
        "docs/operations/kubernetes-deployment.yaml"
    ]
    assert exceptions["DS-0002"]["paths"] == [".clusterfuzzlite/Dockerfile"]
