## 2024-05-24 - Missing Input Validation on File Uploads
**Vulnerability:** The `/parse` endpoint accepted file uploads without validating the `Content-Type` header, allowing arbitrary file types to be processed by the backend MinerU engine.
**Learning:** Even internal backend services need explicit input validation at the API boundary, as delegating type checking entirely to external binaries like MinerU can lead to unexpected failures, resource exhaustion, or unintended processing behavior.
**Prevention:** Validate upload media types at the API controller level before passing payloads to underlying processing engines, and keep extension validation notes separate unless the controller enforces them too.

## 2024-06-23 - Missing HTTP Security Headers
**Vulnerability:** API responses lacked standard HTTP security headers (e.g., `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`), increasing the risk of MIME-sniffing and clickjacking attacks.
**Learning:** FastAPI does not add security headers by default. For public-facing APIs, these must be explicitly configured to provide defense-in-depth, even for APIs primarily serving JSON responses.
**Prevention:** Use a global middleware to automatically inject essential security headers into all responses at the application layer.
