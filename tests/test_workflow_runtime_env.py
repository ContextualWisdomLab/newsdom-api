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


def test_scorecards_workflow_keeps_node24_force_out_of_job_env():
    data = yaml.safe_load(
        Path(".github/workflows/scorecards.yml").read_text(encoding="utf-8")
    )
    scorecard_job = data["jobs"]["scorecard"]
    steps_by_name = {step["name"]: step for step in scorecard_job["steps"]}

    assert "env" not in scorecard_job
    assert (
        steps_by_name["Checkout"]["env"]["FORCE_JAVASCRIPT_ACTIONS_TO_NODE24"] is True
    )
    assert (
        steps_by_name["Upload SARIF results"]["env"][
            "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24"
        ]
        is True
    )


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
