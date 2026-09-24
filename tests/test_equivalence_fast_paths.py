from collections import Counter
from typing import Any

import pytest

from newsdom_api.equivalence import _article_has_headline, _derived_metrics


class CountingPayload(dict[str, Any]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.get_calls: Counter[str] = Counter()

    def get(self, key: str, default: Any = None) -> Any:
        self.get_calls[key] += 1
        return super().get(key, default)


def test_derived_metrics_reads_each_structural_collection_once() -> None:
    payload = CountingPayload(
        articles=[],
        images=[],
        ads=[],
        pages=[],
    )

    _derived_metrics(payload)

    assert payload.get_calls == Counter(
        {
            "articles": 1,
            "images": 1,
            "ads": 1,
            "pages": 1,
        }
    )


@pytest.mark.parametrize(
    ("headline", "expected"),
    [
        (None, False),
        (1, False),
        ("", False),
        (" \t\r\n", False),
        ("\u00a0\u2003\u3000", False),
        (" \u2003headline\u3000 ", True),
        ("📰", True),
        ("\u200b", True),
    ],
)
def test_article_headline_presence_preserves_text_semantics(
    headline: Any, expected: bool
) -> None:
    assert _article_has_headline({"headline": headline}) is expected
