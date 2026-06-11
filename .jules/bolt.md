## 2024-06-11 - Optimize MinerU layout blocks processing in dom_builder.py
**Learning:** For performance optimizations when parsing large block lists (e.g., handling MinerU OCR layout elements), chaining multiple `any()` or `isinstance()` generator comprehensions introduces noticeable function call overhead in hot paths.
**Action:** Consolidate iterations into single explicit `for` loops and prefer exact type checking (`type(x) is ...`) over `isinstance()` when dealing with large lists.
