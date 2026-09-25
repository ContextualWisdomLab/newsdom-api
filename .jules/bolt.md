# Bolt's Performance Journal

## Automated-agent coordination

Before starting work, check this journal and the repository's open pull
requests. Do not open a PR for an issue that already has an open PR or a
journal entry marked **In progress**. Pick a different topic instead, and
keep one PR per distinct issue.

## 2024-05-24 - Defer unnecessary float casting and validation
**Learning:** A performance anti-pattern in `newsdom-api` parsing loops is eager allocation and expensive type conversion of `BoundingBox` values at the start of block iterations. Converting unused `bbox` values to floats in blocks that return early, such as headers and footers, caused about 45% overhead. Pydantic schema construction also performs float conversion and validation, so explicitly casting values that are already floats adds redundant work in deep loops.
**Action:** Defer expensive conversions and allocations into the conditional branches that consume them. Skip explicit `float()` calls for existing floats and conditionally cast integer-like JSON values before schema construction, preserving the `BoundingBox` float contract.

## 2024-05-24 - Defer string operations for MinerU text blocks
**Learning:** Eager string operations such as `.strip()` and `.get("text")` on every block add overhead, especially for non-textual blocks such as images and tables.
**Action:** Defer these operations to the branches that handle textual blocks.

## 2024-05-24 - Avoid regex for simple HTML string checks
**Learning:** Using `re.compile().search()` for simple fixed character sets such as `&`, `<`, `>`, `"`, and `'` in hot string paths adds measurable overhead compared with plain Python `in` checks.
**Action:** Replace regex checks with explicit boolean substring checks for fixed target characters.

## 2024-05-24 - Avoid unnecessary primitive type checks
**Learning:** `isinstance()` adds small but measurable call overhead for exact primitive checks in high-frequency parsing paths. When exact built-in types are required, `type(var) is int` already excludes `bool`, so a redundant `type(var) is not bool` check adds work.
**Action:** Use `type() is` or `type() is not` when exact built-in primitive types are required.

## 2024-06-23 - Avoid empty-list allocation in grouping loops
**Learning:** In hot loops grouped by a key, `dict.setdefault(key, []).append(item)` instantiates an empty list on every iteration even though it is discarded for existing keys.
**Action:** Use `collections.defaultdict(list)` so lists are created only for new keys, avoiding redundant allocation and garbage-collection overhead.

## 2024-07-09 - Avoid eager list allocation on glob generators
**Learning:** Resolving a glob generator into a list causes unnecessary directory traversal and memory allocation when only one match is needed.
**Action:** Use `next(path.glob(...))` with `StopIteration` handling for single-artifact fallback lookups, avoiding eager allocation, sorting, and traversal.

## 2024-07-28 - Check truthiness before string allocation
**Learning:** Calling `.strip()` unconditionally on values that may be empty allocates and adds overhead.
**Action:** Check truthiness, for example with `if not value:`, before string operations on potentially empty values.

## 2024-07-30 - Avoid chained replacement for character-set checks
**Learning:** Chained `.replace()` calls allocate intermediate strings when checking whether a string consists of specific characters.
**Action:** Use `.strip(chars)` to avoid multiple allocations in this hot path.

## 2026-06-24 - Avoid unnecessary newline replacement
**Learning:** Calling `text.replace("\n", " ")` on every text block allocates even when the text has no newline.
**Action:** Check for `"\n"` before replacing in hot text-processing loops.

## 2026-06-25 - Unroll generator expressions in hot paths
**Learning:** Generator expressions, tuple allocations, and `any()` checks for fixed-size lists add iterator overhead and prevent early returns.
**Action:** Unroll extraction and validation for fixed-size arrays to avoid allocations and short-circuit invalid data immediately.

## 2026-06-25 - Avoid expensive `str()` casting for HTML-safe text
**Learning:** Eagerly casting all values with `str()` adds measurable overhead when many values are already strings.
**Action:** Return early for empty values and use exact string type checks to bypass redundant casts.

## 2026-06-27 - Avoid unnecessary HTML escaping in hot text paths
**Learning:** Calling `html.escape()` on already plain strings adds avoidable work in parsing hot paths.
**Action:** After truthiness and string fast-path checks, detect HTML-sensitive characters before escaping.

## 2026-06-30 - Replace `max` generator in page metrics
**Learning:** A generator passed to `max()` adds iterator overhead and can obscure fallback semantics when no valid values are found.
**Action:** Use an explicit loop for hot structural-metric scans while preserving the empty-result fallback.

## 2026-06-30 - Use regex instead of generator-based `any()` string loops
**Learning:** `any()` with a generator comprehension allocates a generator and adds Python-level loop overhead for every character.
**Action:** Use a pre-compiled regex search to evaluate string patterns in C, achieving a measured speedup for text-heavy operations.
