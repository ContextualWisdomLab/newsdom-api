from __future__ import annotations

import json
from pathlib import Path

import pytest

import tools.export_jsonl as export_module


def _two_article_document() -> dict[str, object]:
    return {
        "document_id": "doc-atomic",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "section-1",
                        "headline": "First section",
                        "body_blocks": ["First body"],
                    },
                    {
                        "article_id": "section-2",
                        "headline": "Second section",
                        "body_blocks": ["Second body"],
                    },
                ],
            }
        ],
    }


def test_export_preserves_existing_output_when_serialization_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed export must not replace a previously valid artifact."""
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"
    input_file.write_text(json.dumps(_two_article_document()), encoding="utf-8")
    previous_output = '{"document_id":"previous"}\n'
    output_file.write_text(previous_output, encoding="utf-8")

    original_dumps = export_module.json.dumps
    call_count = 0

    def fail_on_second_record(*args: object, **kwargs: object) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise TypeError("synthetic serialization failure")
        return original_dumps(*args, **kwargs)

    monkeypatch.setattr(export_module.json, "dumps", fail_on_second_record)

    with pytest.raises(TypeError, match="synthetic serialization failure"):
        export_module.export_jsonl(input_file, output_file)

    assert output_file.read_text(encoding="utf-8") == previous_output
    assert list(tmp_path.glob(".output.jsonl.*.tmp")) == []
