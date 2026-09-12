import json
from pathlib import Path

import pytest

from tools.extract_headlines import extract_headlines, main


def write_dom(path: Path, pages: object) -> None:
    """Write a minimal NewsDOM-shaped JSON fixture."""
    path.write_text(json.dumps({"pages": pages}), encoding="utf-8")


def test_extract_headlines_preserves_document_order(tmp_path: Path) -> None:
    """Headline extraction preserves page and article order."""
    json_file = tmp_path / "document.json"
    write_dom(
        json_file,
        [
            {"articles": [{"headline": "First"}, {"headline": "Second"}]},
            {"articles": [{"headline": "Third"}]},
        ],
    )

    assert extract_headlines(json_file) == ["First", "Second", "Third"]


def test_extract_headlines_skips_only_empty_strings(tmp_path: Path) -> None:
    """An explicitly empty headline is not emitted."""
    json_file = tmp_path / "document.json"
    write_dom(json_file, [{"articles": [{"headline": ""}, {"headline": "News"}]}])

    assert extract_headlines(json_file) == ["News"]


@pytest.mark.parametrize(
    "pages",
    [
        {"articles": []},
        ["not-an-object"],
        [{"articles": {"headline": "x"}}],
        [{"articles": ["not-an-object"]}],
        [{"articles": [{"headline": 7}]}],
    ],
)
def test_extract_headlines_rejects_malformed_article_evidence(
    tmp_path: Path, pages: object
) -> None:
    """Malformed article evidence fails closed instead of being silently coerced."""
    json_file = tmp_path / "document.json"
    write_dom(json_file, pages)

    with pytest.raises(ValueError, match="NewsDOM"):
        extract_headlines(json_file)


def test_extract_headlines_accepts_missing_headline_field(tmp_path: Path) -> None:
    """Articles without a headline field remain valid and produce no output."""
    json_file = tmp_path / "document.json"
    write_dom(json_file, [{"articles": [{}]}])

    assert extract_headlines(json_file) == []


def test_extract_headlines_rejects_missing_file_non_json_and_non_object_root(
    tmp_path: Path,
) -> None:
    """Only an existing JSON object document is accepted."""
    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        extract_headlines(tmp_path / "missing.json")

    text_file = tmp_path / "document.txt"
    text_file.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match=r"File must be a \.json file"):
        extract_headlines(text_file)

    json_file = tmp_path / "document.json"
    json_file.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="NewsDOM JSON root must be an object"):
        extract_headlines(json_file)


def test_extract_headlines_main_supports_stdout_and_output_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Operators can emit headlines to stdout or an explicitly requested file."""
    json_file = tmp_path / "document.json"
    write_dom(json_file, [{"articles": [{"headline": "One"}, {"headline": "Two"}]}])

    main([str(json_file)])
    assert capsys.readouterr().out == "One\nTwo\n"

    output_file = tmp_path / "headlines.txt"
    main([str(json_file), "--output", str(output_file)])
    captured = capsys.readouterr()
    assert captured.out == f"Extracted 2 headlines to {output_file}\n"
    assert output_file.read_text(encoding="utf-8") == "One\nTwo\n"


def test_extract_headlines_main_writes_empty_output_without_fake_blank_headline(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Zero headlines produce an empty file rather than a synthetic blank record."""
    json_file = tmp_path / "document.json"
    write_dom(json_file, [{"articles": [{}]}])
    output_file = tmp_path / "headlines.txt"

    main([str(json_file), "--output", str(output_file)])

    assert output_file.read_text(encoding="utf-8") == ""
    assert capsys.readouterr().out == f"Extracted 0 headlines to {output_file}\n"


def test_extract_headlines_main_maps_failures_to_exit_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CLI failures are reported on stderr with a nonzero exit status."""
    with pytest.raises(SystemExit) as exc_info:
        main([str(tmp_path / "missing.json")])

    assert exc_info.value.code == 1
    assert "Error: File not found or is not a file:" in capsys.readouterr().err
