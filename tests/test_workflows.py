from pathlib import Path

import yaml


PR_WORKFLOW_JOBS = {
    "build-ci-image.yml": "build-and-push",
    "clusterfuzzlite.yml": "fuzz",
    "codeql.yml": "analyze",
    "container-image.yml": "image",
    "dependency-review.yml": "dependency-review",
    "quality-gate.yml": "quality-gate",
    "scorecards.yml": "scorecard",
    "tests.yml": "pytest",
}
PR_TRIGGER_TYPES = ["opened", "synchronize", "reopened", "ready_for_review"]
PR_CONCURRENCY_GROUP = (
    "${{ github.workflow }}-${{ github.repository }}-"
    "${{ github.event.pull_request.number || github.run_id }}"
)


def test_scorecards_push_runs_only_on_default_branch():
    text = Path(".github/workflows/scorecards.yml").read_text(encoding="utf-8")
    push_section = text.split("pull_request:", 1)[0]
    assert "branches: [develop]" in push_section
    assert "branches: [main, develop]" not in push_section


def test_scorecards_pull_requests_cover_main_and_develop():
    text = Path(".github/workflows/scorecards.yml").read_text(encoding="utf-8")
    assert "pull_request:" in text
    pull_request_section = text.split("pull_request:", 1)[1].split("schedule:", 1)[0]
    assert "branches:" not in pull_request_section


def test_scorecards_workflow_supports_optional_repo_token_for_branch_protection():
    text = Path(".github/workflows/scorecards.yml").read_text(encoding="utf-8")
    assert "repo_token: ${{ secrets.SCORECARD_TOKEN || github.token }}" in text


def test_pr_workflows_skip_drafts_and_cancel_stale_pr_runs():
    """Require every local PR workflow to avoid draft runner consumption."""
    for workflow_name, job_name in PR_WORKFLOW_JOBS.items():
        workflow = yaml.safe_load(
            Path(f".github/workflows/{workflow_name}").read_text(encoding="utf-8")
        )
        triggers = workflow.get("on", workflow.get(True))
        assert triggers["pull_request"]["types"] == PR_TRIGGER_TYPES
        assert workflow["concurrency"]["group"] == PR_CONCURRENCY_GROUP
        assert workflow["concurrency"]["cancel-in-progress"] == (
            "${{ github.event_name == 'pull_request' }}"
        )
        assert workflow["jobs"][job_name]["if"] == (
            "${{ github.event_name != 'pull_request' || "
            "!github.event.pull_request.draft }}"
        )
