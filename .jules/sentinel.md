## 2024-06-17 - Enforce Strict Content-Type Validation on /parse Endpoint
**Vulnerability:** The `/parse` endpoint lacked explicit validation on the `Content-Type` header of uploaded files, allowing any file format to be blindly passed to the downstream MinerU OCR engine.
**Learning:** This gap existed because the API relied exclusively on the underlying engine's error handling to manage unparseable or unexpected file formats rather than enforcing boundaries at the API surface level.
**Prevention:** Always implement explicit input validation, specifically strict `Content-Type` checks for file uploads in FastAPI (`file.content_type != "application/pdf"`), to prevent arbitrary files from reaching deeper application layers and to fail fast securely.
