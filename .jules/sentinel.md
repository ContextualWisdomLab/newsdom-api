## 2024-05-24 - Missing Input Validation on File Uploads
**Vulnerability:** The `/parse` endpoint accepted file uploads without validating the `Content-Type` header, allowing arbitrary file types to be processed by the backend MinerU engine.
**Learning:** Even internal backend services need explicit input validation at the API boundary, as delegating type checking entirely to external binaries like MinerU can lead to unexpected failures, resource exhaustion, or unintended processing behavior.
**Prevention:** Validate upload media types at the API controller level before passing payloads to underlying processing engines, and keep extension validation notes separate unless the controller enforces them too.

## 2025-02-23 - Missing Magic Bytes Validation on File Uploads
**Vulnerability:** The `/parse` endpoint previously relied solely on the `Content-Type` header and file extension, making it possible for attackers to bypass checks and upload arbitrary files (e.g., executables masquerading as PDFs) that could be processed by the backend MinerU engine.
**Learning:** Relying only on user-supplied metadata (like headers or extensions) is insufficient for security. We must validate the actual file contents (e.g., checking magic bytes) to ensure we're only processing the expected file type.
**Prevention:** Always validate file signatures/magic bytes at the API boundary before passing payloads to processing engines.
