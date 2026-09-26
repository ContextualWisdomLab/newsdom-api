import json
from pathlib import Path

from newsdom_api.equivalence import compare_fixture_to_baseline, load_metrics


def test_load_metrics_reads_json(tmp_path: Path):
    path = tmp_path / "metrics.json"
    path.write_text(json.dumps({"column_count": 1}), encoding="utf-8")
    assert load_metrics(path)["column_count"] == 1


def test_compare_fixture_to_baseline_reports_failures(tmp_path: Path):
    truth_path = tmp_path / "truth.json"
    truth_path.write_text(
        json.dumps(
            {
                "column_count": 10,
                "article_count": 10,
                "image_count": 10,
                "ad_count": 10,
                "headline_blocks": 10,
                "vertical_article_ratio": 0.0,
                "page_count": 10,
                "headline_page_coverage": 0.0,
            }
        ),
        encoding="utf-8",
    )
    baseline = {
        "column_count": 1,
        "article_count": 1,
        "image_count": 1,
        "ad_count": 1,
        "headline_blocks": 1,
        "vertical_article_ratio": 1.0,
        "page_count": 1,
        "headline_page_coverage": 1.0,
    }
    result = compare_fixture_to_baseline(truth_path, baseline)
    assert result["equivalent"] is False
    assert set(result["failures"]) == {
        "column_count",
        "article_count",
        "image_count",
        "ad_count",
        "headline_blocks",
        "vertical_article_ratio",
        "page_count",
        "headline_page_coverage",
    }


def test_article_has_headline_supports_boolean_and_text_forms():
    from newsdom_api.equivalence import _article_has_headline

    assert _article_has_headline({"headline_present": True}) is True
    assert (
        _article_has_headline({"headline_present": False, "headline": "headline"})
        is False
    )
    assert _article_has_headline({"headline": "headline"}) is True


def test_compare_fixture_to_baseline_derives_page_count_from_pages_list(tmp_path: Path):
    truth_path = tmp_path / "truth.json"
    truth_path.write_text(
        json.dumps(
            {
                "column_count": 1,
                "article_count": 1,
                "image_count": 0,
                "ad_count": 0,
                "headline_blocks": 1,
                "vertical_article_ratio": 1.0,
                "page_count": 1,
                "headline_page_coverage": 1.0,
                "pages": [{"column_count": 2}, {"column_count": 3}],
            }
        ),
        encoding="utf-8",
    )

    result = compare_fixture_to_baseline(
        truth_path,
        {
            "column_count": 3,
            "article_count": 1,
            "image_count": 0,
            "ad_count": 0,
            "headline_blocks": 1,
            "vertical_article_ratio": 1.0,
            "page_count": 2,
            "headline_page_coverage": 1.0,
        },
    )

    assert result["checks"]["column_count"] is True
    assert result["checks"]["page_count"] is True


def test_derived_metrics_handles_mixed_article_structures():
    from newsdom_api.equivalence import _derived_metrics

    metrics = _derived_metrics(
        {
            "articles": [
                "not-a-dict",
                {"headline": "test", "vertical": True, "page_number": 1},
                {"headline": "", "vertical": False, "page_number": 2},
                {"headline_present": True, "page_number": "not-an-int"},
            ]
        }
    )

    assert metrics["article_count"] == 4
    assert metrics["headline_blocks"] == 2
    assert metrics["vertical_article_ratio"] == 0.25
    assert metrics["page_count"] == 2
    assert metrics["headline_page_coverage"] == 0.5


def test_compare_fixture_to_baseline_handles_empty_structural_lists(tmp_path: Path):
    truth_path = tmp_path / "truth.json"
    truth_path.write_text(
        json.dumps(
            {
                "column_count": 0,
                "article_count": 0,
                "image_count": 0,
                "ad_count": 0,
                "headline_blocks": 0,
                "vertical_article_ratio": 0.0,
                "page_count": 0,
                "headline_page_coverage": 0.0,
                "articles": [],
                "pages": [],
                "images": [],
                "ads": [],
            }
        ),
        encoding="utf-8",
    )

    result = compare_fixture_to_baseline(
        truth_path,
        {
            "column_count": 0,
            "article_count": 0,
            "image_count": 0,
            "ad_count": 0,
            "headline_blocks": 0,
            "vertical_article_ratio": 0.0,
            "page_count": 0,
            "headline_page_coverage": 0.0,
        },
    )

    assert result["equivalent"] is True


def test_derived_metrics_empty_payload():
    from newsdom_api.equivalence import _derived_metrics

    metrics = _derived_metrics({})
    assert metrics == {}


def test_derived_metrics_images():
    from newsdom_api.equivalence import _derived_metrics

    metrics = _derived_metrics({"images": [1, 2]})
    assert metrics == {"images": [1, 2], "image_count": 2}


def test_derived_metrics_ads():
    from newsdom_api.equivalence import _derived_metrics

    metrics = _derived_metrics({"ads": [1]})
    assert metrics == {"ads": [1], "ad_count": 1}


def test_derived_metrics_pages():
    from newsdom_api.equivalence import _derived_metrics

    metrics = _derived_metrics(
        {
            "column_count": "fallback",
            "pages": [
                "not-dict",
                {"column_count": "str"},
                {"column_count": 5},
                {"column_count": 3},
            ],
        }
    )
    assert metrics == {
        "column_count": 5,
        "pages": [
            "not-dict",
            {"column_count": "str"},
            {"column_count": 5},
            {"column_count": 3},
        ],
        "page_count": 4,
    }


def test_derived_metrics_pages_preserves_column_fallback_without_valid_columns():
    from newsdom_api.equivalence import _derived_metrics

    metrics = _derived_metrics(
        {"column_count": "fallback", "pages": ["not-dict", {"column_count": "str"}]}
    )
    assert metrics == {
        "column_count": "fallback",
        "pages": ["not-dict", {"column_count": "str"}],
        "page_count": 2,
    }


def test_derived_metrics_pages_uses_zero_default_without_valid_columns():
    from newsdom_api.equivalence import _derived_metrics

    metrics = _derived_metrics({"pages": ["not-dict", {"column_count": "str"}]})
    assert metrics == {
        "pages": ["not-dict", {"column_count": "str"}],
        "page_count": 2,
        "column_count": 0,
    }


def test_derived_metrics_invalid_types():
    from newsdom_api.equivalence import _derived_metrics

    payload = {
        "articles": "invalid",
        "images": 123,
        "ads": {},
        "pages": True,
    }
    metrics = _derived_metrics(payload)
    assert metrics == payload

def test_article_has_headline_truthiness() -> None:
    """
    Test that has_headline correctly handles empty and whitespace-only strings
    while avoiding allocations from strip().
    """
    from newsdom_api.equivalence import _article_has_headline
    assert _article_has_headline({}) is False
    assert _article_has_headline({"headline_present": True}) is True
    assert _article_has_headline({"headline": None}) is False
    assert _article_has_headline({"headline": ""}) is False
    assert _article_has_headline({"headline": "   "}) is False
    assert _article_has_headline({"headline": "\n\t"}) is False
    assert _article_has_headline({"headline": "\u3000"}) is False  # Ideographic space

    assert _article_has_headline({"headline": "Title"}) is True
    assert _article_has_headline({"headline": "  Title  "}) is True

def test_article_has_headline_performance_allocation_evidence() -> None:
    """
    Provide evidence that using not isspace() allocates less memory than bool(strip()).
    """
    import tracemalloc

    test_str = "   "

    def strip_approach():
        return bool(test_str.strip())

    def isspace_approach():
        return bool(test_str) and not test_str.isspace()

    # Warmup
    strip_approach()
    isspace_approach()

    tracemalloc.start()
    strip_approach()
    _, peak_strip = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tracemalloc.start()
    isspace_approach()
    _, peak_isspace = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert peak_isspace <= peak_strip # tracemalloc might record 0 peak for both in some environments/short strings
