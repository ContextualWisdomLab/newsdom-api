## 2024-06-14 - Path Traversal in File Uploads on POSIX Systems
**Vulnerability:** User-provided filenames containing backslashes (Windows paths) were not correctly sanitized by `pathlib.Path().name` on POSIX systems, allowing path traversal vectors.
**Learning:** `pathlib.Path` uses POSIX rules on POSIX systems, where backslash is a valid filename character. Thus, `..\\..\\malicious.pdf` is treated as the filename rather than a path, allowing an attacker to write outside the temporary directory when appended to `Path(tempdir)`.
**Prevention:** Always explicitly normalize backslashes to forward slashes (e.g., `filename.replace('\\', '/')`) before extracting the base name using `pathlib.Path().name` in cross-platform or backend-only environments.
