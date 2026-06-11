## 2024-05-15 - POSIX Path Handling Vulnerability
**Vulnerability:** Path Traversal via Windows-style backslashes on POSIX systems.
**Learning:** `pathlib.Path().name` does not properly sanitize filenames on POSIX systems when the filename is constructed with Windows-style backslashes.
**Prevention:** Sanitize the filename by replacing backslashes with forward slashes before extracting the base name.
