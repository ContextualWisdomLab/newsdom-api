"""Generated-schema regressions for the public ``PageNode`` response contract."""

from __future__ import annotations

from typing import Any

from newsdom_api.schemas import PageNode


EXPECTED_EXAMPLES: dict[str, list[Any]] = {
    "width": [595.28],
    "height": [841.89],
    "ads": [["Example advertisement text"]],
    "headers": [["Quarterly report", "2026 Q2"]],
    "footers": [["Confidential"]],
    "page_numbers": [["1", "Page 1"]],
}


def test_pagenode_schema_publishes_typed_plural_examples() -> None:
    """Each documented example must be plural metadata and a valid field value."""

    properties = PageNode.model_json_schema()["properties"]

    for field_name, examples in EXPECTED_EXAMPLES.items():
        field_schema = properties[field_name]
        assert field_schema["examples"] == examples
        assert "example" not in field_schema

        PageNode(page_number=1, **{field_name: examples[0]})
