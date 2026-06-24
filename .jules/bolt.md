## 2024-05-24 - Eager BoundingBox Float Casting
**Learning:** A performance anti-pattern in `newsdom-api` parsing loops is eager allocation and expensive type-conversions (e.g., float casting for `BoundingBox`) at the start of block iterations. We found ~45% overhead was caused by converting unused `bbox` values to floats in blocks that were early-returned (like headers/footers).
**Action:** Defer expensive conversions and allocations into the specific conditional branches that actually consume them to reduce overhead on unused block types.

## 2024-05-24 - Eager Default List Allocations (`setdefault`)
**Learning:** Using `dict.setdefault(key, []).append(item)` inside hot parsing loops contributes to significant unnecessary overhead (about ~20-30% slower for dictionary grouping) due to the eager instantiation of the default list `[]` on *every single iteration*, even when the key already exists.
**Action:** Replace `setdefault` with `collections.defaultdict(list)` when doing grouping/aggregation inside hot loops to defer list creation only to missing keys.
