from __future__ import annotations

from pathlib import Path
import re


def _locked_package_version(name: str) -> tuple[int, ...]:
    text = Path("uv.lock").read_text(encoding="utf-8")
    match = re.search(
        rf'\[\[package\]\]\nname = "{re.escape(name)}"\nversion = "([^"]+)"',
        text,
    )
    assert match is not None, f"package {name!r} missing from uv.lock"
    return tuple(int(part) for part in match.group(1).split("."))


def _dependencies_section(text: str) -> str:
    marker = "dependencies = ["
    if marker not in text:
        raise AssertionError("pyproject.toml is missing a project dependencies section")

    start = text.index(marker) + len(marker)
    bracket_depth = 1
    in_string = False
    escape = False

    for index in range(start, len(text)):
        char = text[index]

        if in_string:
            if escape:
                escape = False
                continue
            if char == "\\":
                escape = True
                continue
            if char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue
        if char == "[":
            bracket_depth += 1
            continue
        if char == "]":
            bracket_depth -= 1
            if bracket_depth == 0:
                return text[start:index]

    raise AssertionError("pyproject.toml dependencies array is not properly closed")


def _project_version(text: str) -> str:
    match = re.search(
        r'^\[project\]\n(?:.*\n)*?^version = "([^"]+)"',
        text,
        re.MULTILINE,
    )
    if match is None:
        raise AssertionError("pyproject.toml is missing [project].version")
    return match.group(1)


def test_dependencies_section_reports_missing_marker_clearly():
    try:
        _dependencies_section("[project]\nname = 'newsdom-api'\n")
    except AssertionError as exc:
        assert str(exc) == "pyproject.toml is missing a project dependencies section"
    else:
        raise AssertionError("expected missing dependencies marker assertion")


def test_dependencies_section_handles_dependency_extras_safely():
    text = '[project]\ndependencies = [\n  "example[docs]>=1.0",\n  "plain>=2.0",\n]\n'

    section = _dependencies_section(text)

    assert '"example[docs]>=1.0"' in section
    assert '"plain>=2.0"' in section


def test_security_dependency_floors_exclude_known_vulnerable_ranges():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    dependencies_section = _dependencies_section(text)

    assert '"Pillow>=12.3,<13.0"' in dependencies_section
    assert '"pypdf>=6.14.2,<7.0"' in dependencies_section
    assert 'requires = ["setuptools>=83", "wheel"]' in text


def test_project_metadata_does_not_bundle_mineru_extra():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    dependencies_section = _dependencies_section(text)
    assert "mineru[pipeline]" not in dependencies_section


def test_project_version_is_prepared_for_v0_2_0_release():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert _project_version(text) == "0.2.0"


def test_project_version_lookup_uses_project_section_only() -> None:
    text = (
        '[tool.example]\nversion = "9.9.9"\n\n'
        '[project]\nname = "newsdom-api"\nversion = "0.2.0"\n'
    )
    assert _project_version(text) == "0.2.0"


def test_uv_lock_tracks_project_version() -> None:
    pyproject_text = Path("pyproject.toml").read_text(encoding="utf-8")
    pyproject_version = _project_version(pyproject_text)

    uv_lock_text = Path("uv.lock").read_text(encoding="utf-8")
    lock_version = re.search(
        r'\[\[package\]\]\nname = "newsdom-api"\nversion = "([^"]+)"',
        uv_lock_text,
    )
    assert lock_version is not None
    assert lock_version.group(1) == pyproject_version


def test_docs_theme_range_tracks_pymdownx_cve_fix():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    # 9.6.x capped pymdown-extensions~=10.2 (<11), blocking the CVE-2026-61632
    # fix. The 9.7.x theme removes that upper bound, while the project retains a
    # direct major-version security floor and keeps MkDocs core on the 1.x line.
    assert '"mkdocs-material>=9.7,<9.8"' in text
    assert '"pymdown-extensions>=11,<12"' in text
    assert _locked_package_version("pymdown-extensions") >= (11, 0, 0)


def test_docs_core_range_stays_below_mkdocs_two():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert '"mkdocs>=1.6,<2.0"' in text


def test_contributing_documents_docs_toolchain_hold():
    text = Path("CONTRIBUTING.md").read_text(encoding="utf-8")
    expected_phrases = [
        "MkDocs 1.x",
        "mkdocs<2.0",
        "mkdocs-material",
        "CVE-2026-61632",
        "uv.lock",
        "migration path",
    ]
    for phrase in expected_phrases:
        assert phrase in text


def test_project_uses_spdx_license_string_not_deprecated_table():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'license = "MIT"' in text
    assert 'license = {text = "MIT"}' not in text


def test_project_declares_locked_fuzz_extra_without_bundling_nvidia_stack():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "fuzz = [" in text
    assert '"atheris==3.0.0 ;' in text
    assert '"pyinstaller==6.21.0"' in text
    assert "nvidia = [" not in text


def test_project_keeps_mineru_pipeline_stack_out_of_pyproject_metadata():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    dependencies_section = _dependencies_section(text)

    assert '"mineru[pipeline]==3.4.4"' not in dependencies_section
    assert "\nmineru = [" not in text
    assert 'mineru = "mineru.cli.app:app"' not in text


def test_uv_lock_does_not_track_external_mineru_pipeline_runtime_stack():
    text = Path("uv.lock").read_text(encoding="utf-8")

    assert '[[package]]\nname = "mineru"' not in text
    assert '[[package]]\nname = "transformers"' not in text
    assert '[[package]]\nname = "torch"' not in text


def test_uv_lock_pins_pypdf_at_patched_release():
    assert _locked_package_version("pypdf") >= (6, 14, 2)
