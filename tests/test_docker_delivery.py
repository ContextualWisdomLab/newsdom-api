from pathlib import Path

import pytest
import re
import yaml


def _load_container_image_workflow() -> dict:
    return yaml.safe_load(
        Path(".github/workflows/container-image.yml").read_text(encoding="utf-8")
    )


def _find_step_by_uses(steps: list[dict], uses: str) -> dict:
    match = next((step for step in steps if re.match(rf"{re.escape(uses)}@[0-9a-fA-F]{{40}}", step.get("uses", ""))), None)
    assert match is not None, f"missing workflow step for uses={uses!r}"
    return match


def _dockerignore_entries(text: str) -> set[str]:
    return {
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _contains_docker_build_command(text: str) -> bool:
    normalized = _normalize_whitespace(text)
    return "docker build" in normalized and "-t newsdom-api" in normalized


def _contains_docker_run_command(text: str) -> bool:
    normalized = _normalize_whitespace(text)
    return (
        "docker run" in normalized
        and "-p 8000:8000" in normalized
        and "newsdom-api" in normalized
    )


def _contains_pinned_python_base_image(text: str) -> bool:
    return bool(re.search(r"python:3\.12-slim@sha256:[0-9a-f]{64}", text))


def _contains_pinned_uv_image(text: str) -> bool:
    return bool(re.search(r"ghcr\.io/astral-sh/uv@sha256:[0-9a-f]{64}", text))


def _contains_copy_or_add_reference(text: str, filename: str) -> bool:
    return bool(re.search(rf"^\s*(COPY|ADD)\b.*\b{re.escape(filename)}\b", text, re.M))


def _contains_healthcheck_path(text: str, path: str) -> bool:
    match = re.search(
        r"^HEALTHCHECK\b(?P<body>[\s\S]*?)(?:^[A-Z][A-Z0-9_]*\b|\Z)",
        text,
        re.M,
    )
    return bool(match and path in match.group("body"))


def test_dockerfile_exists():
    assert Path("Dockerfile").exists()


def test_nvidia_dockerfile_exists():
    assert Path("Dockerfile.nvidia").exists()


def test_dockerignore_exists():
    assert Path(".dockerignore").exists()


def test_dockerfile_uses_project_metadata_and_src_layout():
    text = Path("Dockerfile").read_text(encoding="utf-8")
    assert _contains_copy_or_add_reference(text, "pyproject.toml")
    assert _contains_copy_or_add_reference(text, "uv.lock")
    assert "src/" in text
    assert _contains_pinned_python_base_image(text)
    assert _contains_pinned_uv_image(text)


def test_dockerfile_runs_uvicorn_with_external_mineru_path():
    text = Path("Dockerfile").read_text(encoding="utf-8")
    assert "uvicorn" in text
    assert "newsdom_api.main:app" in text
    assert "NEWSDOM_MINERU_BIN" in text
    assert "--host" in text
    assert "0.0.0.0" in text
    assert "8000" in text
    assert not _contains_healthcheck_path(text, "/health")


def test_nvidia_dockerfile_installs_mineru_pipeline_stack():
    text = Path("Dockerfile.nvidia").read_text(encoding="utf-8")
    assert "nvidia/cuda:12.6.3-cudnn-runtime-ubuntu22.04@sha256:" in text
    assert "ghcr.io/astral-sh/uv@sha256:" in text
    assert 'uv pip install --python .venv/bin/python "mineru[pipeline]==3.0.9"' in text
    assert "NEWSDOM_MINERU_BIN" in text


def test_dockerignore_excludes_local_noise():
    entries = _dockerignore_entries(Path(".dockerignore").read_text(encoding="utf-8"))
    for entry in [".git", ".venv", "__pycache__", ".pytest_cache", ".coverage"]:
        assert entry in entries


def test_dockerignore_line_parser_does_not_confuse_prefix_matches():
    entries = _dockerignore_entries(".github\n")

    assert ".git" not in entries


def test_find_step_by_uses_raises_clear_error_for_missing_step():
    with pytest.raises(AssertionError, match="docker/example-action"):
        _find_step_by_uses([], "docker/example-action")


def test_readme_documents_docker_build_and_run():
    text = Path("README.md").read_text(encoding="utf-8")
    assert _contains_docker_build_command(text)
    assert _contains_docker_run_command(text)
    assert "Dockerfile.nvidia" in text
    assert "Apple Silicon" in text
    assert "NVIDIA" in text


def test_readme_describes_default_image_as_shipping_mineru_runtime() -> None:
    text = Path("README.md").read_text(encoding="utf-8")

    assert "NEWSDOM_MINERU_BIN=mineru" in text
    assert "includes the MinerU runtime" in text
    assert "real `/parse` execution" not in text
    assert "requires a compatible MinerU runtime to be available inside the container image" not in text


def test_docker_command_matchers_allow_wrapped_whitespace():
    sample = "docker   build\n  -t   newsdom-api .\n\n docker run   -p 8000:8000\n newsdom-api"

    assert _contains_docker_build_command(sample)
    assert _contains_docker_run_command(sample)


def test_dockerfile_pattern_helpers_match_pinned_images_and_healthcheck():
    sample = (
        "ARG PYTHON_BASE=python:3.12-slim@sha256:" + "a" * 64 + "\n"
        "ARG UV_IMAGE=ghcr.io/astral-sh/uv@sha256:" + "b" * 64 + "\n"
        "COPY pyproject.toml uv.lock README.md ./\n"
        'HEALTHCHECK --interval=30s \\\n+  CMD python -c "http://127.0.0.1:8000/health"\n'
    )

    assert _contains_pinned_python_base_image(sample)
    assert _contains_pinned_uv_image(sample)
    assert _contains_copy_or_add_reference(sample, "pyproject.toml")
    assert _contains_copy_or_add_reference(sample, "uv.lock")
    assert _contains_healthcheck_path(sample, "/health")


def test_healthcheck_path_matcher_ignores_later_unrelated_health_strings():
    sample = (
        'HEALTHCHECK CMD python -c "http://127.0.0.1:8000/ping"\n'
        'CMD ["echo", "/health"]\n'
    )

    assert not _contains_healthcheck_path(sample, "/health")


def test_container_image_workflow_sets_up_qemu_for_multi_arch_builds():
    data = _load_container_image_workflow()
    image_steps = data["jobs"]["image"]["steps"]
    assert any(
        step.get("uses")
        == "docker/setup-qemu-action@ce360397dd3f832beb865e1373c09c0e9f86d70a"
        for step in image_steps
    )


def test_container_image_workflow_exists_for_ghcr_release():
    data = _load_container_image_workflow()
    assert (
        data["jobs"]["image-nvidia"]["if"]
        == "github.event_name == 'workflow_dispatch' && github.event.inputs.publish_nvidia == 'true'"
    )
    image_steps = data["jobs"]["image"]["steps"]
    image_build_step = _find_step_by_uses(
        image_steps,
        "docker/build-push-action",
    )
    nvidia_steps = data["jobs"]["image-nvidia"]["steps"]
    nvidia_build_step = _find_step_by_uses(
        nvidia_steps,
        "docker/build-push-action",
    )

    assert data["jobs"]["image"]["env"]["REGISTRY"] == "ghcr.io"
    assert image_build_step["with"]["platforms"] == "linux/amd64,linux/arm64"
    assert nvidia_build_step["with"]["file"] == "./Dockerfile.nvidia"
