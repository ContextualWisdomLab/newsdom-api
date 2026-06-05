## 2024-05-24 - Fix POSIX path traversal via backslashes

**Vulnerability:** File uploads containing backslashes in their filenames (e.g., `..\\..\\etc\\passwd`) could bypass `Path().name` sanitization on POSIX systems, leading to path traversal when writing the file.
**Learning:** `pathlib.Path().name` uses the host OS path separators. On POSIX systems, `\` is a valid filename character, so `Path("..\\..\\etc\\passwd").name` returns the full string, allowing attackers to potentially write files outside the intended directory.
**Prevention:** Always sanitize user-provided filenames by explicitly replacing backslashes with forward slashes before calling `Path().name` (e.g., `filename.replace('\\', '/')`).