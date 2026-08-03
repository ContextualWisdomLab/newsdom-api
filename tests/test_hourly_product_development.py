"""Contract tests for the hourly autonomous product-development workflow."""

from pathlib import Path


WORKFLOW_PATH = (
    Path(__file__).parents[1]
    / ".github"
    / "workflows"
    / "hourly-product-development.yml"
)


def _workflow() -> str:
    """Return the workflow as text without adding a YAML test dependency."""

    return WORKFLOW_PATH.read_text(encoding="utf-8")


def test_hourly_product_development_uses_supported_agent_task_authentication():
    """Agent Tasks REST calls use a fine-grained user token, not GITHUB_TOKEN."""

    workflow = _workflow()

    assert 'AGENT_TASK_TOKEN: ${{ secrets.COPILOT_GITHUB_TOKEN }}' in workflow
    assert 'REPOSITORY_TOKEN: ${{ github.token }}' in workflow
    assert 'GH_TOKEN="$AGENT_TASK_TOKEN" gh api' in workflow
    assert 'GH_TOKEN="$REPOSITORY_TOKEN" gh pr list' in workflow
    assert 'X-GitHub-Api-Version: 2022-11-28' in workflow
    assert "copilot-requests: write" not in workflow
    assert "GH_TOKEN: ${{ github.token }}" not in workflow


def test_hourly_product_development_is_single_flight_and_fail_closed():
    """New work starts only when no PR or active or unknown task exists."""

    workflow = _workflow()

    assert 'cron: "41 * * * *"' in workflow
    assert "cancel-in-progress: false" in workflow
    assert '--state open --limit 1 --json number,url' in workflow
    assert '"/agents/repos/${GITHUB_REPOSITORY}/tasks?per_page=100"' in workflow
    assert "reason=open_pull_request" in workflow
    assert "reason=agent_task_token_unavailable" in workflow
    assert "reason=task_inventory_unavailable" in workflow
    assert "reason=active_agent_task" in workflow
    assert '$state != "completed"' in workflow
    assert '$state != "failed"' in workflow
    assert '$state != "timed_out"' in workflow
    assert '$state != "cancelled"' in workflow
    assert "// \"unknown\"" in workflow


def test_hourly_product_task_is_bounded_and_commercially_focused():
    """Every cycle creates one reviewable PR and never self-merges or publishes."""

    workflow = _workflow()

    assert "create_pull_request: true" in workflow
    assert "single highest-value" in workflow
    assert "buyer-visible" in workflow
    assert "Work test-first" in workflow
    assert "100% production statement and branch coverage" in workflow
    assert "complete production docstrings" in workflow
    assert "Update CHANGELOG.md" in workflow
    assert "Create exactly one bounded pull request" in workflow
    assert "security-sensitive edge cases" in workflow
    assert "Do not merge, publish," in workflow
    assert "release, or bypass reviews" in workflow
    assert "standalone service and a modular sidecar" in workflow
    assert "naruon" in workflow
    assert "gh pr merge" not in workflow
