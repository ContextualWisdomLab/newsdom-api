"""Contracts for documentation-only GitHub Actions filtering."""

from pathlib import Path

import pytest


_DOC_ONLY_PATHS = {"docs/**", "manual/**", "**.md"}


def _event_block(workflow: str, event: str) -> list[str]:
    """Return one peer event block from the workflow's top-level ``on`` mapping."""
    lines = workflow.splitlines()
    marker = f"  {event}:"
    try:
        start = lines.index(marker)
    except ValueError as exc:
        raise AssertionError(f"missing workflow event: {event}") from exc

    block: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("  ") and not line.startswith("    "):
            break
        block.append(line)
    return block


def _paths_ignore(block: list[str]) -> set[str]:
    """Read the ``paths-ignore`` list from one event block without quote coupling."""
    try:
        start = block.index("    paths-ignore:")
    except ValueError as exc:
        raise AssertionError("event is missing paths-ignore") from exc

    entries: set[str] = set()
    for line in block[start + 1 :]:
        if not line.startswith("      - "):
            break
        entries.add(line.removeprefix("      - ").strip().strip("'\""))
    return entries


@pytest.mark.parametrize(
    "workflow_path",
    (
        ".github/workflows/clusterfuzzlite.yml",
        ".github/workflows/container-image.yml",
    ),
)
def test_pr_filters_ignore_all_documentation_assets(workflow_path: str) -> None:
    """PR filters skip Markdown, generated docs, and non-Markdown manual assets."""
    workflow = Path(workflow_path).read_text(encoding="utf-8")
    pull_request = _event_block(workflow, "pull_request")

    assert _paths_ignore(pull_request) == _DOC_ONLY_PATHS


def test_tagged_container_release_does_not_claim_path_filtering() -> None:
    """Tag pushes retain their release trigger without an ineffective path filter."""
    workflow = Path(".github/workflows/container-image.yml").read_text(encoding="utf-8")
    push_section = _event_block(workflow, "push")

    assert "    paths-ignore:" not in push_section
    assert "    tags:" in push_section
    assert "      - 'v*'" in push_section
