## 2024-06-17 - Defer BoundingBox allocation in parsing loops
**Learning:** A performance anti-pattern in `newsdom-api` parsing loops is eager allocation and expensive type-conversions (e.g., float casting for `BoundingBox`) at the start of block iterations.
**Action:** Defer such calculations into the specific conditional branches that actually consume them to reduce overhead on unused block types.
