from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict


def _print_tree(
    node: Any, prefix: str = "", is_last: bool = True, key: str = ""
) -> None:
    """Recursively print a dictionary or list in tree format."""
    marker = "└── " if is_last else "├── "
    line = f"{prefix}{marker}"

    if key:
        line += f"{key}: "

    if isinstance(node, dict):
        if not node:
            print(f"{line}{{}}")
            return
        if key:
            print(line)
        else:
            print(f"{prefix}{marker} (dict)")

        new_prefix = prefix + ("    " if is_last else "│   ")
        items = list(node.items())
        for i, (k, v) in enumerate(items):
            _print_tree(v, new_prefix, i == len(items) - 1, str(k))

    elif isinstance(node, list):
        if not node:
            print(f"{line}[]")
            return
        if key:
            print(f"{line}[list, len={len(node)}]")
        else:
            print(f"{prefix}{marker}[list, len={len(node)}]")

        new_prefix = prefix + ("    " if is_last else "│   ")
        for i, item in enumerate(node):
            _print_tree(item, new_prefix, i == len(node) - 1, f"[{i}]")
    else:
        # Primitive values
        val_str = str(node)
        if len(val_str) > 50:
            val_str = val_str[:47] + "..."
        print(f"{line}{val_str}")


def pretty_print_dom(data: Dict[str, Any]) -> None:
    """Print the DOM JSON in a tree format."""
    print("NewsDOM Root")
    _print_tree(data, is_last=True)


def main(argv: list[str] | None = None) -> None:
    """Run pretty_print_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Pretty print a NewsDOM JSON in tree format."
    )
    parser.add_argument("input", type=Path, help="Path to input JSON file.")

    args = parser.parse_args(argv)

    if not args.input.is_file():
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}", file=sys.stderr)
        sys.exit(1)

    pretty_print_dom(data)


if __name__ == "__main__":  # pragma: no cover
    main()
