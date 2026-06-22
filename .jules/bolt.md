## 2024-05-24 - Eager BoundingBox Float Casting
**Learning:** A performance anti-pattern in `newsdom-api` parsing loops is eager allocation and expensive type-conversions (e.g., float casting for `BoundingBox`) at the start of block iterations. We found ~45% overhead was caused by converting unused `bbox` values to floats in blocks that were early-returned (like headers/footers).
**Action:** Defer expensive conversions and allocations into the specific conditional branches that actually consume them to reduce overhead on unused block types.

## 2025-03-02 - Eager Evaluation of setdefault in Loops
**Learning:** A Python performance anti-pattern found in `newsdom-api` is the use of `dict.setdefault(key, []).append(value)` inside large loops (such as parsing `content_list`). Because Python evaluates arguments eagerly, an empty list `[]` is allocated and subsequently garbage collected on *every single iteration* if the key already exists.
**Action:** Replace `setdefault` with `collections.defaultdict(list)` inside tight loops. `defaultdict` only instantiates the default value (the list) when a missing key is accessed, preventing O(N) wasteful object allocations.
