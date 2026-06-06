## 2024-06-06 - Optimize metric derivation loop in equivalence.py
**Learning:** Multiple generator expressions that iterate over the same large list (e.g., `articles` array in JSON payloads) can cause significant performance overhead by repeatedly performing the same operations (like type checking and dictionary lookups).
**Action:** Always prefer consolidating multiple array passes into a single loop when extracting multiple metrics or properties from the same collection.
