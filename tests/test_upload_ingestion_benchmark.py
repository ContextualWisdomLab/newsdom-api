"""Contracts for the upload-ingestion benchmark and raw evidence schema."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from tools import benchmark_upload_ingestion as benchmark


def _sample(
    duration: float = 0.25,
    *,
    read_calls: int = 3,
    bytes_copied: int = 100,
) -> dict[str, int | float]:
    """Return one compact request sample for aggregate-metric tests."""

    return {
        "duration_seconds": duration,
        "read_calls": read_calls,
        "bytes_copied": bytes_copied,
    }


def test_candidate_matrix_preserves_every_issue_534_chunk_option() -> None:
    """The harness must not silently omit or preselect one requested candidate."""

    assert benchmark.CHUNK_CANDIDATES == {
        "8kib": 8 * 1024,
        "64kib": 64 * 1024,
        "256kib": 256 * 1024,
        "1mib": 1024 * 1024,
        "adaptive": None,
    }
    assert benchmark.CONCURRENCY_LEVELS == (1, 8, 32, 128)
    assert benchmark.TARGET_FIXTURE_BYTES == (
        1 * 1024 * 1024,
        5 * 1024 * 1024,
        20 * 1024 * 1024,
    )


@pytest.mark.parametrize(
    ("fixture_bytes", "expected"),
    [
        (1 * 1024 * 1024, 64 * 1024),
        (5 * 1024 * 1024, 256 * 1024),
        (20 * 1024 * 1024, 1024 * 1024),
    ],
)
def test_adaptive_candidate_resolves_deterministically(
    fixture_bytes: int,
    expected: int,
) -> None:
    """The adaptive candidate needs an auditable size rule before measurement."""

    assert benchmark.resolve_chunk_bytes("adaptive", fixture_bytes) == expected


def test_unknown_candidate_is_rejected() -> None:
    """A typo must not fall back to an unrecorded upload policy."""

    with pytest.raises(ValueError, match="Unknown chunk candidate"):
        benchmark.resolve_chunk_bytes("unexpected", 1024)


def test_fixture_inventory_rejects_non_pdf_magic(tmp_path: Path) -> None:
    """Raw benchmark evidence must identify actual PDF inputs."""

    fixture = tmp_path / "invalid.pdf"
    fixture.write_bytes(b"not a PDF")

    with pytest.raises(ValueError, match="PDF magic"):
        benchmark.inventory_fixture(fixture)


def test_fixture_inventory_records_hash_and_size(tmp_path: Path) -> None:
    """Every benchmark case should be traceable to immutable fixture bytes."""

    fixture = tmp_path / "fixture.pdf"
    fixture.write_bytes(b"%PDF-1.4\nsynthetic benchmark bytes\n%%EOF\n")

    record = benchmark.inventory_fixture(fixture)

    assert record["fixture_name"] == "fixture.pdf"
    assert record["size_bytes"] == fixture.stat().st_size
    assert record["sha256"].startswith("sha256:")
    assert len(record["sha256"]) == len("sha256:") + 64


def test_percentile_uses_nearest_rank_for_small_reproducible_samples() -> None:
    """The raw report should define deterministic p50 and p95 aggregation."""

    values = [0.4, 0.1, 0.3, 0.2]

    assert benchmark.nearest_rank_percentile(values, 0.50) == 0.2
    assert benchmark.nearest_rank_percentile(values, 0.95) == 0.4


def test_current_rss_reads_linux_vmrss_in_bytes(tmp_path: Path) -> None:
    """Per-case memory evidence must use current RSS rather than lifetime high-water."""

    status_path = tmp_path / "status"
    status_path.write_text("Name:\tpython\nVmRSS:\t1234 kB\n", encoding="utf-8")

    assert benchmark.current_rss_bytes(status_path=status_path) == 1234 * 1024


def test_current_rss_returns_zero_when_status_is_missing_or_malformed(
    tmp_path: Path,
) -> None:
    """Unsupported memory providers should be explicit zero evidence, not stale RSS."""

    missing = tmp_path / "missing"
    malformed = tmp_path / "status"
    malformed.write_text("VmRSS:\tnot-a-number kB\n", encoding="utf-8")

    assert benchmark.current_rss_bytes(status_path=missing) == 0
    assert benchmark.current_rss_bytes(status_path=malformed) == 0


def test_metrics_use_case_local_rss_and_nearest_rank_event_loop_p95() -> None:
    """Memory and responsiveness aggregates must derive from raw cohort evidence."""

    first = benchmark.CohortObservation(
        samples=(_sample(0.10), _sample(0.30)),
        wall_seconds=0.40,
        cpu_seconds=0.20,
        rss_baseline_bytes=100,
        peak_rss_bytes=500,
        event_loop_delay_samples_seconds=(0.001, 0.002, 0.003, 0.100),
    )
    second = benchmark.CohortObservation(
        samples=(_sample(0.20),),
        wall_seconds=0.20,
        cpu_seconds=0.10,
        rss_baseline_bytes=150,
        peak_rss_bytes=250,
        event_loop_delay_samples_seconds=(0.004, 0.005),
    )

    metrics = benchmark.aggregate_metrics((first, second))

    assert metrics["peak_rss_bytes"] == 500
    assert metrics["peak_rss_delta_bytes"] == 400
    assert metrics["event_loop_p95_delay_seconds"] == 0.100
    assert metrics["event_loop_max_delay_seconds"] == 0.100
    assert metrics["p50_latency_seconds"] == 0.20
    assert metrics["p95_latency_seconds"] == 0.30


def test_later_case_can_report_lower_rss_than_an_earlier_case() -> None:
    """A process-lifetime high-water mark must not contaminate later matrix cases."""

    high = benchmark.CohortObservation(
        samples=(_sample(),),
        wall_seconds=0.25,
        cpu_seconds=0.10,
        rss_baseline_bytes=1_000,
        peak_rss_bytes=9_000,
        event_loop_delay_samples_seconds=(),
    )
    low = benchmark.CohortObservation(
        samples=(_sample(),),
        wall_seconds=0.25,
        cpu_seconds=0.10,
        rss_baseline_bytes=1_000,
        peak_rss_bytes=2_000,
        event_loop_delay_samples_seconds=(),
    )

    assert benchmark.aggregate_metrics((high,))["peak_rss_bytes"] == 9_000
    assert benchmark.aggregate_metrics((low,))["peak_rss_bytes"] == 2_000


@pytest.mark.asyncio
async def test_matrix_report_records_environment_cases_and_raw_samples(
    tmp_path: Path,
) -> None:
    """A small injected run should preserve all inputs and unaggregated samples."""

    fixture = tmp_path / "fixture.pdf"
    fixture.write_bytes(b"%PDF-1.4\nsynthetic benchmark bytes\n%%EOF\n")
    output = tmp_path / "report.json"
    calls: list[tuple[str, int, int]] = []

    async def fake_cohort(
        fixture_path: Path,
        *,
        chunk_bytes: int,
        concurrency: int,
    ) -> benchmark.CohortObservation:
        calls.append((fixture_path.name, chunk_bytes, concurrency))
        return benchmark.CohortObservation(
            samples=tuple(
                {
                    "duration_seconds": 0.25,
                    "read_calls": 3,
                    "bytes_copied": fixture_path.stat().st_size,
                }
                for _ in range(concurrency)
            ),
            wall_seconds=0.50,
            cpu_seconds=0.25,
            rss_baseline_bytes=1_000,
            peak_rss_bytes=2_000,
            event_loop_delay_samples_seconds=(0.001, 0.010),
        )

    report = await benchmark.run_matrix(
        [fixture],
        output_path=output,
        candidates=("8kib", "adaptive"),
        concurrency_levels=(1, 2),
        repetitions=2,
        cohort_runner=fake_cohort,
    )

    assert output.read_text(encoding="utf-8") == json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    assert report["schema_version"] == "1.1.0"
    assert report["benchmark_environment"]["python_version"]
    assert len(report["fixtures"]) == 1
    assert len(report["cases"]) == 4
    assert len(report["cases"][0]["samples"]) == 2
    assert len(report["cases"][0]["cohort_observations"]) == 2
    assert report["cases"][0]["metrics"]["p50_latency_seconds"] == 0.25
    assert report["cases"][0]["metrics"]["p95_latency_seconds"] == 0.25
    assert report["cases"][0]["metrics"]["peak_rss_delta_bytes"] == 1_000
    assert report["cases"][0]["metrics"]["event_loop_p95_delay_seconds"] == 0.010
    assert calls == [
        ("fixture.pdf", 8 * 1024, 1),
        ("fixture.pdf", 8 * 1024, 1),
        ("fixture.pdf", 64 * 1024, 1),
        ("fixture.pdf", 64 * 1024, 1),
        ("fixture.pdf", 8 * 1024, 2),
        ("fixture.pdf", 8 * 1024, 2),
        ("fixture.pdf", 64 * 1024, 2),
        ("fixture.pdf", 64 * 1024, 2),
    ]


def test_raw_evidence_schema_is_strict_and_covers_required_metrics() -> None:
    """Checked-in evidence must be machine-auditable before results are accepted."""

    schema_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "benchmarks"
        / "upload-ingestion-result.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    case_schema = schema["$defs"]["benchmark_case"]
    metric_properties = case_schema["properties"]["metrics"]["properties"]

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema_version"] == {"const": "1.1.0"}
    assert schema["additionalProperties"] is False
    assert case_schema["additionalProperties"] is False
    assert "cohort_observations" in case_schema["required"]
    assert case_schema["properties"]["concurrency"] == {
        "type": "integer",
        "minimum": 1,
    }
    for required_metric in (
        "p50_latency_seconds",
        "p95_latency_seconds",
        "throughput_bytes_per_second",
        "read_calls",
        "cpu_seconds",
        "peak_rss_bytes",
        "peak_rss_delta_bytes",
        "temporary_disk_bytes",
        "event_loop_p95_delay_seconds",
        "event_loop_max_delay_seconds",
    ):
        assert required_metric in metric_properties
        assert required_metric in case_schema["properties"]["metrics"]["required"]


def test_cli_defaults_to_the_complete_evidence_matrix(monkeypatch, tmp_path: Path) -> None:
    """The documented command should run every required candidate and concurrency."""

    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    output = tmp_path / "results.json"
    captured: dict[str, object] = {}

    async def fake_run_matrix(
        fixture_paths: list[Path],
        *,
        output_path: Path,
        candidates: tuple[str, ...],
        concurrency_levels: tuple[int, ...],
        repetitions: int,
        cohort_runner=benchmark.run_cohort,
    ) -> dict[str, object]:
        captured.update(
            fixture_paths=fixture_paths,
            output_path=output_path,
            candidates=candidates,
            concurrency_levels=concurrency_levels,
            repetitions=repetitions,
            cohort_runner=cohort_runner,
        )
        return {}

    monkeypatch.setattr(benchmark, "run_matrix", fake_run_matrix)
    monkeypatch.setattr(benchmark, "discover_fixtures", lambda _directory: [])

    benchmark.main(
        [
            "--fixtures-dir",
            str(fixtures),
            "--output",
            str(output),
            "--repetitions",
            "3",
        ]
    )

    assert captured["candidates"] == tuple(benchmark.CHUNK_CANDIDATES)
    assert captured["concurrency_levels"] == benchmark.CONCURRENCY_LEVELS
    assert captured["repetitions"] == 3
    assert captured["output_path"] == output
    assert asyncio.iscoroutinefunction(fake_run_matrix)
