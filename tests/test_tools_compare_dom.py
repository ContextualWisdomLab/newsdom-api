from pathlib import Path
import json
import pytest
from tools.compare_dom import compare_dom, main


def test_compare_dom_valid(tmp_path: Path):
    f1 = tmp_path / "1.json"
    f2 = tmp_path / "2.json"
    d1 = {"pages": [{"articles": [{"images": [{}]}]}]}
    d2 = {"pages": [{"articles": []}]}
    f1.write_text(json.dumps(d1))
    f2.write_text(json.dumps(d2))

    res = compare_dom(f1, f2)
    assert res["pages_diff"] == 0
    assert res["articles_diff"] == 1
    assert res["images_diff"] == 1


def test_compare_dom_not_found():
    with pytest.raises(FileNotFoundError):
        compare_dom(Path("no1.json"), Path("no2.json"))


def test_main_compare(tmp_path: Path, capsys):
    f1 = tmp_path / "1.json"
    f2 = tmp_path / "2.json"
    f1.write_text(json.dumps({"pages": []}))
    f2.write_text(json.dumps({"pages": []}))

    main([str(f1), str(f2)])
    captured = capsys.readouterr()
    assert "Pages Diff: 0" in captured.out


def test_main_compare_error(capsys):
    with pytest.raises(SystemExit):
        main(["no1.json", "no2.json"])
    captured = capsys.readouterr()
    assert "Error:" in captured.err
