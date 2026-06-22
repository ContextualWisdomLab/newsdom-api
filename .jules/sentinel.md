## 2024-05-24 - Missing Input Validation on File Uploads
**Vulnerability:** The `/parse` endpoint accepted file uploads without validating the `Content-Type` header, allowing arbitrary file types to be processed by the backend MinerU engine.
**Learning:** Even internal backend services need explicit input validation at the API boundary, as delegating type checking entirely to external binaries like MinerU can lead to unexpected failures, resource exhaustion, or unintended processing behavior.
**Prevention:** Validate upload media types at the API controller level before passing payloads to underlying processing engines, and keep extension validation notes separate unless the controller enforces them too.

## 2024-06-22 - [File Upload DoS Vulnerability]
**Vulnerability:** Memory exhaustion Denial of Service (DoS) vulnerability due to unbounded file reads in the `/parse` endpoint. The endpoint was using `await file.read()` which loads the entire file into memory at once.
**Learning:** The FastAPI `UploadFile` object streams data to a temporary file on disk if it exceeds a certain size, but calling `.read()` on it without arguments forces the entire contents into RAM.
**Prevention:** Always read uploaded files in chunks (e.g., `await file.read(65536)`) and enforce a strict maximum size limit (e.g., 50MB) during the reading process, returning a 413 Payload Too Large error if exceeded.
