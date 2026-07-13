"""Fuzz and smoke-test the equivalence metrics normalization boundary.

``_derived_metrics`` is the untrusted-input normalizer in the equivalence
comparator: it takes a JSON payload loaded from disk (a metrics file or a
structural fixture) and derives structural counts from it. Because those
payloads are not schema-validated before reaching this function, it must
tolerate *arbitrary* JSON objects without raising, while keeping the counts it
derives internally consistent with the structural lists it read.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from newsdom_api.equivalence import _derived_metrics


def _check_invariants(payload: dict[str, Any], metrics: dict[str, Any]) -> None:
    """Assert the derived metrics stay consistent with the structural input."""

    assert isinstance(metrics, dict)
    # Normalization never drops caller-provided keys.
    assert set(payload).issubset(metrics)

    articles = payload.get("articles")
    if isinstance(articles, list):
        assert metrics["article_count"] == len(articles)
        assert metrics["headline_blocks"] >= 0
        if articles:
            assert 0.0 <= metrics["vertical_article_ratio"] <= 1.0

    images = payload.get("images")
    if isinstance(images, list):
        assert metrics["image_count"] == len(images)

    ads = payload.get("ads")
    if isinstance(ads, list):
        assert metrics["ad_count"] == len(ads)

    pages = payload.get("pages")
    if isinstance(pages, list):
        assert metrics["page_count"] == len(pages)


def exercise_equivalence(raw_bytes: bytes) -> None:
    """Normalize arbitrary decoded JSON objects and assert invariants hold."""

    try:
        decoded = raw_bytes.decode("utf-8", errors="ignore")
        candidate = json.loads(decoded)
    except json.JSONDecodeError:
        return

    if not isinstance(candidate, dict):
        return

    metrics = _derived_metrics(candidate)
    _check_invariants(candidate, metrics)


def _run_smoke(seed_path: Path) -> None:
    """Run one deterministic normalization pass from a known corpus seed."""

    sample = json.loads(seed_path.read_text(encoding="utf-8"))
    if isinstance(sample, dict):
        _check_invariants(sample, _derived_metrics(sample))


def main(argv: list[str] | None = None) -> int:
    """Run either deterministic smoke mode or Atheris fuzz mode."""

    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--smoke", type=Path)
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args, forwarded = parser.parse_known_args(raw_argv)

    if forwarded[:1] == ["--"]:
        forwarded = forwarded[1:]

    if args.smoke is not None:
        if forwarded:
            parser.error(f"unrecognized arguments: {' '.join(forwarded)}")
        _run_smoke(args.smoke)
        return 0

    import atheris

    def test_one_input(data: bytes) -> None:
        exercise_equivalence(data)

    atheris.Setup([sys.argv[0], *forwarded], test_one_input)
    atheris.Fuzz()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
