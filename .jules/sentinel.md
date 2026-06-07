## 2025-03-05 - Fix Path Traversal via Backslash Evasion
**Vulnerability:** User-provided filename in the upload payload was processed using `Path(filename).name`. On POSIX systems, `pathlib` considers backslashes (`\`) as valid filename characters, thus it did not sanitize paths like `..\..\etc\passwd`, which allowed for a path traversal vulnerability.
**Learning:** `Path(filename).name` does not extract the final filename if the path uses backslashes on POSIX systems (e.g. Linux). This allows directory traversal vectors utilizing backslashes to bypass filename sanitization.
**Prevention:** Always sanitize backslashes into forward slashes (e.g. `filename.replace('\\', '/')`) before passing them to `Path` on backend POSIX systems handling paths from diverse sources or Windows clients.
