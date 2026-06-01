## 2024-06-01 - Optimizing multiple list passes

**Learning:** When dealing with large arrays (like `content_list` produced from parsed documents), multiple iterations using `any()` with generator expressions introduce significant overhead due to both the number of iterations and the cost of the generator expressions themselves. Combining them into a single pass over the list can dramatically reduce loop overhead. Also, using `type(x) is T` is faster than `isinstance(x, T)` inside tight loops.

**Action:** Look for multiple consecutive iterations over the same list and combine them when possible. Avoid `any()` or `all()` with generators on large loops when checking multiple conditions that can be evaluated simultaneously in one combined loop. Also consider using `type() is` for simple type checks in critical paths.
