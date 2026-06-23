## 2024-05-24 - Eager BoundingBox Float Casting
**Learning:** A performance anti-pattern in `newsdom-api` parsing loops is eager allocation and expensive type-conversions (e.g., float casting for `BoundingBox`) at the start of block iterations. We found ~45% overhead was caused by converting unused `bbox` values to floats in blocks that were early-returned (like headers/footers).
**Action:** Defer expensive conversions and allocations into the specific conditional branches that actually consume them to reduce overhead on unused block types.

## 2026-06-23 - `setdefault` in tight parsing loops
**Learning:** In Python, `dict.setdefault(key, [])` evaluates the default value (creating a new list) on *every single call*, even if the key already exists. In `dom_builder.py`, processing thousands of blocks caused unnecessary memory allocation overhead.
**Action:** Use `collections.defaultdict(list)` instead of `dict.setdefault()` when grouping items in loops with large datasets to avoid thousands of discarded allocations.
