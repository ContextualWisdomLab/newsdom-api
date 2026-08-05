"""Contracts for NewsDOM's hourly commercial-maintenance caller."""

from __future__ import annotations

from pathlib import Path
import re


WORKFLOW_PATH = Path(".github/workflows/hourly-commercial-maintenance.yml")


def _workflow_text() -> str:
    """Return the tracked hourly workflow text."""

    return WORKFLOW_PATH.read_text(encoding="utf-8")


def test_hourly_cadence_is_single_flight() -> None:
    """The repository should request one non-overlapping maintenance run each hour."""

    workflow = _workflow_text()

    assert 'cron: "41 * * * *"' in workflow
    assert "hourly-commercial-maintenance-${{ github.repository }}" in workflow
    assert "cancel-in-progress: true" in workflow
    assert 'max_dispatches: "1"' in workflow
    assert 'retry_hours: "1"' in workflow


def test_caller_targets_newsdom_develop_through_immutable_central_source() -> None:
    """The leaf workflow must retain only local routing and pin central behavior by SHA."""

    workflow = _workflow_text()
    match = re.search(
        r"uses: ContextualWisdomLab/\.github/\.github/workflows/"
        r"nvidia-nim-pr-maintenance\.yml@([0-9a-f]{40})",
        workflow,
    )

    assert match is not None
    assert match.group(1) == "2ebda8063d3c541e2552dc474c3c8601ddc986f8"
    assert "target_repository: ContextualWisdomLab/newsdom-api" in workflow
    assert "base_branch: develop" in workflow
    assert "uses: ./.github/workflows/" not in workflow
    assert "@main" not in workflow


def test_caller_grants_only_scheduler_permissions() -> None:
    """The reusable scheduler receives no code-write or merge permission from the leaf."""

    workflow = _workflow_text()

    required_permissions = (
        "actions: write",
        "contents: read",
        "id-token: write",
        "issues: write",
        "pull-requests: read",
        "statuses: read",
    )
    for permission in required_permissions:
        assert permission in workflow

    assert "contents: write" not in workflow
    assert "pull-requests: write" not in workflow
    assert "secrets: inherit" not in workflow


def test_caller_never_uses_copilot_or_model_credentials() -> None:
    """Inference credentials belong to the central NIM worker, not the leaf scheduler."""

    workflow = _workflow_text()

    assert "COPILOT_GITHUB_TOKEN" not in workflow
    assert "NVIDIA_NIM_API_KEY" not in workflow
    assert "NVIDIA_API_KEY" not in workflow
    assert "STRIX_GITHUB_MODELS_TOKEN" not in workflow
    assert "models.github.ai" not in workflow


def test_manual_dry_run_is_available_without_changing_schedule_behavior() -> None:
    """Operators should be able to inspect the queue without dispatching repairs."""

    workflow = _workflow_text()

    assert "workflow_dispatch:" in workflow
    assert "dry_run:" in workflow
    assert "type: boolean" in workflow
    assert "github.event_name == 'workflow_dispatch'" in workflow
