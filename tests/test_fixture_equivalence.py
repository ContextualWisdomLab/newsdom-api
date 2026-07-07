import json
from pathlib import Path

from newsdom_api.equivalence import compare_fixture_to_baseline


def test_synthetic_fixture_matches_private_baseline():
    truth_path = Path("tests/fixtures/synthetic_reference.json")
    baseline = json.loads(
        Path("tests/fixtures/private_page_baseline.json").read_text(encoding="utf-8")
    )
    result = compare_fixture_to_baseline(truth_path, baseline)
    assert result["equivalent"] is True


def test_fixture_equivalence_checks_page_aware_structural_metrics(tmp_path: Path):
    truth_path = tmp_path / "truth.json"
    truth_path.write_text(
        json.dumps(
            {
                "column_count": 4,
                "article_count": 4,
                "image_count": 3,
                "ad_count": 2,
                "headline_blocks": 4,
                "vertical_article_ratio": 1.0,
                "page_count": 2,
                "headline_page_coverage": 1.0,
            }
        ),
        encoding="utf-8",
    )
    baseline = {
        "column_count": 4,
        "article_count": 4,
        "image_count": 3,
        "ad_count": 2,
        "headline_blocks": 5,
        "vertical_article_ratio": 1.0,
        "page_count": 2,
        "headline_page_coverage": 1.0,
    }

    result = compare_fixture_to_baseline(truth_path, baseline)

    assert result["checks"]["page_count"] is True
    assert result["checks"]["headline_page_coverage"] is True


def test_fixture_equivalence_fails_when_page_aware_metrics_drift(tmp_path: Path):
    truth_path = tmp_path / "truth.json"
    truth_path.write_text(
        json.dumps(
            {
                "column_count": 4,
                "article_count": 4,
                "image_count": 3,
                "ad_count": 2,
                "headline_blocks": 4,
                "vertical_article_ratio": 1.0,
                "page_count": 1,
                "headline_page_coverage": 0.5,
            }
        ),
        encoding="utf-8",
    )
    baseline = {
        "column_count": 4,
        "article_count": 4,
        "image_count": 3,
        "ad_count": 2,
        "headline_blocks": 5,
        "vertical_article_ratio": 1.0,
        "page_count": 2,
        "headline_page_coverage": 1.0,
    }

    result = compare_fixture_to_baseline(truth_path, baseline)

    assert result["equivalent"] is False
    assert "page_count" in result["failures"]
    assert "headline_page_coverage" in result["failures"]


def test_fixture_equivalence_derives_page_metrics_from_structural_data(tmp_path: Path):
    truth_path = tmp_path / "truth.json"
    truth_path.write_text(
        json.dumps(
            {
                "column_count": 4,
                "article_count": 4,
                "image_count": 3,
                "ad_count": 2,
                "headline_blocks": 4,
                "vertical_article_ratio": 1.0,
                "page_count": 1,
                "headline_page_coverage": 1.0,
                "articles": [
                    {"headline": "Page one headline", "page_number": 1, "vertical": True},
                    {"headline": "", "page_number": 2, "vertical": True},
                ],
                "images": [],
                "ads": [],
            }
        ),
        encoding="utf-8",
    )
    baseline = {
        "column_count": 4,
        "article_count": 2,
        "image_count": 0,
        "ad_count": 0,
        "headline_blocks": 1,
        "vertical_article_ratio": 1.0,
        "page_count": 2,
        "headline_page_coverage": 0.5,
    }

    result = compare_fixture_to_baseline(truth_path, baseline)

    assert result["checks"]["page_count"] is True
    assert result["checks"]["headline_page_coverage"] is True
    assert result["checks"]["headline_blocks"] is True


def test_synthetic_fixture_truth_declares_single_page_metrics(tmp_path: Path):
    from newsdom_api.synthetic import generate_fixture

    _, truth_path = generate_fixture(tmp_path, seed=7)
    truth = json.loads(truth_path.read_text(encoding="utf-8"))

    assert truth["page_count"] == 1
    assert truth["headline_page_coverage"] == 1.0
    assert truth["articles"][0]["page_number"] == 1
