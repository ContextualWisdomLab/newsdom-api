## 2024-05-18 - [Add PDF Upload Validation]
**Vulnerability:** Unrestricted File Upload in `/parse` Endpoint
**Learning:** The `parse_pdf_bytes` service directly passed any uploaded bytes to the MinerU CLI wrapper. An attacker could potentially upload malicious non-PDF files that could either crash the underlying CLI tool or exploit potential vulnerabilities in it.
**Prevention:** Added robust file validation. First, checked the `Content-Type` header (should be `application/pdf`). Second, and more importantly, read the bytes and validated that they start with the standard PDF magic bytes (`%PDF-`). Throws a `415 Unsupported Media Type` if either of these fail.
