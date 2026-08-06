"""Benchmark bounded PDF upload ingestion without selecting a new default."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
import platform
import sys
import tempfile
import time
from collections.abc import Awaitable, Callable, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from starlette.datastructures import UploadFile

CHUNK_CANDIDATES: dict[str, int | None] = {
    "8kib": 8 * 1024,
    "64kib": 64 * 1024,
    "256kib": 256 * 1024,
    "1mib": 1024 * 1024,
    "adaptive": None,
}
CONCURRENCY_LEVELS = (1, 8, 32, 128)
TARGET_FIXTURE_BYTES = (
    1 * 1024 * 1024,
    5 * 1024 * 1024,
    20 * 1024 * 1024,
)
_RESULT_SCHEMA_PATH = "docs/benchmarks/upload-ingestion-result.schema.json"
CohortRunner = Callable[..., Awaitable[list[dict[str, int | float]]]]


def resolve_chunk_bytes(candidate: str, fixture_bytes: int) -> int:
    """Resolve one named candidate to the exact read size used for a fixture."""

    if candidate not in CHUNK_CANDIDATES:
        raise ValueError(f"Unknown chunk candidate: {candidate}")
    configured = CHUNK_CANDIDATES[candidate]
    if configured is not None:
        return configured
    if fixture_bytes <= TARGET_FIXTURE_BYTES[0]:
        return 64 * 1024
    if fixture_bytes <= TARGET_FIXTURE_BYTES[1]:
        return 256 * 1024
    return 1024 * 1024


def _sha256(path: Path) -> str:
    """Return a streaming SHA-256 identifier for one fixture."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def inventory_fixture(path: Path) -> dict[str, int | str]:
    """Validate and inventory one immutable PDF benchmark fixture."""

    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Fixture must be a regular non-symlink file: {path}")
    with path.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise ValueError(f"Fixture does not contain PDF magic bytes: {path.name}")
    return {
        "fixture_name": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def discover_fixtures(directory: Path) -> list[Path]:
    """Return the sorted regular PDF fixtures directly under a directory."""

    if not directory.is_dir():
        raise ValueError(f"Fixture directory does not exist: {directory}")
    return sorted(
        path
        for path in directory.glob("*.pdf")
        if path.is_file() and not path.is_symlink()
    )


def nearest_rank_percentile(values: Sequence[float], probability: float) -> float:
    """Return the deterministic nearest-rank percentile for non-empty samples."""

    if not values:
        raise ValueError("Percentile requires at least one sample")
    if not 0 < probability <= 1:
        raise ValueError("Percentile probability must be in (0, 1]")
    ordered = sorted(values)
    rank = max(1, math.ceil(probability * len(ordered)))
    return ordered[rank - 1]


def _peak_rss_bytes() -> int:
    """Return the process peak RSS in bytes when the platform exposes it."""

    try:
        import resource
    except ImportError:
        return 0
    raw_value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if platform.system() == "Darwin":
        return raw_value
    return raw_value * 1024


async def _event_loop_probe(
    stop_event: asyncio.Event,
    observed_delays: list[float],
    *,
    interval_seconds: float = 0.005,
) -> None:
    """Measure maximum event-loop scheduling delay while a cohort is active."""

    expected = time.perf_counter() + interval_seconds
    while not stop_event.is_set():
        await asyncio.sleep(interval_seconds)
        now = time.perf_counter()
        observed_delays.append(max(0.0, now - expected))
        expected = now + interval_seconds


async def _copy_one_fixture(
    fixture_path: Path,
    *,
    chunk_bytes: int,
    temporary_directory: Path,
) -> dict[str, int | float]:
    """Copy one real file-backed UploadFile to temporary storage and measure it."""

    started = time.perf_counter()
    read_calls = 0
    bytes_copied = 0
    source_handle = fixture_path.open("rb")
    upload = UploadFile(
        file=source_handle,
        size=fixture_path.stat().st_size,
        filename=fixture_path.name,
    )
    try:
        with tempfile.NamedTemporaryFile(
            dir=temporary_directory,
            prefix="newsdom-ingestion-benchmark-",
            delete=True,
        ) as destination:
            while True:
                chunk = await upload.read(chunk_bytes)
                read_calls += 1
                if not chunk:
                    break
                destination.write(chunk)
                bytes_copied += len(chunk)
            destination.flush()
    finally:
        await upload.close()
    return {
        "duration_seconds": time.perf_counter() - started,
        "read_calls": read_calls,
        "bytes_copied": bytes_copied,
    }


async def run_cohort(
    fixture_path: Path,
    *,
    chunk_bytes: int,
    concurrency: int,
) -> list[dict[str, int | float]]:
    """Run one concurrent real-file cohort and preserve per-request raw samples."""

    if concurrency < 1:
        raise ValueError("Concurrency must be at least one")
    if chunk_bytes < 1:
        raise ValueError("Chunk size must be at least one byte")

    stop_event = asyncio.Event()
    observed_delays: list[float] = []
    with tempfile.TemporaryDirectory(prefix="newsdom-ingestion-benchmark-") as root:
        temporary_directory = Path(root)
        probe = asyncio.create_task(_event_loop_probe(stop_event, observed_delays))
        try:
            samples = await asyncio.gather(
                *(
                    _copy_one_fixture(
                        fixture_path,
                        chunk_bytes=chunk_bytes,
                        temporary_directory=temporary_directory,
                    )
                    for _ in range(concurrency)
                )
            )
        finally:
            stop_event.set()
            await probe

    maximum_delay = max(observed_delays, default=0.0)
    for sample in samples:
        sample["event_loop_max_delay_seconds"] = maximum_delay
    return samples


def _environment_record() -> dict[str, Any]:
    """Return reproducibility metadata that does not contain credentials."""

    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "executable": Path(sys.executable).name,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor_count": os.cpu_count(),
    }


def _metrics(
    samples: Sequence[dict[str, int | float]],
    *,
    cohort_wall_seconds: Sequence[float],
    cpu_seconds: Sequence[float],
    peak_rss_bytes: Sequence[int],
) -> dict[str, int | float]:
    """Aggregate raw samples without discarding the samples themselves."""

    durations = [float(sample["duration_seconds"]) for sample in samples]
    total_bytes = sum(int(sample["bytes_copied"]) for sample in samples)
    total_wall = sum(cohort_wall_seconds)
    return {
        "p50_latency_seconds": nearest_rank_percentile(durations, 0.50),
        "p95_latency_seconds": nearest_rank_percentile(durations, 0.95),
        "throughput_bytes_per_second": total_bytes / total_wall if total_wall else 0.0,
        "read_calls": sum(int(sample["read_calls"]) for sample in samples),
        "cpu_seconds": sum(cpu_seconds),
        "peak_rss_bytes": max(peak_rss_bytes, default=0),
        "temporary_disk_bytes": total_bytes,
        "event_loop_max_delay_seconds": max(
            (
                float(sample.get("event_loop_max_delay_seconds", 0.0))
                for sample in samples
            ),
            default=0.0,
        ),
    }


async def run_matrix(
    fixture_paths: list[Path],
    *,
    output_path: Path,
    candidates: tuple[str, ...] = tuple(CHUNK_CANDIDATES),
    concurrency_levels: tuple[int, ...] = CONCURRENCY_LEVELS,
    repetitions: int = 3,
    cohort_runner: CohortRunner = run_cohort,
) -> dict[str, Any]:
    """Run and write the reproducible raw upload-ingestion evidence matrix."""

    if repetitions < 1:
        raise ValueError("Repetitions must be at least one")
    if not fixture_paths:
        raise ValueError("At least one PDF fixture is required")

    fixture_records = [inventory_fixture(path) for path in fixture_paths]
    cases: list[dict[str, Any]] = []
    for concurrency in concurrency_levels:
        if concurrency < 1:
            raise ValueError("Concurrency levels must be positive")
        for fixture_path, fixture_record in zip(fixture_paths, fixture_records):
            fixture_bytes = int(fixture_record["size_bytes"])
            for candidate in candidates:
                chunk_bytes = resolve_chunk_bytes(candidate, fixture_bytes)
                all_samples: list[dict[str, int | float]] = []
                cohort_wall_seconds: list[float] = []
                cpu_seconds: list[float] = []
                peak_rss_bytes: list[int] = []
                for _ in range(repetitions):
                    wall_started = time.perf_counter()
                    cpu_started = time.process_time()
                    samples = await cohort_runner(
                        fixture_path,
                        chunk_bytes=chunk_bytes,
                        concurrency=concurrency,
                    )
                    cpu_seconds.append(time.process_time() - cpu_started)
                    cohort_wall_seconds.append(time.perf_counter() - wall_started)
                    peak_rss_bytes.append(_peak_rss_bytes())
                    all_samples.extend(samples)
                cases.append(
                    {
                        "fixture_name": fixture_path.name,
                        "candidate": candidate,
                        "chunk_bytes": chunk_bytes,
                        "concurrency": concurrency,
                        "repetitions": repetitions,
                        "metrics": _metrics(
                            all_samples,
                            cohort_wall_seconds=cohort_wall_seconds,
                            cpu_seconds=cpu_seconds,
                            peak_rss_bytes=peak_rss_bytes,
                        ),
                        "samples": all_samples,
                    }
                )

    report: dict[str, Any] = {
        "schema_version": "1.0.0",
        "schema_path": _RESULT_SCHEMA_PATH,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_environment": _environment_record(),
        "fixtures": fixture_records,
        "cases": cases,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _positive_int(value: str) -> int:
    """Parse one strictly positive command-line integer."""

    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be at least one")
    return parsed


def main(argv: list[str] | None = None) -> None:
    """Run the complete issue #534 candidate matrix from the command line."""

    parser = argparse.ArgumentParser(
        description=(
            "Benchmark PDF UploadFile ingestion candidates and emit raw JSON evidence."
        )
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        required=True,
        help="Directory containing real 1 MiB, 5 MiB, and 20 MiB PDF fixtures.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path for the schema-versioned raw JSON report.",
    )
    parser.add_argument(
        "--repetitions",
        type=_positive_int,
        default=3,
        help="Cohort repetitions for every matrix case (default: 3).",
    )
    parser.add_argument(
        "--candidate",
        dest="candidates",
        action="append",
        choices=tuple(CHUNK_CANDIDATES),
        help="Optional candidate filter; repeat to select multiple values.",
    )
    parser.add_argument(
        "--concurrency",
        dest="concurrency_levels",
        action="append",
        type=_positive_int,
        help="Optional concurrency filter; repeat to select multiple values.",
    )
    args = parser.parse_args(argv)
    fixture_paths = discover_fixtures(args.fixtures_dir)
    candidates = tuple(args.candidates or CHUNK_CANDIDATES)
    concurrency_levels = tuple(args.concurrency_levels or CONCURRENCY_LEVELS)
    asyncio.run(
        run_matrix(
            fixture_paths,
            output_path=args.output,
            candidates=candidates,
            concurrency_levels=concurrency_levels,
            repetitions=args.repetitions,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
