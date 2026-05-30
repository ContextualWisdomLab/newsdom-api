## 2025-02-20 - Security Enhancement on Upload Endpoint
**Vulnerability:** The `/parse` endpoint lacked basic input validation on the uploaded PDF file. A malicious user could potentially upload extremely large files leading to DoS, or upload non-PDF files that could be misinterpreted or break subsequent processing steps.
**Learning:** File uploads in web applications are a common vector for attack. Validating both the `content_type` and the actual magic bytes of the file content adds a crucial layer of defense against file spoofing.
**Prevention:** Always add file size limits, content type checks, and content inspection (like magic bytes) to file upload endpoints to ensure the server only processes expected file types and sizes.
