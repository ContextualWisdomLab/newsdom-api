from __future__ import annotations

import json
from pathlib import Path


OPENCODE_CONFIG = Path("opencode.jsonc")
DEFAULT_MODEL = "nvidia-nim/nvidia/llama-3.3-nemotron-super-49b-v1.5"
SMALL_MODEL = "nvidia-nim/meta/llama-3.3-70b-instruct"
NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
FORBIDDEN_FRAGMENTS = (
    "github-models",
    "openai/gpt-5",
    "STRIX_GITHUB_MODELS_TOKEN",
    "COPILOT_GITHUB_TOKEN",
    "https://models.github.ai/inference",
)


def _config_text() -> str:
    return OPENCODE_CONFIG.read_text(encoding="utf-8")


def _config() -> dict[str, object]:
    return json.loads(_config_text())


def test_opencode_configuration_file_exists() -> None:
    assert OPENCODE_CONFIG.exists()


def test_opencode_uses_nvidia_nim_only() -> None:
    config = _config()
    provider = config["provider"]
    nim = provider["nvidia-nim"]

    assert config["model"] == DEFAULT_MODEL
    assert config["small_model"] == SMALL_MODEL
    assert config["enabled_providers"] == ["nvidia-nim"]
    assert list(provider) == ["nvidia-nim"]
    assert nim["npm"] == "@ai-sdk/openai-compatible"
    assert nim["options"]["baseURL"] == NIM_BASE_URL
    assert nim["options"]["apiKey"] == "{env:NVIDIA_API_KEY}"
    assert "nvidia/llama-3.3-nemotron-super-49b-v1.5" in nim["models"]


def test_opencode_rejects_github_models_and_copilot_tokens() -> None:
    text = _config_text()
    for fragment in FORBIDDEN_FRAGMENTS:
        assert fragment not in text, fragment
