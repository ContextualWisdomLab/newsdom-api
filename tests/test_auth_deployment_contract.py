"""Deployment and documentation contracts for fail-closed authentication."""

from __future__ import annotations

from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    """Read one repository-relative UTF-8 text artifact."""

    return (REPOSITORY_ROOT / path).read_text(encoding="utf-8")


def test_compose_requires_production_authentication_and_probes_readiness() -> None:
    """The standalone compose contract must fail before starting without a token."""

    compose_text = _text("docker-compose.yml")
    compose = yaml.safe_load(compose_text)
    environment = compose["services"]["newsdom-api"]["environment"]
    healthcheck = compose["services"]["newsdom-api"]["healthcheck"]

    assert environment["NEWSDOM_AUTH_MODE"] == "required"
    assert environment["NEWSDOM_RUNTIME_PROFILE"] == "production"
    assert environment["NEWSDOM_API_TOKEN"] == (
        "${NEWSDOM_API_TOKEN:?set NEWSDOM_API_TOKEN}"
    )
    assert "/ready" in " ".join(healthcheck["test"])
    assert "/health" not in " ".join(healthcheck["test"])


def test_example_environment_documents_only_explicit_safe_modes() -> None:
    """The example environment must not normalize production toward the bypass."""

    example = _text(".env.example")

    assert "NEWSDOM_AUTH_MODE=required" in example
    assert "NEWSDOM_RUNTIME_PROFILE=production" in example
    assert "NEWSDOM_API_TOKEN=" in example
    assert "NEWSDOM_AUTH_MODE=disabled" not in example


def test_kubernetes_manifest_separates_liveness_and_readiness() -> None:
    """Kubernetes traffic routing must use `/ready` and keep `/health` for liveness."""

    documents = list(
        yaml.safe_load_all(_text("docs/operations/kubernetes-deployment.yaml"))
    )
    deployment = next(doc for doc in documents if doc["kind"] == "Deployment")
    container = deployment["spec"]["template"]["spec"]["containers"][0]
    env_by_name = {entry["name"]: entry for entry in container["env"]}

    assert container["livenessProbe"]["httpGet"]["path"] == "/health"
    assert container["readinessProbe"]["httpGet"]["path"] == "/ready"
    assert env_by_name["NEWSDOM_AUTH_MODE"]["value"] == "required"
    assert env_by_name["NEWSDOM_RUNTIME_PROFILE"]["value"] == "production"
    assert "secretKeyRef" in env_by_name["NEWSDOM_API_TOKEN"]["valueFrom"]


def test_readme_and_runbook_explain_new_default_and_rollback_boundary() -> None:
    """Operators need an explicit default-open to required migration."""

    combined = _text("README.md") + _text("docs/operations/deploy-runbook.md")

    for phrase in (
        "authentication is required by default",
        "NEWSDOM_AUTH_MODE=required",
        "NEWSDOM_RUNTIME_PROFILE=production",
        "GET /ready",
        "GET /health",
        "development-only bypass",
        "previous default-open behavior",
    ):
        assert phrase in combined
    assert "NEWSDOM_AUTH_MODE=disabled" in combined
    assert "NEWSDOM_RUNTIME_PROFILE=development" in combined


def test_doctoring_records_distinct_failure_domains_and_apa_references() -> None:
    """The security decision record must preserve operational ownership and sources."""

    doctoring = _text("docs/doctoring/fail-closed-parser-authentication.md")

    for phrase in (
        "Caller authentication failure",
        "Service configuration failure",
        "Liveness",
        "Readiness",
        "Development bypass",
        "Standalone and gateway ownership",
        "Hardt, D. (2012)",
        "OWASP Foundation. (2023)",
        "Kubernetes Authors. (2025)",
        "0.3.0",
    ):
        assert phrase in doctoring


def test_changelog_records_breaking_default_and_readiness_endpoint() -> None:
    """The unreleased history must make the deployment behavior change visible."""

    changelog = _text("CHANGELOG.md")

    assert "default-open" in changelog
    assert "default-required" in changelog
    assert "`/ready`" in changelog
    assert "0.3.0" in changelog
