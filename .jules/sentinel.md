## 2025-05-18 - PDF Magic Bytes Validation
**Vulnerability:** The `/parse` endpoint relied solely on the `Content-Type` header, which could be spoofed to upload malicious non-PDF files that could be processed by the backend MinerU engine.
**Learning:** Relying on user-provided headers for file type validation is insufficient and can lead to arbitrary file processing. Deep inspection of the file content (e.g., magic bytes) is required.
**Prevention:** Always validate file types by inspecting the file content (e.g., magic bytes) in addition to or instead of relying on client-provided metadata.
