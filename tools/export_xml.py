from __future__ import annotations

import argparse
import json
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom


def export_xml(json_path: Path, output_path: Path) -> None:
    """Export NewsDOM JSON to an XML file using atomic writes."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    root = ET.Element("NewsDOM")

    document_id = data.get("document_id", "Unknown Document")
    doc_el = ET.SubElement(root, "Document")
    doc_el.set("id", str(document_id))

    pages = data.get("pages", [])
    for page in pages:
        if not isinstance(page, dict):
            continue
        page_el = ET.SubElement(doc_el, "Page")
        page_el.set("number", str(page.get("page_number", "Unknown")))

        for header in page.get("headers", []):
            h_el = ET.SubElement(page_el, "Header")
            h_el.text = str(header)

        for article in page.get("articles", []):
            if not isinstance(article, dict):
                continue
            article_el = ET.SubElement(page_el, "Article")
            article_el.set("id", str(article.get("article_id", "Unknown")))

            hl_el = ET.SubElement(article_el, "Headline")
            hl_el.text = str(article.get("headline", ""))

            for block in article.get("body_blocks", []):
                b_el = ET.SubElement(article_el, "BodyBlock")
                b_el.text = str(block)

            for img in article.get("images", []):
                if not isinstance(img, dict):
                    continue
                img_el = ET.SubElement(article_el, "Image")
                img_el.set("path", str(img.get("path", "")))

                for cap in img.get("captions", []):
                    cap_el = ET.SubElement(img_el, "Caption")
                    cap_el.text = str(cap.get("text", "") if isinstance(cap, dict) else cap)
                for fn in img.get("footnotes", []):
                    fn_el = ET.SubElement(img_el, "Footnote")
                    fn_el.text = str(fn.get("text", "") if isinstance(fn, dict) else fn)

            for cap in article.get("captions", []):
                cap_el = ET.SubElement(article_el, "Caption")
                cap_el.text = str(cap.get("text", "") if isinstance(cap, dict) else cap)

            for fn in article.get("footnotes", []):
                fn_el = ET.SubElement(article_el, "Footnote")
                fn_el.text = str(fn.get("text", "") if isinstance(fn, dict) else fn)

        for ad in page.get("ads", []):
            ad_el = ET.SubElement(page_el, "Ad")
            ad_el.text = str(ad)

        for footer in page.get("footers", []):
            f_el = ET.SubElement(page_el, "Footer")
            f_el.text = str(footer)

    xml_str = ET.tostring(root, encoding="unicode")
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(indent="  ")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, dir=output_path.parent) as tf:
        tf.write(pretty_xml)
        temp_name = tf.name

    Path(temp_name).replace(output_path)


def main(argv: list[str] | None = None) -> None:
    """Run the JSON-to-XML export CLI."""
    parser = argparse.ArgumentParser(description="Export a NewsDOM JSON file to XML.")
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument("output", type=Path, help="Path to write the XML output file.")

    args = parser.parse_args(argv)

    try:
        export_xml(args.input, args.output)
        print(f"XML successfully written to {args.output}")
    except Exception as exc:
        print(f"Error exporting XML: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
