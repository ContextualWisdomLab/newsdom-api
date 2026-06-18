## 2025-06-18 - Missing Content-Type Validation on /parse
**Vulnerability:** The /parse endpoint allowed arbitrary file uploads by not verifying the `Content-Type` of uploaded files before passing them to the backend MinerU engine.
**Learning:** Framework-level type hints (like `UploadFile`) do not automatically enforce media types. Explicit application-level validation is required to ensure backend systems do not attempt to process malicious or unsupported files.
**Prevention:** Always validate `file.content_type` against an explicit allowlist (e.g., `application/pdf`) and return a `415 Unsupported Media Type` response on mismatch before passing file bytes to backend processes.
