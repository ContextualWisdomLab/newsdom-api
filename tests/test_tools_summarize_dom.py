import json
from pathlib import Path
import pytest
from tools.summarize_dom import main, summarize_dom

@pytest.fixture
def sample_json(tmp_path: Path) -> Path:
    data = {
        "pages": [
            {
                "articles": [
                    {
                        "headline": "Test Headline 1",
                        "body_blocks": ["This is a very long body block that should be truncated because it exceeds the max length of fifty characters in this test case."]
                    },
                    {
                        "headline": "Test Headline 2",
                        "body_blocks": ["Short block."]
                    },
                    {
                        "headline": "",
                        "body_blocks": ["Missing headline block."]
                    },
                    {
                        "headline": "Empty Body Blocks",
                        "body_blocks": []
                    }
                ]
            }
        ]
    }
    file_path = tmp_path / "sample.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    return file_path

@pytest.fixture
def empty_json(tmp_path: Path) -> Path:
    data = {"pages": [{"articles": []}]}
    file_path = tmp_path / "empty.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    return file_path

def test_summarize_dom_success(sample_json: Path):
    result = summarize_dom(sample_json, max_length=50)
    assert "Headline: Test Headline 1" in result
    assert "Summary: This is a very long body block that should be trun..." in result
    assert "Headline: Test Headline 2" in result
    assert "Summary: Short block." in result
    assert "Missing headline block." not in result
    assert "Headline: Empty Body Blocks" in result

def test_summarize_dom_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        summarize_dom(tmp_path / "nonexistent.json")

def test_summarize_dom_invalid_extension(tmp_path: Path):
    bad_ext = tmp_path / "bad.txt"
    bad_ext.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a .json file"):
        summarize_dom(bad_ext)

def test_summarize_dom_invalid_json(tmp_path: Path):
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{invalid", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        summarize_dom(bad_json)

def test_main_success(sample_json: Path, capsys: pytest.CaptureFixture[str]):
    main([str(sample_json), "--max-length", "50"])
    captured = capsys.readouterr()
    assert "DOM Summary" in captured.out
    assert "Headline: Test Headline 1" in captured.out

def test_main_empty(empty_json: Path, capsys: pytest.CaptureFixture[str]):
    main([str(empty_json)])
    captured = capsys.readouterr()
    assert "No valid articles found to summarize." in captured.out

def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as exc_info:
        main([str(tmp_path / "missing.json")])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
