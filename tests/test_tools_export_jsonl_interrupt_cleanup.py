"""Lifecycle cleanup contracts for the NewsDOM JSONL exporter."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

export_module = importlib.import_module("tools.export_jsonl")


def test_export_jsonl_cleans_temporary_artifact_on_keyboard_interrupt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A user cancellation must not leak a temporary publication artifact."""
    input_file = tmp_path / "input.json"
    input_file.write_text(
        json.dumps(
            {
                "document_id": "test_doc",
                "pages": [
                    {
                        "page_number": 1,
                        "articles": [
                            {
                                "article_id": "art_1",
                                "headline": "Headline",
                                "body_blocks": ["Block"],
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    output_file = tmp_path / "output.jsonl"
    output_file.write_text("previous publication\n", encoding="utf-8")

    def _interrupt(*_args: object, **_kwargs: object) -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr(export_module.json, "dumps", _interrupt)

    with pytest.raises(KeyboardInterrupt):
        export_module.export_jsonl(input_file, output_file)

    assert output_file.read_text(encoding="utf-8") == "previous publication\n"
    assert list(tmp_path.glob(".output.jsonl.*.tmp")) == []
