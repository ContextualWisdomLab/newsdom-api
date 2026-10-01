import json
import re
from unittest.mock import patch

import pytest

from tools.export_jsonl import export_jsonl, main


def test_export_jsonl_success(tmp_path):
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"
    data = {
        "document_id": "doc123",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {"article_id": "art1", "headline": "Headline 1"},
                    {"article_id": "art2", "headline": "Headline 2"}
                ]
            }
        ]
    }
    input_json.write_text(json.dumps(data), encoding="utf-8")
    export_jsonl(input_json, output_jsonl)
    assert output_jsonl.exists()
    lines = output_jsonl.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    parsed1 = json.loads(lines[0])
    assert parsed1["document_id"] == "doc123"
    assert parsed1["page_number"] == 1
    assert parsed1["article_id"] == "art1"


def test_export_jsonl_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        export_jsonl(tmp_path / "missing.json", tmp_path / "out.jsonl")


def test_export_jsonl_invalid_suffix(tmp_path):
    p = tmp_path / "test.txt"
    p.touch()
    with pytest.raises(ValueError, match="Input file must be a .json file"):
        export_jsonl(p, tmp_path / "out.jsonl")


def test_export_jsonl_invalid_json(tmp_path):
    p = tmp_path / "test.json"
    p.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(p, tmp_path / "out.jsonl")


def test_export_jsonl_non_finite(tmp_path):
    p = tmp_path / "test.json"
    p.write_text("{\"pages\": NaN}", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(p, tmp_path / "out.jsonl")


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("[]", "root must be an object"),
        ('{"pages": {}}', "pages must be an array"),
        ('{"pages": [1]}', "pages[0] must be an object"),
        ('{"pages": [{"articles": {}}]}', "pages[0].articles must be an array"),
        ('{"pages": [{"articles": [1]}]}', "pages[0].articles[0] must be an object"),
    ],
)
def test_export_jsonl_rejects_malformed_newsdom_structure(tmp_path, payload, message):
    p = tmp_path / "test.json"
    p.write_text(payload, encoding="utf-8")
    output = tmp_path / "out.jsonl"

    with pytest.raises(ValueError, match=re.escape(message)):
        export_jsonl(p, output)

    assert not output.exists()



@pytest.mark.parametrize("use_alias", [False, True])
def test_export_jsonl_rejects_input_as_output(tmp_path, use_alias):
    input_json = tmp_path / "input.json"
    original = '{"pages": []}'
    input_json.write_text(original, encoding="utf-8")
    output_jsonl = input_json
    if use_alias:
        output_jsonl = tmp_path / "output.jsonl"
        output_jsonl.hardlink_to(input_json)

    with pytest.raises(ValueError, match="must not refer to the input file"):
        export_jsonl(input_json, output_jsonl)

    assert input_json.read_text(encoding="utf-8") == original


def test_export_jsonl_preserves_existing_output_on_encoding_failure(
    tmp_path, monkeypatch
):
    input_json = tmp_path / "input.json"
    input_json.write_text('{"pages": []}', encoding="utf-8")
    output_jsonl = tmp_path / "output.jsonl"
    original = '{"existing": true}\n'
    output_jsonl.write_text(original, encoding="utf-8")

    def fail_serialization(*_args, **_kwargs):
        raise TypeError("encoding failed")

    monkeypatch.setattr(json, "dumps", fail_serialization)
    input_json.write_text(
        '{"pages": [{"articles": [{"value": 1}]}]}',
        encoding="utf-8",
    )

    with pytest.raises(TypeError, match="encoding failed"):
        export_jsonl(input_json, output_jsonl)

    assert output_jsonl.read_text(encoding="utf-8") == original


def test_export_jsonl_creates_output_parent(tmp_path):
    input_json = tmp_path / "input.json"
    input_json.write_text('{"pages": []}', encoding="utf-8")
    output_jsonl = tmp_path / "nested" / "output.jsonl"

    export_jsonl(input_json, output_jsonl)

    assert output_jsonl.read_text(encoding="utf-8") == ""

def test_main_success(tmp_path, capsys):
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"
    input_json.write_text("{\"pages\": []}", encoding="utf-8")
    with patch("sys.argv", ["export_jsonl.py", str(input_json), str(output_jsonl)]):
        main()
    captured = capsys.readouterr()
    assert "successfully written" in captured.out


def test_main_exception(tmp_path, capsys):
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"
    input_json.write_text("{\"pages\": []}", encoding="utf-8")
    with patch("sys.argv", ["export_jsonl.py", str(input_json), str(output_jsonl)]):
        with patch("tools.export_jsonl.export_jsonl", side_effect=OSError("test err")):
            with pytest.raises(SystemExit) as exc:
                main()
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "test err" in captured.err
