from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from pydantic import ValidationError  # noqa: E402
from newsdom_api.schemas import ParseResponse  # noqa: E402


def minify_dom(json_path: Path, output_path: Path) -> None:
    """Minify NewsDOM JSON by removing bounding boxes and dimensions."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError(f"Input file must be a .json file: {json_path}")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file ({json_path}): {exc}") from exc

    try:
        ParseResponse.model_validate(data)
    except ValidationError as exc:
        raise ValueError(
            f"File {json_path} does not match ParseResponse schema: {exc}"
        ) from exc

    for page in data.get("pages", []):
        page.pop("width", None)
        page.pop("height", None)
        for article in page.get("articles", []):
            article.pop("bbox", None)
            for caption in article.get("captions", []):
                caption.pop("bbox", None)
            for footnote in article.get("footnotes", []):
                footnote.pop("bbox", None)
            for img in article.get("images", []):
                img.pop("bbox", None)
                for caption in img.get("captions", []):
                    caption.pop("bbox", None)
                for footnote in img.get("footnotes", []):
                    footnote.pop("bbox", None)

    output_path.write_text(
        json.dumps(data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> None:
    """Run the JSON minifier CLI."""
    parser = argparse.ArgumentParser(
        description="Minify a NewsDOM JSON file by removing bbox and dimensions."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to write the minified JSON output file.",
    )

    args = parser.parse_args(argv)

    try:
        # Validate output path to prevent directory traversal
        import tempfile

        output_path = args.output.resolve()
        base_dir = Path.cwd().resolve()
        temp_dir = Path(tempfile.gettempdir()).resolve()

        try:
            output_path.relative_to(base_dir)
        except ValueError:
            try:
                output_path.relative_to(temp_dir)
            except ValueError:
                print(
                    f"Error: Output path must be within {base_dir} or {temp_dir}",
                    file=sys.stderr,
                )
                sys.exit(1)

        minify_dom(args.input, args.output)
        print(f"Minified JSON successfully written to {args.output}")
    except Exception as exc:
        print(f"Error minifying JSON file: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
