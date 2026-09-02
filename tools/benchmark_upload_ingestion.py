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
from dataclasses import dataclass
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
SampleRecord = dict[str, int | float]


@dataclass(frozen=True, slots=True)
class CohortObservation:
    """Raw process and request evidence for one concurrent ingestion cohort."""

    samples: tuple[SampleRecord, ...]
    wall_seconds: float
    cpu_seconds: float
    rss_baseline_bytes: int
    peak_rss_bytes: int
    event_loop_delay_samples_seconds: tuple[float, ...]

    def as_record(self) -> dict[str, Any]:
        """Return the JSON-serializable cohort evidence retained in the report."""

        return {
            "wall_seconds": self.wall_seconds,
            "cpu_seconds": self.cpu_seconds,
            "rss_baseline_bytes": self.rss_baseline_bytes,
            "peak_rss_bytes": self.peak_rss_bytes,
            "peak_rss_delta_bytes": max(
                0,
                self.peak_rss_bytes - self.rss_baseline_bytes,
            ),
            "event_loop_delay_samples_seconds": list(
                self.event_loop_delay_samples_seconds
            ),
        }


CohortRunner = Callable[..., Awaitable[CohortObservation]]


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


def current_rss_bytes(*, status_path: Path = Path("/proc/self/status")) -> int:
    """Return current Linux process RSS in bytes, or zero when unavailable."""

    try:
        lines = status_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0
    for line in lines:
        if not line.startswith("VmRSS:"):
            continue
        fields = line.split()
        if len(fields) != 3 or fields[2] != "kB":
            return 0
        try:
            kibibytes = int(fields[1])
        except ValueError:
            return 0
        return max(0, kibibytes) * 1024
    return 0


async def _event_loop_probe(
    stop_event: asyncio.Event,
    observed_delays: list[float],
    *,
    interval_seconds: float = 0.005,
) -> None:
    """Sample event-loop scheduling delays while one cohort is active."""

    expected = time.perf_counter() + interval_seconds
    while not stop_event.is_set():
        await asyncio.sleep(interval_seconds)
        now = time.perf_counter()
        observed_delays.append(max(0.0, now - expected))
        expected = now + interval_seconds


async def _rss_probe(
    stop_event: asyncio.Event,
    observed_rss_bytes: list[int],
    *,
    rss_reader: Callable[[], int] = current_rss_bytes,
    interval_seconds: float = 0.005,
) -> None:
    """Sample current process RSS so each case has an independent peak."""

    observed_rss_bytes.append(rss_reader())
    while not stop_event.is_set():
        await asyncio.sleep(interval_seconds)
        observed_rss_bytes.append(rss_reader())


async def _copy_one_fixture(
    fixture_path: Path,
    *,
    chunk_bytes: int,
    temporary_directory: Path,
) -> SampleRecord:
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
) -> CohortObservation:
    """Run one real-file cohort and retain raw timing, loop, and RSS evidence."""

    if concurrency < 1:
        raise ValueError("Concurrency must be at least one")
    if chunk_bytes < 1:
        raise ValueError("Chunk size must be at least one byte")

    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    rss_baseline_bytes = current_rss_bytes()
    observed_rss_bytes = [rss_baseline_bytes]
    stop_event = asyncio.Event()
    observed_delays: list[float] = []
    with tempfile.TemporaryDirectory(prefix="newsdom-ingestion-benchmark-") as root:
        temporary_directory = Path(root)
        event_loop_probe = asyncio.create_task(
            _event_loop_probe(stop_event, observed_delays)
        )
        rss_probe = asyncio.create_task(_rss_probe(stop_event, observed_rss_bytes))
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
            observed_rss_bytes.append(current_rss_bytes())
            stop_event.set()
            await asyncio.gather(event_loop_probe, rss_probe)

    return CohortObservation(
        samples=tuple(samples),
        wall_seconds=time.perf_counter() - wall_started,
        cpu_seconds=time.process_time() - cpu_started,
        rss_baseline_bytes=rss_baseline_bytes,
        peak_rss_bytes=max(observed_rss_bytes, default=0),
        event_loop_delay_samples_seconds=tuple(observed_delays),
    )


def _environment_record() -> dict[str, Any]:
    """Return reproducibility metadata that does not contain credentials."""

    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "executable": Path(sys.executable).name,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor_count": os.cpu_count(),
        "rss_provider": "linux_proc_status_vmrss",
    }


def aggregate_metrics(
    cohorts: Sequence[CohortObservation],
) -> dict[str, int | float]:
    """Aggregate request and cohort evidence without lifetime RSS contamination."""

    samples = [sample for cohort in cohorts for sample in cohort.samples]
    if not samples:
        raise ValueError("At least one request sample is required")
    durations = [float(sample["duration_seconds"]) for sample in samples]
    total_bytes = sum(int(sample["bytes_copied"]) for sample in samples)
    total_wall = sum(cohort.wall_seconds for cohort in cohorts)
    loop_delays = [
        delay
        for cohort in cohorts
        for delay in cohort.event_loop_delay_samples_seconds
    ]
    return {
        "p50_latency_seconds": nearest_rank_percentile(durations, 0.50),
        "p95_latency_seconds": nearest_rank_percentile(durations, 0.95),
        "throughput_bytes_per_second": total_bytes / total_wall if total_wall else 0.0,
        "read_calls": sum(int(sample["read_calls"]) for sample in samples),
        "cpu_seconds": sum(cohort.cpu_seconds for cohort in cohorts),
        "peak_rss_bytes": max(
            (cohort.peak_rss_bytes for cohort in cohorts),
            default=0,
        ),
        "peak_rss_delta_bytes": max(
            (
                max(0, cohort.peak_rss_bytes - cohort.rss_baseline_bytes)
                for cohort in cohorts
            ),
            default=0,
        ),
        "temporary_disk_bytes": total_bytes,
        "event_loop_p95_delay_seconds": (
            nearest_rank_percentile(loop_delays, 0.95) if loop_delays else 0.0
        ),
        "event_loop_max_delay_seconds": max(loop_delays, default=0.0),
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
                cohorts = [
                    await cohort_runner(
                        fixture_path,
                        chunk_bytes=chunk_bytes,
                        concurrency=concurrency,
                    )
                    for _ in range(repetitions)
                ]
                all_samples = [
                    sample
                    for cohort in cohorts
                    for sample in cohort.samples
                ]
                cases.append(
                    {
                        "fixture_name": fixture_path.name,
                        "candidate": candidate,
                        "chunk_bytes": chunk_bytes,
                        "concurrency": concurrency,
                        "repetitions": repetitions,
                        "metrics": aggregate_metrics(cohorts),
                        "cohort_observations": [
                            cohort.as_record() for cohort in cohorts
                        ],
                        "samples": all_samples,
                    }
                )

    report: dict[str, Any] = {
        "schema_version": "1.1.0",
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
