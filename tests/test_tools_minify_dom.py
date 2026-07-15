from pathlib import Path
import pytest
from tools.minify_dom import minify_dom, main


def test_minify_dom_valid(tmp_path: Path):
    f = tmp_path / "test.json"
    f.write_text('{\n  "test": 1\n}')
    res = minify_dom(f)
    assert res == '{"test":1}'


def test_minify_dom_not_found():
    with pytest.raises(FileNotFoundError):
        minify_dom(Path("not_found.json"))


def test_main_minify(tmp_path: Path, capsys):
    f = tmp_path / "test.json"
    out = tmp_path / "out.json"
    f.write_text('{"a":1}')

    main([str(f), "--output", str(out)])
    assert out.exists()

    main([str(f)])
    captured = capsys.readouterr()
    assert '{"a":1}' in captured.out


def test_main_minify_error(capsys):
    with pytest.raises(SystemExit):
        main(["not_found.json"])
    captured = capsys.readouterr()
    assert "Error:" in captured.err
