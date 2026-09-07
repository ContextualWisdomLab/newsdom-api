from __future__ import annotations

import re
import shlex
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _coverage_source_paths() -> set[str]:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(
        r"(?ms)^\[tool\.coverage\.run\]\s*$\n(?P<section>.*?)(?=^\[|\Z)",
        pyproject,
    )
    assert match is not None, "pyproject.toml must declare [tool.coverage.run]"

    source_match = re.search(r"(?m)^source\s*=\s*\[(?P<paths>[^]]+)\]", match["section"])
    assert source_match is not None, "coverage run config must declare source paths"
    return set(re.findall(r'"([^"]+)"', source_match["paths"]))


def test_ci_coverage_uses_project_sources_without_narrowing_them() -> None:
    """CI must measure every production source declared by coverage configuration."""
    declared_sources = _coverage_source_paths()
    assert {"src/newsdom_api", "tools"}.issubset(declared_sources)

    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
    )
    pytest_job = workflow["jobs"]["pytest"]
    coverage_step = next(
        step for step in pytest_job["steps"] if step.get("name") == "Run tests with coverage"
    )
    command = coverage_step["run"]
    tokens = shlex.split(command)

    assert "--cov" in tokens, (
        "pytest-cov must use bare --cov so [tool.coverage.run].source remains authoritative; "
        "--cov=<value> overrides the configured source set"
    )
    assert not any(token.startswith("--cov=") for token in tokens)
