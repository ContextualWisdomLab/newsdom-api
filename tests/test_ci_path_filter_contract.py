"""Contracts for documentation-only GitHub Actions filtering."""

from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "workflow_path",
    (
        ".github/workflows/clusterfuzzlite.yml",
        ".github/workflows/container-image.yml",
    ),
)
def test_pr_filters_ignore_markdown_at_any_depth(workflow_path: str) -> None:
    """PR filters cover nested Markdown instead of repository-root files only."""
    workflow = Path(workflow_path).read_text(encoding="utf-8")

    assert '      - "**.md"' in workflow
    assert '      - "*.md"' not in workflow


def test_tagged_container_release_does_not_claim_path_filtering() -> None:
    """Tag pushes retain their release trigger without an ineffective path filter."""
    workflow = Path(".github/workflows/container-image.yml").read_text(encoding="utf-8")
    push_section = workflow.split("  push:\n", maxsplit=1)[1].split(
        "  workflow_dispatch:\n", maxsplit=1
    )[0]

    assert "paths-ignore:" not in push_section
    assert "tags:\n      - 'v*'" in push_section
