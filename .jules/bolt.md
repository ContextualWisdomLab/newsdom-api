## 2024-06-07 - Caching with Environment/Mocked Dependencies in Tests
**Learning:** Adding `@functools.lru_cache` to a function that reads environment variables (like `os.environ.get`) or uses external lookups (like `shutil.which`) breaks tests that use `monkeypatch` to manipulate those variables or mocks sequentially, leading to cross-test contamination due to caching.
**Action:** Always call `<function_name>.cache_clear()` in unit tests immediately before or after `monkeypatch` setup when caching such functions to ensure each test execution evaluates with a clean cache.
