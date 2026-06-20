import json
from pathlib import Path


def _extract_first_json_block(text: str) -> str:
    marker = "```json\n"
    start = text.index(marker) + len(marker)
    end = text.index("\n```", start)
    return text[start:end]


def _has_blank_line_after_heading(text: str, heading: str) -> bool:
    return f"{heading}\n\n" in text


def test_api_reference_examples_are_consistent_and_valid_json():
    text = Path("manual/api-reference.md").read_text(encoding="utf-8")
    assert "#### Python 클라이언트 예제 (requests)" in text
    payload = json.loads(_extract_first_json_block(text))
    assert payload["pages"][0]["articles"][0]["images"][0]["bbox"]["x0"] == 120.0


def test_api_reference_uses_current_runtime_commands_and_temp_file_contract() -> None:
    text = Path("manual/api-reference.md").read_text(encoding="utf-8")

    assert "uv run uvicorn --app-dir src newsdom_api.main:app --reload" in text
    assert "임시 디렉토리" in text
    assert "응답 후 정리됩니다" in text
    assert "uvicorn newsdom_api.main:app --reload" not in text


def test_api_reference_documents_sanitized_parse_failure_semantics() -> None:
    text = Path("manual/api-reference.md").read_text(encoding="utf-8")

    for expected in [
        "503 Service Unavailable",
        "MinerU runtime unavailable",
        "502 Bad Gateway",
        "MinerU output was incomplete",
    ]:
        assert expected in text


def test_development_doc_uses_tree_wording():
    text = Path("manual/development.md").read_text(encoding="utf-8")
    assert "트리 구조의 DOM" in text


def test_development_doc_adds_blank_line_after_branch_rules_heading() -> None:
    text = Path("manual/development.md").read_text(encoding="utf-8")
    assert _has_blank_line_after_heading(text, "### 🌿 브랜치 규칙")


def test_installation_doc_uses_quoted_extras_and_clear_python_wording():
    text = Path("manual/installation.md").read_text(encoding="utf-8")
    assert "Required: `>=3.10, <3.14`" in text
    for token in ("python3.10", "지원 범위", "인터프리터"):
        assert token in text
    assert "python3.10 -m venv .venv" in text
    assert 'pip install -e ".[dev]"' in text
    assert 'pip install "mineru[pipeline]==3.0.9"' in text


def test_installation_doc_includes_manual_api_healthcheck_commands():
    text = Path("manual/installation.md").read_text(encoding="utf-8")
    for token in [
        "python -m uvicorn",
        "--app-dir src",
        "newsdom_api.main:app",
        "--host 0.0.0.0",
        "--port 8000",
        "--reload",
    ]:
        assert token in text

    for token in ["curl", "127.0.0.1:8000/health", "HTTP 200"]:
        assert token in text
