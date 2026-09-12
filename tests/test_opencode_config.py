from __future__ import annotations

import json
from pathlib import Path


OPENCODE_CONFIG = Path("opencode.jsonc")
DEFAULT_MODEL = "nvidia-nim/nvidia/nemotron-3-ultra-550b-a55b"
SMALL_MODEL = "nvidia-nim/nvidia/nemotron-3-super-120b-a12b"
ULTRA_MODEL_ID = "nvidia/nemotron-3-ultra-550b-a55b"
SUPER_MODEL_ID = "nvidia/nemotron-3-super-120b-a12b"
NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL_LIMIT = {"context": 131072, "output": 32768}
FORBIDDEN_FRAGMENTS = (
    "github-models",
    "openai/gpt-5",
    "STRIX_GITHUB_MODELS_TOKEN",
    "COPILOT_GITHUB_TOKEN",
    "https://models.github.ai/inference",
    "reasoningEffort",
)


def _config_text() -> str:
    return OPENCODE_CONFIG.read_text(encoding="utf-8")


def _config() -> dict[str, object]:
    return json.loads(_config_text())


def _assert_nemotron_model(model: object) -> None:
    assert isinstance(model, dict)
    assert model["tool_call"] is True
    assert model["reasoning"] is True
    assert model["limit"] == MODEL_LIMIT
    assert "options" not in model


def test_opencode_configuration_file_exists() -> None:
    assert OPENCODE_CONFIG.exists()


def test_opencode_uses_nvidia_nim_only() -> None:
    config = _config()
    provider = config["provider"]
    nim = provider["nvidia-nim"]
    models = nim["models"]

    assert config["model"] == DEFAULT_MODEL
    assert config["small_model"] == SMALL_MODEL
    assert config["enabled_providers"] == ["nvidia-nim"]
    assert list(provider) == ["nvidia-nim"]
    assert nim["npm"] == "@ai-sdk/openai-compatible"
    assert nim["options"]["baseURL"] == NIM_BASE_URL
    assert nim["options"]["apiKey"] == "{env:NVIDIA_API_KEY}"
    assert list(models) == [ULTRA_MODEL_ID, SUPER_MODEL_ID]
    _assert_nemotron_model(models[ULTRA_MODEL_ID])
    _assert_nemotron_model(models[SUPER_MODEL_ID])


def test_opencode_rejects_github_models_and_copilot_tokens() -> None:
    text = _config_text()
    for fragment in FORBIDDEN_FRAGMENTS:
        assert fragment not in text, fragment


def test_contributing_documents_nvidia_nim_api_key_binding() -> None:
    text = Path("CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "NVIDIA NIM only" in text
    assert 'export NVIDIA_API_KEY="${NVIDIA_NIM_API_KEY}"' in text
    assert "STRIX_GITHUB_MODELS_TOKEN" in text
    assert "COPILOT_GITHUB_TOKEN" in text
