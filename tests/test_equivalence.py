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
    assert _article_has_headline({"headline_present": False, "headline": "headline"}) is False
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
