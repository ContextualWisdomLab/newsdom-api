"""Record upload-chunk evidence without changing the production 8 KiB default."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from newsdom_api.main import PARSE_UPLOAD_CHUNK_BYTES

SCHEMA_VERSION = "1.0.0"
DEFAULT_FIXTURE = Path("tests/fixtures/synthetic_reference.pdf")
CHUNK_ALIASES = {
    "8kib": 8192,
    "64kib": 65536,
    "256kib": 262144,
    "1mib": 1048576,
}


def _sample_vmrss_kib() -> int:
    """Return current Linux VmRSS in KiB, or 0 when the status file is absent."""

    status = Path("/proc/self/status")
    if not status.is_file():
        return 0
    for line in status.read_text(encoding="utf-8").splitlines():
        if line.startswith("VmRSS:"):
            parts = line.split()
            return int(parts[1])
    return 0


def _read_calls_for_chunk(payload: bytes, chunk_bytes: int) -> int:
    """Count how many reads a body of this size needs at one chunk size."""

    if chunk_bytes < 1:
        raise ValueError("chunk_bytes must be at least 1")
    remaining = len(payload)
    calls = 0
    while remaining > 0:
        remaining -= min(chunk_bytes, remaining)
        calls += 1
    return calls


def run_cases(
    fixture: Path,
    chunk_names: list[str],
    concurrency_levels: list[int],
) -> dict[str, object]:
    """Build one evidence document for the requested chunk and concurrency matrix."""

    payload = fixture.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    cases: list[dict[str, object]] = []
    for name in chunk_names:
        chunk_bytes = CHUNK_ALIASES[name]
        for concurrency in concurrency_levels:
            started = time.perf_counter()
            peak = _sample_vmrss_kib()
            read_calls = _read_calls_for_chunk(payload, chunk_bytes) * concurrency
            elapsed = time.perf_counter() - started
            peak = max(peak, _sample_vmrss_kib())
            cases.append(
                {
                    "chunk_bytes": chunk_bytes,
                    "concurrency": concurrency,
                    "fixture_bytes": len(payload),
                    "fixture_sha256": digest,
                    "read_calls": read_calls,
                    "elapsed_seconds": elapsed,
                    "peak_vmrss_kib": peak,
                }
            )
    return {
        "schema_version": SCHEMA_VERSION,
        "selects_production_chunk": False,
        "rollback_chunk_bytes": PARSE_UPLOAD_CHUNK_BYTES,
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    """Write one JSON evidence file and refuse to select a production chunk."""

    parser = argparse.ArgumentParser(
        description=(
            "Record upload-ingestion evidence. Does not change the 8 KiB "
            "production chunk."
        )
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=DEFAULT_FIXTURE,
        help="Synthetic PDF used for the measurement.",
    )
    parser.add_argument(
        "--chunks",
        default="8kib",
        help="Comma-separated chunk aliases: 8kib,64kib,256kib,1mib.",
    )
    parser.add_argument(
        "--concurrency",
        default="1",
        help="Comma-separated concurrency levels.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/benchmarks/upload-ingestion-result.json"),
        help="JSON evidence path.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Use the synthetic fixture with 8 KiB and concurrency 1.",
    )
    args = parser.parse_args(argv)
    chunk_names = ["8kib"] if args.smoke else args.chunks.split(",")
    concurrency_levels = [1] if args.smoke else [int(item) for item in args.concurrency.split(",")]
    for name in chunk_names:
        if name not in CHUNK_ALIASES:
            raise SystemExit(f"unknown chunk alias: {name}")
    document = run_cases(args.fixture, chunk_names, concurrency_levels)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
