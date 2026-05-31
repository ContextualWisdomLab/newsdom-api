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
    return isinstance(headline, str) and bool(headline.strip())


def _derived_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize structural metrics, preferring derivation from structural data when present."""

    metrics = dict(payload)
    articles = payload.get("articles") if isinstance(payload.get("articles"), list) else None
    images = payload.get("images") if isinstance(payload.get("images"), list) else None
    ads = payload.get("ads") if isinstance(payload.get("ads"), list) else None
    pages = payload.get("pages") if isinstance(payload.get("pages"), list) else None

    if articles is not None:
        metrics["article_count"] = len(articles)
        headline_blocks = 0
        vertical_count = 0
        article_page_numbers = set()
        headline_pages = set()

        # Performance: Consolidate multiple iterations over 'articles' into a single pass
        # to reduce list comprehensions and dict lookups overhead.
        for article in articles:
            if isinstance(article, dict):
                has_headline = _article_has_headline(article)
                if has_headline:
                    headline_blocks += 1
                if article.get("vertical"):
                    vertical_count += 1

                page_num = article.get("page_number")
                if isinstance(page_num, int):
                    article_page_numbers.add(page_num)
                    if has_headline:
                        headline_pages.add(page_num)

        metrics["headline_blocks"] = headline_blocks
        if articles:
            metrics["vertical_article_ratio"] = vertical_count / len(articles)

        if article_page_numbers:
            metrics["page_count"] = len(article_page_numbers)
            metrics["headline_page_coverage"] = len(headline_pages) / len(article_page_numbers)

    if images is not None:
        metrics["image_count"] = len(images)

    if ads is not None:
        metrics["ad_count"] = len(ads)

    if pages is not None:
        metrics["page_count"] = len(pages)
        if pages:
            # Performance: Replace max() generator comprehension with a single pass loop
            # to avoid generator instantiation overhead.
            max_col = metrics.get("column_count", 0)
            for page in pages:
                if isinstance(page, dict):
                    c = page.get("column_count")
                    if isinstance(c, int) and c > max_col:
                        max_col = c
            metrics["column_count"] = max_col

    return metrics


def compare_fixture_to_baseline(
    truth_path: Path, baseline: dict[str, Any]
) -> dict[str, Any]:
    """Compare a synthetic fixture metrics file against the committed baseline."""

    truth = _derived_metrics(load_metrics(truth_path))
    baseline_metrics = _derived_metrics(baseline)
    failures: list[str] = []

    checks = {
        "column_count": abs(truth["column_count"] - baseline_metrics["column_count"]) <= 1,
        "article_count": abs(truth["article_count"] - baseline_metrics["article_count"]) <= 1,
        "image_count": abs(truth["image_count"] - baseline_metrics["image_count"]) <= 1,
        "ad_count": abs(truth["ad_count"] - baseline_metrics["ad_count"]) <= 1,
        "headline_blocks": abs(truth["headline_blocks"] - baseline_metrics["headline_blocks"])
        <= 2,
        "vertical_article_ratio": abs(
            truth["vertical_article_ratio"] - baseline_metrics["vertical_article_ratio"]
        )
        <= 0.2,
        "page_count": truth["page_count"] == baseline_metrics["page_count"],
        "headline_page_coverage": abs(
            truth["headline_page_coverage"] - baseline_metrics["headline_page_coverage"]
        )
        <= 0.2,
    }

    for key, passed in checks.items():
        if not passed:
            failures.append(key)

    return {"equivalent": not failures, "failures": failures, "checks": checks}
