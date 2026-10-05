## 2023-10-24 - [Upload Chunk Optimization]
**Learning:** In FastAPI/Starlette, `await file.read(size)` dispatches blocking read operations to a threadpool. Using small chunks (e.g. 8KB) for large file uploads causes significant threadpool overhead and context-switching.
**Action:** Optimize file upload endpoints by using larger chunk sizes (e.g. 1MB) to reduce threadpool dispatch overhead.
