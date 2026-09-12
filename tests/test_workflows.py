from pathlib import Path

import pytest
import yaml


def _load_workflow(workflow_name: str) -> dict:
    return yaml.safe_load(
        Path(".github/workflows", workflow_name).read_text(encoding="utf-8")
    )


def _triggers(workflow: dict) -> dict:
    return workflow.get("on", workflow.get(True))


@pytest.mark.parametrize(
    ("workflow_name", "group", "cancel_in_progress"),
    [
        (
            "tests.yml",
            "tests-${{ github.repository }}-${{ github.event.pull_request.number }}",
            True,
        ),
        (
            "clusterfuzzlite.yml",
            "clusterfuzzlite-${{ github.repository }}-${{ github.event.pull_request.number || github.run_id }}",
            "${{ github.event_name == 'pull_request' }}",
        ),
        (
            "container-image.yml",
            "container-image-${{ github.repository }}-${{ github.event.pull_request.number || github.ref }}",
            False,
        ),
        (
            "build-ci-image.yml",
            "build-ci-environment-image-${{ github.repository }}-${{ github.event.pull_request.number || github.ref }}",
            False,
        ),
        (
            "gh-pages.yml",
            "deploy-web-manual-to-github-pages-${{ github.repository }}-${{ github.ref }}",
            False,
        ),
        (
            "release.yml",
            "release-${{ github.repository }}-${{ github.ref }}",
            False,
        ),
        (
            "codeql.yml",
            "codeql-${{ github.repository }}-${{ github.ref }}",
            False,
        ),
        (
            "scorecards.yml",
            "scorecards-${{ github.repository }}-${{ github.ref }}",
            False,
        ),
    ],
)
def test_workflow_concurrency_is_trigger_aware(
    workflow_name: str, group: str, cancel_in_progress: bool | str
) -> None:
    concurrency = _load_workflow(workflow_name)["concurrency"]

    assert concurrency == {
        "group": group,
        "cancel-in-progress": cancel_in_progress,
    }


def test_tests_run_once_per_pull_request_without_post_merge_push_duplication() -> None:
    triggers = _triggers(_load_workflow("tests.yml"))

    assert set(triggers) == {"pull_request"}


@pytest.mark.parametrize("workflow_name", ["codeql.yml", "scorecards.yml"])
def test_central_security_owners_replace_local_pr_triggers(
    workflow_name: str,
) -> None:
    triggers = _triggers(_load_workflow(workflow_name))

    assert "pull_request" not in triggers
    assert {"push", "schedule"}.issubset(triggers)


@pytest.mark.parametrize(
    "workflow_name", ["clusterfuzzlite.yml", "container-image.yml"]
)
def test_expensive_pr_workflows_skip_documentation_only_changes(
    workflow_name: str,
) -> None:
    paths_ignore = set(
        _triggers(_load_workflow(workflow_name))["pull_request"]["paths-ignore"]
    )

    assert paths_ignore == {"docs/**", "manual/**", "**.md"}


def test_tagged_container_release_has_no_path_filter() -> None:
    push_trigger = _triggers(_load_workflow("container-image.yml"))["push"]

    assert push_trigger == {"tags": ["v*"]}
