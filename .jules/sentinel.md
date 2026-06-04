
## 2025-06-04 - Path Traversal Vector via Windows Backslashes on POSIX Systems
**Vulnerability:** User-provided filenames containing backslashes (e.g., `..\..\..\etc\passwd`) might bypass standard POSIX path protections because `pathlib.Path().name` treats `\` as a regular character rather than a directory separator on Linux/Mac, potentially allowing path traversal if combined with subsequent unintended resolutions.
**Learning:** `Path(filename).name` alone is insufficient sanitization if the backend runs on POSIX but the client provides a Windows-style path.
**Prevention:** Always sanitize backslashes by replacing them with forward slashes (e.g., `filename.replace('\\', '/')`) before extracting the basename when handling file uploads.
