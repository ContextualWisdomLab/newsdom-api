## 2024-05-24 - Missing Input Validation on File Uploads
**Vulnerability:** The `/parse` endpoint accepted file uploads without validating the `Content-Type` header, allowing arbitrary file types to be processed by the backend MinerU engine.
**Learning:** Even internal backend services need explicit input validation at the API boundary, as delegating type checking entirely to external binaries like MinerU can lead to unexpected failures, resource exhaustion, or unintended processing behavior.
**Prevention:** Validate upload media types at the API controller level before passing payloads to underlying processing engines, and keep extension validation notes separate unless the controller enforces them too.

## 2025-02-28 - Missing Null Byte and Magic Byte Validations on Uploads
**Vulnerability:** The `/parse` endpoint accepted PDF uploads based purely on HTTP Content-Type and stripped filename inputs safely up to standard characters but lacked explicit validation of null bytes and PDF magic byte headers.
**Learning:** Content-Type headers can be trivially spoofed by clients, and `PurePosixPath` in standard python does not strip null bytes natively.
**Prevention:** Always ensure null bytes are stripped out from filename strings manually to prevent path poisoning, and explicitly check binary formats via magic bytes to avoid passing spoofed malicious files to downstream external binaries.
