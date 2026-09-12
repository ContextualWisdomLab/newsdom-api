"""Contracts for bounded parser admission control."""

from pathlib import Path

import pytest
import yaml

from newsdom_api.config import (
    RuntimeConfigurationError,
    RuntimeSettings,
    load_runtime_settings,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    """Read one repository-relative UTF-8 artifact."""

    return (REPOSITORY_ROOT / path).read_text(encoding="utf-8")


def test_runtime_settings_default_to_one_concurrent_parse() -> None:
    """A standalone process should admit one expensive parse by default."""

    settings = RuntimeSettings()

    assert settings.max_concurrent_parses == 1


def test_runtime_settings_load_configured_parse_capacity() -> None:
    """Operators should be able to set a bounded per-process parse budget."""

    settings = load_runtime_settings({"NEWSDOM_MAX_CONCURRENT_PARSES": "8"})

    assert settings.max_concurrent_parses == 8


@pytest.mark.parametrize("raw_value", ["", "0", "129", "not-an-integer"])
def test_runtime_settings_reject_invalid_environment_capacity(raw_value: str) -> None:
    """Environment input must be an integer in the supported process range."""

    with pytest.raises(RuntimeConfigurationError, match="NEWSDOM_MAX_CONCURRENT_PARSES"):
        load_runtime_settings({"NEWSDOM_MAX_CONCURRENT_PARSES": raw_value})


@pytest.mark.parametrize("capacity", [0, 129, True, "3"])
def test_runtime_settings_reject_invalid_direct_capacity(capacity: object) -> None:
    """Direct construction must preserve the same immutable capacity boundary."""

    with pytest.raises(RuntimeConfigurationError, match="NEWSDOM_MAX_CONCURRENT_PARSES"):
        RuntimeSettings(max_concurrent_parses=capacity)  # type: ignore[arg-type]


def test_deployment_examples_publish_the_per_process_capacity_budget() -> None:
    """Every production example should expose one explicit parser capacity."""

    assert "NEWSDOM_MAX_CONCURRENT_PARSES=1" in _text(".env.example")

    compose = yaml.safe_load(_text("docker-compose.yml"))
    compose_environment = compose["services"]["newsdom-api"]["environment"]
    assert compose_environment["NEWSDOM_MAX_CONCURRENT_PARSES"] == "1"

    documents = list(
        yaml.safe_load_all(_text("docs/operations/kubernetes-deployment.yaml"))
    )
    deployment = next(document for document in documents if document["kind"] == "Deployment")
    container = deployment["spec"]["template"]["spec"]["containers"][0]
    environment = {entry["name"]: entry for entry in container["env"]}
    assert environment["NEWSDOM_MAX_CONCURRENT_PARSES"]["value"] == "1"


def test_operator_docs_explain_non_waiting_backpressure_and_replica_capacity() -> None:
    """Operators need enough context to size capacity without hidden queues."""

    combined = "\n".join(
        (
            _text("README.md"),
            _text("ARCHITECTURE.md"),
            _text("docs/operations/deploy-runbook.md"),
            _text("CHANGELOG.md"),
        )
    )

    for expected in (
        "NEWSDOM_MAX_CONCURRENT_PARSES",
        "429 Too Many Requests",
        "Retry-After: 1",
        "per process",
        "replica",
        "before the multipart body",
    ):
        assert expected in combined


def test_capacity_doctoring_records_primary_sources_in_apa_seventh_style() -> None:
    """The decision record should preserve standards and security rationale."""

    doctoring = _text("docs/doctoring/bounded-parser-admission.md")

    for expected in (
        "Nottingham, M., & Fielding, R. (2012)",
        "Fielding, R., Nottingham, M., & Reschke, J. (2022)",
        "OWASP Foundation. (2023)",
        "Python Software Foundation. (2026)",
        "RFC 6585",
        "RFC 9111",
        "API4:2023",
        "BoundedSemaphore",
        "Rollback",
    ):
        assert expected in doctoring
