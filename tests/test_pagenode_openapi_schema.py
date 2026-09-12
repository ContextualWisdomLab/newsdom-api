"""Generated-schema regressions for public response-example contracts."""

from __future__ import annotations

from typing import Any

from newsdom_api.schemas import ImageNode, PageNode


EXPECTED_EXAMPLES: dict[str, list[Any]] = {
    "page_number": [1],
    "width": [595.28],
    "height": [841.89],
    "ads": [["Example advertisement text"]],
    "headers": [["Quarterly report", "2026 Q2"]],
    "footers": [["Confidential"]],
    "page_numbers": [["1", "Page 1"]],
}


def test_pagenode_schema_publishes_typed_plural_examples() -> None:
    """Each documented page example must be plural metadata and a valid field value."""

    properties = PageNode.model_json_schema()["properties"]

    for field_name, examples in EXPECTED_EXAMPLES.items():
        field_schema = properties[field_name]
        assert field_schema["examples"] == examples
        assert "example" not in field_schema

        field_values: dict[str, Any] = {"page_number": 1}
        field_values[field_name] = examples[0]
        PageNode(**field_values)


def test_imagenode_media_type_publishes_a_typed_plural_example() -> None:
    """Image media metadata should use the same standards-based plural example contract."""

    field_schema = ImageNode.model_json_schema()["properties"]["media_type"]

    assert field_schema["examples"] == ["image"]
    assert "example" not in field_schema
    ImageNode(media_type=field_schema["examples"][0], path="page-1/image-1.png")
