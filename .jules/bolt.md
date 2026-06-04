## 2024-06-04 - Cache MinerU executable resolution
**Learning:** `shutil.which` does disk I/O to search through all directories in the `PATH` environment variable. Caching this result for functions called on every request avoids redundant I/O operations and speeds up the API endpoint. In this case, `_resolve_mineru_bin` was heavily penalizing request time by calling `shutil.which` every time.
**Action:** Always look for and cache disk I/O operations in high-frequency functions. Remember to clear the cache in tests using `.cache_clear()` if the cache behavior interferes with monkeypatching.
