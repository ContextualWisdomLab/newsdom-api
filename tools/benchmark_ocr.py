from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

from newsdom_api.service import parse_pdf_bytes


def run_mineru_engine(pdf_path: Path) -> dict[str, Any]:
    """
    Run the 'mineru' OCR engine on a single PDF file.

    This function acts as a wrapper around the existing 'parse_pdf_bytes' service,
    adapting its output for the benchmark harness.

    Args:
        pdf_path: The path to the PDF file to process.

    Returns:
        A dictionary containing the processing status and key metrics.
    """
    response = parse_pdf_bytes(pdf_path.read_bytes(), filename=pdf_path.name)
    return {
        "status": "success",
        "page_count": len(response.pages),
        "article_count": sum(len(p.articles) for p in response.pages),
    }


OCR_ENGINES: dict[str, Callable[[Path], dict[str, Any]]] = {
    "mineru": run_mineru_engine,
}


def run_benchmark(
    fixtures_dir: Path, output_path: Path, engines: list[str]
) -> None:
    """
    Run the OCR benchmark against a directory of PDFs for a list of engines.

    It iterates through each PDF and runs each specified engine, capturing
    success, failure, or timeout, along with performance metrics. The
    aggregated results are written to a JSON file.

    Args:
        fixtures_dir: The directory containing the PDF files to benchmark.
        output_path: The path to write the final JSON results file.
        engines: A list of engine names to run.
    """
    pdf_paths = sorted(list(fixtures_dir.glob("*.pdf")))
    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files found in {fixtures_dir}")

    all_results: dict[str, Any] = {
        "summary": {
            "total_files": len(pdf_paths),
            "total_runs": len(pdf_paths) * len(engines),
        }
    }

    for engine_name in engines:
        if engine_name not in OCR_ENGINES:
            raise ValueError(f"Unknown engine: {engine_name}")

        print(f"--- Running benchmark for engine: {engine_name} ---")
        engine_runner = OCR_ENGINES[engine_name]
        engine_results: dict[str, Any] = {
            "success": 0,
            "failed": 0,
            "timed_out": 0,
            "results": {},
        }

        for pdf_path in pdf_paths:
            start_time = time.monotonic()
            try:
                result = engine_runner(pdf_path)
                duration = time.monotonic() - start_time
                engine_results["success"] += 1
                engine_results["results"][pdf_path.name] = {
                    "status": "success",
                    "duration": round(duration, 2),
                    **result,
                }
                print(f"  [SUCCESS] {pdf_path.name} in {duration:.2f}s")

            except (RuntimeError, subprocess.CalledProcessError) as e:
                duration = time.monotonic() - start_time
                engine_results["failed"] += 1
                engine_results["results"][pdf_path.name] = {
                    "status": "failed",
                    "duration": round(duration, 2),
                    "error": str(e),
                }
                print(f"  [FAILED] {pdf_path.name} in {duration:.2f}s")

            except subprocess.TimeoutExpired:
                duration = time.monotonic() - start_time
                engine_results["timed_out"] += 1
                engine_results["results"][pdf_path.name] = {
                    "status": "timed_out",
                    "duration": round(duration, 2),
                }
                print(f"  [TIMED OUT] {pdf_path.name} after {duration:.2f}s")

        all_results[engine_name] = engine_results

    output_path.write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nBenchmark results written to {output_path}")


def main(argv: list[str] | None = None) -> None:
    """
    Main entry point for the OCR benchmark script.

    Parses command-line arguments and initiates the benchmark run.

    Args:
        argv: Optional list of command-line arguments for testing.
    """
    parser = argparse.ArgumentParser(
        description="Run OCR benchmark against a directory of PDFs."
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        required=True,
        help="Directory containing PDF files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to write the JSON results file.",
    )
    parser.add_argument(
        "--engines",
        nargs="+",
        default=["mineru"],
        help=f"Space-separated list of engines to benchmark. Available: {', '.join(OCR_ENGINES.keys())}",
    )
    args = parser.parse_args(argv)

    run_benchmark(args.fixtures_dir, args.output, args.engines)


if __name__ == "__main__":
    main()
