## 2024-05-20 - Failed lazy bbox evaluation due to unexpected block dependencies
**Learning:** In document layout parsing schemas like `newsdom_api.dom_builder`, lazily evaluating fields like `bbox` might look like a great micro-optimization if only certain blocks seem to use them at first glance. However, delaying evaluation can easily cause runtime `UnboundLocalError` side effects, especially if subsequent blocks in a sequence silently rely on earlier variable state.
**Action:** Always verify variables instantiated outside of specific conditionals aren't implicitly expected by other parts of the parsing loop before aggressively moving them.

## 2024-05-20 - Generator expressions within tight loops in _derived_metrics
**Learning:** In `newsdom_api.equivalence._derived_metrics`, using multiple separate generator expressions (like `sum(1 for x in list if condition)`) on the same large array scales poorly because it requires a fresh iteration of the array and dictionary lookups for each metric calculation.
**Action:** When aggregating multiple independent metrics from a single array of dictionaries, consolidate them into a single pass `for` loop to massively reduce lookup and iteration overhead.
