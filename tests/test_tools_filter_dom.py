import json
import pytest
from pathlib import Path
from tools.filter_dom import filter_dom, main


def test_filter_dom_removes_elements(tmp_path: Path):
    input_file = tmp_path / "input.json"
    data = {
        "pages": [
            {
                "ads": ["Ad 1"],
                "headers": ["Header 1"],
                "footers": ["Footer 1"],
                "articles": [{"headline": "H1", "images": [{"path": "img1.png"}]}],
            }
        ]
    }
    input_file.write_text(json.dumps(data))

    result = filter_dom(
        input_file,
        remove_ads=True,
        remove_images=True,
        remove_headers=True,
        remove_footers=True,
    )

    page = result["pages"][0]
    assert page["ads"] == []
    assert page["headers"] == []
    assert page["footers"] == []
    assert page["articles"][0]["images"] == []


def test_filter_dom_partial_removal(tmp_path: Path):
    input_file = tmp_path / "input.json"
    data = {"pages": [{"articles": [{"headline": "H1"}]}]}
    input_file.write_text(json.dumps(data))

    result = filter_dom(
        input_file,
        remove_ads=True,
        remove_images=True,
    )

    page = result["pages"][0]
    assert "ads" not in page
    assert "images" not in page["articles"][0]


def test_filter_dom_not_a_file(tmp_path: Path):
    non_existent = tmp_path / "non_existent.json"
    with pytest.raises(FileNotFoundError):
        filter_dom(non_existent)


def test_filter_dom_wrong_extension(tmp_path: Path):
    txt_file = tmp_path / "input.txt"
    txt_file.write_text("{}")
    with pytest.raises(ValueError, match="must be a .json file"):
        filter_dom(txt_file)


def test_main_with_output(tmp_path: Path, capsys):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    data = {"pages": [{"ads": ["Ad 1"]}]}
    input_file.write_text(json.dumps(data))

    main([str(input_file), "-o", str(output_file), "--remove-ads"])

    assert output_file.is_file()
    result = json.loads(output_file.read_text())
    assert result["pages"][0]["ads"] == []


def test_main_without_output(tmp_path: Path, capsys):
    input_file = tmp_path / "input.json"
    data = {"pages": [{"ads": ["Ad 1"]}]}
    input_file.write_text(json.dumps(data))

    main([str(input_file), "--remove-ads"])

    captured = capsys.readouterr()
    assert '"ads": []' in captured.out


def test_main_exception(tmp_path: Path, capsys):
    non_existent = tmp_path / "non_existent.json"
    with pytest.raises(SystemExit) as exc:
        main([str(non_existent)])

    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
