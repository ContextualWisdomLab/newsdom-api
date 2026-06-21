## 2024-05-24 - Eager BoundingBox Float Casting
**Learning:** A performance anti-pattern in `newsdom-api` parsing loops is eager allocation and expensive type-conversions (e.g., float casting for `BoundingBox`) at the start of block iterations. We found ~45% overhead was caused by converting unused `bbox` values to floats in blocks that were early-returned (like headers/footers).
**Action:** Defer expensive conversions and allocations into the specific conditional branches that actually consume them to reduce overhead on unused block types.
