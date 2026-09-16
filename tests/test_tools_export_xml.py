import json
from pathlib import Path
from unittest.mock import patch

import pytest
from tools.export_xml import export_xml, main

@pytest.fixture
def sample_json(tmp_path: Path) -> Path:
    data = {
        "document_id": "test_doc",
        "pages": [
            {
                "page_number": 1,
                "headers": ["Header 1"],
                "articles": [
                    {
                        "article_id": "art_1",
                        "headline": "Test Headline",
                        "body_blocks": ["Block 1", "Block 2"],
                        "captions": [{"text": "Cap 1"}, "Cap 2"],
                        "footnotes": [{"text": "Fn 1"}, "Fn 2"],
                        "images": [
                            {
                                "path": "img.png",
                                "captions": [{"text": "Img Cap 1"}, "Img Cap 2"],
                                "footnotes": [{"text": "Img Fn 1"}, "Img Fn 2"],
                            },
                            "invalid_image_type",
                        ]
                    },
                    "invalid_article_type"
                ],
                "ads": ["Ad 1"],
                "footers": ["Footer 1"],
            },
            "invalid_page_type"
        ]
    }
    json_path = tmp_path / "test.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path

def test_export_xml_success(sample_json: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "output.xml"
    export_xml(sample_json, output_path)
    assert output_path.exists()
    xml_content = output_path.read_text(encoding="utf-8")
    assert '<Document id="test_doc">' in xml_content
    assert '<Page number="1">' in xml_content
    assert '<Header>Header 1</Header>' in xml_content
    assert '<Article id="art_1">' in xml_content
    assert '<Headline>Test Headline</Headline>' in xml_content
    assert '<BodyBlock>Block 1</BodyBlock>' in xml_content
    assert '<BodyBlock>Block 2</BodyBlock>' in xml_content
    assert '<Image path="img.png">' in xml_content
    assert '<Caption>Img Cap 1</Caption>' in xml_content
    assert '<Caption>Img Cap 2</Caption>' in xml_content
    assert '<Footnote>Img Fn 1</Footnote>' in xml_content
    assert '<Footnote>Img Fn 2</Footnote>' in xml_content
    assert '<Caption>Cap 1</Caption>' in xml_content
    assert '<Caption>Cap 2</Caption>' in xml_content
    assert '<Footnote>Fn 1</Footnote>' in xml_content
    assert '<Footnote>Fn 2</Footnote>' in xml_content
    assert '<Ad>Ad 1</Ad>' in xml_content
    assert '<Footer>Footer 1</Footer>' in xml_content

def test_export_xml_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="File not found"):
        export_xml(tmp_path / "missing.json", tmp_path / "out.xml")

def test_export_xml_invalid_extension(tmp_path: Path) -> None:
    invalid_file = tmp_path / "test.txt"
    invalid_file.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Input file must be a .json file."):
        export_xml(invalid_file, tmp_path / "out.xml")

def test_export_xml_invalid_json(tmp_path: Path) -> None:
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{bad", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file:"):
        export_xml(bad_json, tmp_path / "out.xml")

def test_main_success(sample_json: Path, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    output_path = tmp_path / "out_main.xml"
    main([str(sample_json), str(output_path)])
    assert output_path.exists()
    captured = capsys.readouterr()
    assert "XML successfully written to" in captured.out

def test_main_failure(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    missing_file = tmp_path / "missing.json"
    output_path = tmp_path / "out_main.xml"
    with pytest.raises(SystemExit) as excinfo:
        main([str(missing_file), str(output_path)])
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error exporting XML:" in captured.err
