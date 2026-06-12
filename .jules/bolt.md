## 2024-06-12 - Consolidate iterative operations in dom_builder.py
**Learning:** Chaining multiple `any()` or `isinstance()` generator comprehensions introduces noticeable function call overhead in hot paths, such as parsing large block lists in `dom_builder.py`.
**Action:** Prefer consolidating iterations into single explicit `for` loops with exact type checking (`type(x) is ...`) over chained comprehensions for parsing heavy data lists.
