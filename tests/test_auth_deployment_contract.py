"""Deployment and documentation contracts for fail-closed authentication."""

from __future__ import annotations

import re
from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    """Read one repository-relative UTF-8 text artifact."""

    return (REPOSITORY_ROOT / path).read_text(encoding="utf-8")


def _project_version(pyproject_text: str) -> str:
    """Return the project version without requiring Python 3.11 ``tomllib``."""

    match = re.search(
        r'^\[project\]\n(?:.*\n)*?^version = "([^"]+)"',
        pyproject_text,
        re.MULTILINE,
    )
    if match is None:
        raise AssertionError("pyproject.toml is missing [project].version")
    return match.group(1)


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


def test_kubernetes_manifest_uses_restricted_non_root_runtime() -> None:
    """The example workload must meet the bounded restricted-container contract."""

    documents = list(
        yaml.safe_load_all(_text("docs/operations/kubernetes-deployment.yaml"))
    )
    namespace = next(doc for doc in documents if doc["kind"] == "Namespace")
    deployment = next(doc for doc in documents if doc["kind"] == "Deployment")
    pod_spec = deployment["spec"]["template"]["spec"]
    pod_security = pod_spec["securityContext"]
    container = pod_spec["containers"][0]
    container_security = container["securityContext"]

    assert namespace["metadata"]["labels"] == {
        "pod-security.kubernetes.io/enforce": "restricted",
        "pod-security.kubernetes.io/audit": "restricted",
        "pod-security.kubernetes.io/warn": "restricted",
    }
    assert pod_spec["automountServiceAccountToken"] is False
    assert pod_security["runAsNonRoot"] is True
    assert pod_security["runAsUser"] == 10001
    assert pod_security["runAsGroup"] == 10001
    assert pod_security["fsGroup"] == 10001
    assert pod_security["fsGroupChangePolicy"] == "OnRootMismatch"
    assert pod_security["seccompProfile"] == {"type": "RuntimeDefault"}

    assert container_security["allowPrivilegeEscalation"] is False
    assert container_security["privileged"] is False
    assert container_security["readOnlyRootFilesystem"] is True
    assert container_security["runAsNonRoot"] is True
    assert container_security["runAsUser"] == 10001
    assert container_security["runAsGroup"] == 10001
    assert container_security["capabilities"] == {"drop": ["ALL"]}

    mounts_by_path = {mount["mountPath"]: mount for mount in container["volumeMounts"]}
    volumes_by_name = {volume["name"]: volume for volume in pod_spec["volumes"]}
    temporary_mount = mounts_by_path["/tmp"]
    cache_mount = mounts_by_path["/home/newsdom"]

    assert temporary_mount["readOnly"] is False
    assert cache_mount["readOnly"] is False
    assert volumes_by_name[temporary_mount["name"]]["emptyDir"]["sizeLimit"] == "1Gi"
    assert volumes_by_name[cache_mount["name"]]["emptyDir"]["sizeLimit"] == "4Gi"


def test_kubernetes_manifest_uses_an_explicit_unreleased_image_placeholder() -> None:
    """An unreleased migration must not advertise a nonexistent release image."""

    documents = list(
        yaml.safe_load_all(_text("docs/operations/kubernetes-deployment.yaml"))
    )
    deployment = next(doc for doc in documents if doc["kind"] == "Deployment")
    container = deployment["spec"]["template"]["spec"]["containers"][0]

    assert container["image"] == "ghcr.io/contextualwisdomlab/newsdom-api:unreleased"
    assert container["imagePullPolicy"] == "Always"
    assert ":0.3.0" not in container["image"]


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


def test_authoritative_deployment_docs_reject_obsolete_default_open_guidance() -> None:
    """Newer text must not coexist with contradictory operator instructions."""

    changelog = _text("CHANGELOG.md")
    runbook = _text("docs/operations/deploy-runbook.md")
    authoritative = "\n".join((changelog, _text("README.md"), runbook)).lower()

    for obsolete_phrase in (
        "미설정 시 개방",
        "optional bearer",
        "healthcheck가 `/health`",
        "healthcheck targets `/health`",
        "no in-tree kubernetes manifests",
    ):
        assert obsolete_phrase not in authoritative

    for required_phrase in (
        "newsdom_auth_mode=required",
        "newsdom_runtime_profile=production",
        "newsdom_api_token",
        "get /health",
        "get /ready",
    ):
        assert required_phrase in authoritative


def test_package_openapi_and_manifest_do_not_claim_an_unreleased_version() -> None:
    """Package and OpenAPI versions must agree while deployment stays Unreleased."""

    project_version = _project_version(_text("pyproject.toml"))
    main_source = _text("src/newsdom_api/main.py")
    version_match = re.search(
        r"application = FastAPI\([\s\S]*?\n\s*version=\"([^\"]+)\"",
        main_source,
    )
    assert version_match is not None
    assert version_match.group(1) == project_version

    documents = list(
        yaml.safe_load_all(_text("docs/operations/kubernetes-deployment.yaml"))
    )
    deployment = next(doc for doc in documents if doc["kind"] == "Deployment")
    image = deployment["spec"]["template"]["spec"]["containers"][0]["image"]
    assert image.endswith(":unreleased")
    assert f":{project_version}" not in image


def test_project_version_parser_is_scoped_to_the_project_table() -> None:
    """Unrelated tool metadata must not be mistaken for the package version."""

    text = (
        '[tool.example]\nversion = "9.9.9"\n\n'
        '[project]\nname = "newsdom-api"\nversion = "0.2.0"\n'
    )

    assert _project_version(text) == "0.2.0"


def test_project_version_parser_rejects_missing_project_version() -> None:
    """Malformed package metadata should fail with an actionable assertion."""

    try:
        _project_version('[project]\nname = "newsdom-api"\n')
    except AssertionError as exc:
        assert str(exc) == "pyproject.toml is missing [project].version"
    else:
        raise AssertionError("expected a missing project version assertion")


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
