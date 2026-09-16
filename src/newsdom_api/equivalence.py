"""Compare synthetic fixture metrics against the committed structural baseline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_metrics(path: Path) -> dict[str, Any]:
    """Load a JSON metrics file from disk using UTF-8 encoding."""

    return json.loads(path.read_text(encoding="utf-8"))


def _article_has_headline(article: dict[str, Any]) -> bool:
    """Return whether an article-like structure declares a headline."""

    headline_present = article.get("headline_present")
    if isinstance(headline_present, bool):
        return headline_present

    headline = article.get("headline")
    # ⚡ Bolt: Early truthiness return to avoid allocating a stripped string when it is empty
    return isinstance(headline, str) and bool(headline) and not headline.isspace()


def _process_articles(metrics: dict[str, Any], articles: list[Any]) -> None:
    """Process articles and update metrics."""
    metrics.setdefault("article_count", len(articles))
    metrics.setdefault("vertical_article_ratio", 0.0)
    metrics.setdefault("headline_page_coverage", 0.0)

    metrics["article_count"] = len(articles)
    headline_blocks = 0
    vertical_count = 0
    article_page_numbers: set[int] = set()
    headline_page_numbers: set[int] = set()

    for article in articles:
        if not isinstance(article, dict):
            continue

        has_headline = _article_has_headline(article)
        if has_headline:
            headline_blocks += 1

        if bool(article.get("vertical")):
            vertical_count += 1

        page_number = article.get("page_number")
        if isinstance(page_number, int):
            article_page_numbers.add(page_number)
            if has_headline:
                headline_page_numbers.add(page_number)

    metrics["headline_blocks"] = headline_blocks
    if articles:
        metrics["vertical_article_ratio"] = vertical_count / len(articles)

    if article_page_numbers:
        metrics["page_count"] = len(article_page_numbers)
        metrics["headline_page_coverage"] = len(headline_page_numbers) / len(
            article_page_numbers
        )


def _process_images(metrics: dict[str, Any], images: list[Any]) -> None:
    """Process images and update metrics."""
    metrics["image_count"] = len(images)


def _process_ads(metrics: dict[str, Any], ads: list[Any]) -> None:
    """Process ads and update metrics."""
    metrics["ad_count"] = len(ads)


def _process_pages(metrics: dict[str, Any], pages: list[Any]) -> None:
    """Process pages and update metrics."""
    metrics["page_count"] = len(pages)
    metrics.setdefault("column_count", 0)
    if pages:
        max_col = metrics.get("column_count", 0)
        found_column_count = False
        for page in pages:
            if not isinstance(page, dict):
                continue
            column_count = page.get("column_count")
            if not isinstance(column_count, int):
                continue
            if not found_column_count or column_count > max_col:
                max_col = column_count
                found_column_count = True
        metrics["column_count"] = max_col


def _derived_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize structural metrics, preferring derivation from structural data when present."""

    metrics = dict(payload)
    articles = (
        payload.get("articles") if isinstance(payload.get("articles"), list) else None
    )
    images = payload.get("images") if isinstance(payload.get("images"), list) else None
    ads = payload.get("ads") if isinstance(payload.get("ads"), list) else None
    pages = payload.get("pages") if isinstance(payload.get("pages"), list) else None

    if articles is not None:
        _process_articles(metrics, articles)

    if images is not None:
        _process_images(metrics, images)

    if ads is not None:
        _process_ads(metrics, ads)

    if pages is not None:
        _process_pages(metrics, pages)

    return metrics


def compare_fixture_to_baseline(
    truth_path: Path, baseline: dict[str, Any]
) -> dict[str, Any]:
    """Compare a synthetic fixture metrics file against the committed baseline."""

    truth = _derived_metrics(load_metrics(truth_path))
    baseline_metrics = _derived_metrics(baseline)
    failures: list[str] = []

    checks = {
        "column_count": abs(truth.get("column_count", 0) - baseline_metrics.get("column_count", 0))
        <= 1,
        "article_count": abs(truth.get("article_count", 0) - baseline_metrics.get("article_count", 0))
        <= 1,
        "image_count": abs(truth.get("image_count", 0) - baseline_metrics.get("image_count", 0)) <= 1,
        "ad_count": abs(truth.get("ad_count", 0) - baseline_metrics.get("ad_count", 0)) <= 1,
        "headline_blocks": abs(
            truth.get("headline_blocks", 0) - baseline_metrics.get("headline_blocks", 0)
        )
        <= 2,
        "vertical_article_ratio": abs(
            truth.get("vertical_article_ratio", 0.0) - baseline_metrics.get("vertical_article_ratio", 0.0)
        )
        <= 0.2,
        "page_count": truth.get("page_count", 0) == baseline_metrics.get("page_count", 0),
        "headline_page_coverage": abs(
            truth.get("headline_page_coverage", 0.0) - baseline_metrics.get("headline_page_coverage", 0.0)
        )
        <= 0.2,
    }

    for key, passed in checks.items():
        if not passed:
            failures.append(key)

    return {"equivalent": not failures, "failures": failures, "checks": checks}
