## 2024-05-24 - Missing Input Validation on File Uploads
**Vulnerability:** The `/parse` endpoint accepted file uploads without validating the `Content-Type` header, allowing arbitrary file types to be processed by the backend MinerU engine.
**Learning:** Even internal backend services need explicit input validation at the API boundary, as delegating type checking entirely to external binaries like MinerU can lead to unexpected failures, resource exhaustion, or unintended processing behavior.
**Prevention:** Validate upload media types at the API controller level before passing payloads to underlying processing engines, and keep extension validation notes separate unless the controller enforces them too.
