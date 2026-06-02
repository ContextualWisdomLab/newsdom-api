## 2024-06-02 - Added Content-Type Validation on Uploads
**Vulnerability:** The `/parse` API endpoint accepted any `UploadFile` without validating the file's `content_type`, making it possible for arbitrary files to be passed to the underlying MinerU runner.
**Learning:** Even though the downstream processes might fail on invalid input, failing early and securely at the API boundary avoids unnecessary resource usage and prevents potentially malicious files from entering the temporary directory structure.
**Prevention:** Always validate `file.content_type` against expected MIME types before persisting or processing uploaded files.
