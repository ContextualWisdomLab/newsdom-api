## 2025-02-28 - Normalize Windows Filenames
**Vulnerability:** The API allowed users to upload files literally containing Windows-style backslashes in their names on POSIX systems, because `pathlib.Path` treats backslashes as regular filename characters. While not a path traversal vulnerability, this can cause cross-platform issues or edge cases.
**Learning:** On POSIX systems, `pathlib.Path` treats backslashes as regular filename characters, not directory separators. A Windows-style path like `..\\..\\file.pdf` does not cause path traversal via `Path(filename).name`, but creates a file literally containing backslashes.
**Prevention:** Always normalize backward slashes to forward slashes before applying `Path` extraction.
