"""Fuzz and smoke-test the ParseResponse DTO validation boundary.

``ParseResponse`` is the untrusted-input boundary the API deserializes into:
any object that reaches ``model_validate`` originates from parser output or a
client payload. The contract we assert is the standard parser contract — for
*arbitrary* decoded JSON the validator must either return a well-formed model
or raise ``pydantic.ValidationError``. Any other exception type (TypeError,
RecursionError leaking out, AttributeError, ...) is a defect worth a crash.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from newsdom_api.schemas import ParseResponse


def exercise_schema(raw_bytes: bytes) -> None:
    """Validate arbitrary decoded JSON against ParseResponse.

    Invariant: validation either succeeds (and the model round-trips through
    ``model_dump`` back into an equivalent, re-validatable model) or raises
    ``pydantic.ValidationError``. Escaping any other exception is a bug.
    """

    try:
        decoded = raw_bytes.decode("utf-8", errors="ignore")
        candidate = json.loads(decoded)
    except json.JSONDecodeError:
        return

    try:
        model = ParseResponse.model_validate(candidate)
    except ValidationError:
        return

    # A successful validation must survive a serialize/parse round trip: the
    # canonical dump is by construction a valid ParseResponse.
    dumped = model.model_dump()
    reparsed = ParseResponse.model_validate(dumped)
    assert reparsed.model_dump() == dumped


def _coerce_json(candidate: Any) -> Any:
    """Return the candidate untouched; kept for parity with sibling fuzzers."""

    return candidate


def _run_smoke(seed_path: Path) -> None:
    """Run one deterministic validation pass from a known corpus seed."""

    sample = json.loads(seed_path.read_text(encoding="utf-8"))
    ParseResponse.model_validate(_coerce_json(sample))


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
        exercise_schema(data)

    atheris.Setup([sys.argv[0], *forwarded], test_one_input)
    atheris.Fuzz()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
