## 2024-05-24 - Eager BoundingBox Float Casting
**Learning:** A performance anti-pattern in `newsdom-api` parsing loops is eager allocation and expensive type-conversions (e.g., float casting for `BoundingBox`) at the start of block iterations. We found ~45% overhead was caused by converting unused `bbox` values to floats in blocks that were early-returned (like headers/footers).
**Action:** Defer expensive conversions and allocations into the specific conditional branches that actually consume them to reduce overhead on unused block types.
## 2024-05-24 - Defer string operations for MinerU text blocks
**Learning:** Eager execution of string operations like `.strip()` and `.get("text")` on every block adds overhead, especially for non-textual blocks like images and tables.
**Action:** Defer these operations to the conditional branches that actually handle textual blocks to optimize parsing speed.

## 2024-06-23 - Overhead of `dict.setdefault` with empty lists
**Learning:** In hot loops where data is grouped by a key (e.g., grouping parser blocks by page index), using `dict.setdefault(key, []).append(item)` forces the instantiation of an empty list `[]` on every single iteration, even though it's thrown away on all but the first insertion per key. This causes significant, unnecessary garbage collection overhead when processing tens of thousands of items.
**Action:** Use `collections.defaultdict(list)` instead. This defers list creation only to the points where new keys are encountered, avoiding redundant allocations and showing a ~40% speedup in hot grouping paths.
