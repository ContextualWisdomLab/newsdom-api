## 2024-06-13 - Path Traversal Vulnerability
**Vulnerability:** User-provided file upload name could allow path traversal on POSIX systems via backslashes bypassing `Path().name`.
**Learning:** Backslashes are treated as regular characters in file names on POSIX, not path separators, allowing malicious payloads to bypass simple basename extraction.
**Prevention:** Always sanitize uploaded filenames by replacing backslashes with forward slashes before extracting the basename.
