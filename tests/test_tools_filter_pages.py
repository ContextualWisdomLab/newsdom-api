import json
from pathlib import Path

import pytest

from tools.filter_pages import filter_pages, main


def write_dom(path: Path, pages: object) -> None:
    """Write a minimal NewsDOM-shaped JSON fixture."""
    path.write_text(json.dumps({"source": "fixture", "pages": pages}), encoding="utf-8")


def test_filter_pages_preserves_document_metadata_and_inclusive_order(tmp_path: Path) -> None:
    """Filtering keeps non-page metadata and original page order."""
    json_file = tmp_path / "document.json"
    write_dom(
        json_file,
        [
            {"page_number": 1, "articles": []},
            {"page_number": 2, "articles": []},
            {"page_number": 3, "articles": []},
        ],
    )

    result = filter_pages(json_file, 2, 3)

    assert result["source"] == "fixture"
    assert [page["page_number"] for page in result["pages"]] == [2, 3]


def test_filter_pages_can_return_an_empty_page_set(tmp_path: Path) -> None:
    """A valid range with no matching pages returns an empty list."""
    json_file = tmp_path / "document.json"
    write_dom(json_file, [{"page_number": 1}])

    assert filter_pages(json_file, 4, 5)["pages"] == []


@pytest.mark.parametrize("start_page,end_page", [(0, 1), (1, 0), (3, 2)])
def test_filter_pages_rejects_invalid_ranges(
    tmp_path: Path, start_page: int, end_page: int
) -> None:
    """Page ranges must be positive and ordered."""
    json_file = tmp_path / "document.json"
    write_dom(json_file, [{"page_number": 1}])

    with pytest.raises(ValueError, match="positive integers in ascending order"):
        filter_pages(json_file, start_page, end_page)


@pytest.mark.parametrize(
    "pages",
    [
        {"page_number": 1},
        ["not-an-object"],
        [{"page_number": True}],
        [{"page_number": 0}],
        [{"page_number": "1"}],
        [{}],
    ],
)
def test_filter_pages_rejects_malformed_page_evidence(tmp_path: Path, pages: object) -> None:
    """Malformed page evidence fails closed instead of being silently dropped."""
    json_file = tmp_path / "document.json"
    write_dom(json_file, pages)

    with pytest.raises(ValueError, match="NewsDOM pages"):
        filter_pages(json_file, 1, 2)


def test_filter_pages_rejects_missing_file_and_non_json_extension(tmp_path: Path) -> None:
    """The CLI accepts only an existing JSON file."""
    missing_file = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        filter_pages(missing_file, 1, 2)

    text_file = tmp_path / "document.txt"
    text_file.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match=r"File must be a \.json file"):
        filter_pages(text_file, 1, 2)


def test_filter_pages_requires_a_json_object_root(tmp_path: Path) -> None:
    """A JSON array cannot masquerade as a NewsDOM document."""
    json_file = tmp_path / "document.json"
    json_file.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="NewsDOM JSON root must be an object"):
        filter_pages(json_file, 1, 2)


def test_filter_pages_main_prints_json_and_maps_failures_to_exit_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The command prints valid JSON and gives a bounded nonzero failure."""
    json_file = tmp_path / "document.json"
    write_dom(json_file, [{"page_number": 1}, {"page_number": 2}])

    main([str(json_file), "--start-page", "2", "--end-page", "2"])
    assert json.loads(capsys.readouterr().out)["pages"] == [{"page_number": 2}]

    with pytest.raises(SystemExit) as exc_info:
        main([str(tmp_path / "missing.json"), "--start-page", "1", "--end-page", "2"])
    assert exc_info.value.code == 1
    error = capsys.readouterr().err
    assert "Error: File not found or is not a file:" in error
