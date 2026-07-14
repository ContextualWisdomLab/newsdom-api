import json
import pytest
from tools.filter_dom import filter_dom, main


@pytest.fixture
def sample_json_path(tmp_path):
    data = {
        "pages": [
            {
                "ads": ["ad1"],
                "headers": ["header1"],
                "footers": ["footer1"],
                "articles": [{"images": ["img1", "img2"], "text": "content"}],
            }
        ]
    }
    p = tmp_path / "input.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_filter_dom_all_flags(sample_json_path, tmp_path):
    out_path = tmp_path / "out.json"
    filter_dom(
        sample_json_path,
        out_path,
        remove_ads=True,
        remove_headers=True,
        remove_footers=True,
        remove_images=True,
    )

    data = json.loads(out_path.read_text(encoding="utf-8"))
    page = data["pages"][0]
    assert page["ads"] == []
    assert page["headers"] == []
    assert page["footers"] == []
    assert page["articles"][0]["images"] == []
    assert page["articles"][0]["text"] == "content"


def test_filter_dom_no_flags(sample_json_path, tmp_path):
    out_path = tmp_path / "out.json"
    filter_dom(sample_json_path, out_path)

    data = json.loads(out_path.read_text(encoding="utf-8"))
    page = data["pages"][0]
    assert len(page["ads"]) == 1
    assert len(page["headers"]) == 1
    assert len(page["footers"]) == 1
    assert len(page["articles"][0]["images"]) == 2


def test_filter_dom_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        filter_dom(tmp_path / "missing.json", tmp_path / "out.json")


def test_filter_dom_invalid_extension(tmp_path):
    p = tmp_path / "input.txt"
    p.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Input file must be a .json file."):
        filter_dom(p, tmp_path / "out.json")


def test_filter_dom_invalid_json(tmp_path):
    p = tmp_path / "input.json"
    p.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file:"):
        filter_dom(p, tmp_path / "out.json")


def test_main_success(sample_json_path, tmp_path, capsys):
    out_path = tmp_path / "out.json"
    main([str(sample_json_path), str(out_path), "--remove-ads"])
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["pages"][0]["ads"] == []


def test_main_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path / "missing.json"), str(tmp_path / "out.json")])
    assert exc.value.code == 1
    out, err = capsys.readouterr()
    assert "Error:" in err


def test_filter_dom_no_images_in_article(sample_json_path, tmp_path):
    data = {"pages": [{"articles": [{"text": "content_without_images"}]}]}
    p = tmp_path / "input.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    out_path = tmp_path / "out.json"

    filter_dom(p, out_path, remove_images=True)

    out_data = json.loads(out_path.read_text(encoding="utf-8"))
    assert "images" not in out_data["pages"][0]["articles"][0]
