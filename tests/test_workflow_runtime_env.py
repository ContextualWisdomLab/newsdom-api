from pathlib import Path

import yaml


def _workflow_paths() -> list[Path]:
    return sorted(Path(".github/workflows").glob("*.yml")) + sorted(
        Path(".github/workflows").glob("*.yaml")
    )


def test_each_workflow_job_forces_javascript_actions_to_node24():
    for workflow_path in _workflow_paths():
        data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        for job_name, job_data in data["jobs"].items():
            if workflow_path.name in {"scorecards.yml", "gh-pages.yml"}:
                continue
            assert job_data["env"]["FORCE_JAVASCRIPT_ACTIONS_TO_NODE24"] is True, (
                workflow_path,
                job_name,
            )


def test_workflows_do_not_use_top_level_env_blocks():
    for workflow_path in _workflow_paths():
        text = workflow_path.read_text(encoding="utf-8")
        assert not text.startswith("env:\n")
        assert "\nenv:\n" not in text.split("jobs:", 1)[0], workflow_path


def test_gh_pages_workflow_keeps_node24_force_off_upload_pages_artifact_step():
    data = yaml.safe_load(
        Path(".github/workflows/gh-pages.yml").read_text(encoding="utf-8")
    )
    build_job = data["jobs"]["build"]
    deploy_job = data["jobs"]["deploy"]
    build_steps_by_name = {step["name"]: step for step in build_job["steps"]}

    assert "env" not in build_job
    assert "env" not in deploy_job
    assert (
        build_steps_by_name["Checkout repository"]["env"][
            "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24"
        ]
        is True
    )
    assert (
        build_steps_by_name["Set up Python"]["env"][
            "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24"
        ]
        is True
    )
    assert (
        build_steps_by_name["Set up uv"]["env"]["FORCE_JAVASCRIPT_ACTIONS_TO_NODE24"]
        is True
    )
    assert "env" not in build_steps_by_name["Upload GitHub Pages artifact"]


def test_central_review_workflows_are_not_copied_into_this_repository():
    central_only_paths = [
        Path(".github/workflows/opencode-review.yml"),
        Path(".github/workflows/pr-review-merge-scheduler.yml"),
        Path(".github/workflows/strix.yml"),
        Path("requirements-opencode-review-ci.txt"),
        Path("requirements-strix-ci.txt"),
        Path("requirements-strix-ci-hashes.txt"),
        Path("scripts/ci/collect_failed_check_evidence.sh"),
        Path("scripts/ci/emit_opencode_failed_check_fallback_findings.sh"),
        Path("scripts/ci/opencode_review_approve_gate.sh"),
        Path("scripts/ci/opencode_review_normalize_output.py"),
        Path("scripts/ci/pr_review_merge_scheduler.py"),
        Path("scripts/ci/strix_model_utils.sh"),
        Path("scripts/ci/strix_quick_gate.sh"),
        Path("scripts/ci/test_opencode_fact_gate_contract.sh"),
        Path("scripts/ci/test_strix_quick_gate.sh"),
        Path("scripts/ci/validate_opencode_failed_check_review.sh"),
    ]

    for central_only_path in central_only_paths:
        assert not central_only_path.exists(), central_only_path


def test_central_governance_workflows_are_not_copied_into_this_repository():
    # Security/governance scanning (OpenSSF Scorecard, CodeQL, dependency
    # review) is provided by the org-wide CENTRAL required workflows in
    # ContextualWisdomLab/.github. Local duplicates cause double runs and
    # duplicate SARIF uploads, so they must not exist in this repository.
    central_governance_paths = [
        Path(".github/workflows/scorecards.yml"),
        Path(".github/workflows/codeql.yml"),
        Path(".github/workflows/dependency-review.yml"),
    ]

    for central_governance_path in central_governance_paths:
        assert not central_governance_path.exists(), central_governance_path
