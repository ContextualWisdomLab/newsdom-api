## 2024-05-19 - Fast DOM block skips
**Learning:** MinerU's block stream processing in Python was doing expensive property lookup (`.get`) and conditional float casting (`_bbox_from_values`) unconditionally *before* determining if a text block was entirely empty or irrelevant (fast skip check: `not text and block_type not in {...}`). Delaying type conversions and extra `.get()` calls to *after* the fast conditional checks speeds up list processing significantly for documents with many blocks.
**Action:** Always check loop invariant/early exit conditions with minimal initial property accesses (like `block.get("type")` and string `.strip()`) before resolving heavier block geometry (like `_bbox_from_values` casting list float properties).

## 2024-05-19 - Page indexing O(n) reduction
**Learning:** Python generators and comprehensions like `any(isinstance(..., int))` scan lists exhaustively for every check. Code combining these conditional state derivations (`has_page_idx`, `has_missing_page_idx`) into the identical iteration loop that groups the blocks reduces `O(3n)` scans into a single `O(n)` grouping scan.
**Action:** When grouping list dictionaries in Python for building a DOM, collapse Boolean existence checks into the same loop that builds the `defaultdict` or `dict.setdefault()` groupings to save iteration passes.

## 2024-05-19 - Fuzzing failure PyInstaller
**Learning:** PyInstaller can fail to detect library dependencies correctly if the entry point script is in a separate directory (`fuzzers/`) from the main package (`src/`) unless the `src` directory is explicitly specified with `--paths src` or `PYTHONPATH`. Without it, `PyInstaller` might fail to package internal modules causing a runtime `ModuleNotFoundError`.
**Action:** Ensure `PYTHONPATH` includes the `src` package or use `--paths src` when packaging standalone executables with `pyinstaller` for internal scripts.
