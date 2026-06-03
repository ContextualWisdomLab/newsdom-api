## 2024-06-03 - Fix Path Traversal in filename sanitation
**Vulnerability:** The application was vulnerable to path traversal because `Path(filename).name` doesn't sanitize backslashes (`\`) on non-Windows systems, allowing arbitrary file writes if a user provides a payload like `..\\..\\etc\\passwd`.
**Learning:** Python's `pathlib.Path().name` uses the semantics of the operating system it runs on. On POSIX systems, `\` is treated as a valid filename character, not a directory separator.
**Prevention:** Always normalize both forward and backward slashes before extracting the base filename, e.g. using `Path(filename.replace('\\', '/')).name`.
