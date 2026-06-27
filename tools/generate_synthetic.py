"""
CLI tool for generate_synthetic.py.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from newsdom_api.synthetic import generate_fixture


def main(argv: list[str] | None = None) -> None:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic newspaper PDFs and corresponding truth JSONs."
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory to save the generated PDF and JSON files.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for repeatable generation (default: 42).",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of distinct fixtures to generate by incrementing the seed (default: 1).",
    )

    args = parser.parse_args(argv)

    if not args.output_dir.exists():
        args.output_dir.mkdir(parents=True, exist_ok=True)
    elif not args.output_dir.is_dir():
        print(
            f"Error: {args.output_dir} exists and is not a directory.", file=sys.stderr
        )
        sys.exit(1)

    try:
        for i in range(args.count):
            current_seed = args.seed + i
            print(f"Generating fixture with seed {current_seed}...")
            pdf_path, truth_path = generate_fixture(args.output_dir, seed=current_seed)
            print(f"  Generated PDF: {pdf_path}")
            print(f"  Generated JSON: {truth_path}")

    except Exception as e:
        print(
            f"An error occurred while generating synthetic fixtures: {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\nAll fixtures generated successfully.")


if __name__ == "__main__":  # pragma: no cover
    main()
