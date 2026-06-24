## 2025-02-14 - Fix Insecure File Upload via Missing Magic Byte Check
**Vulnerability:** The `/parse` endpoint verified file types exclusively using the `Content-Type` header, omitting payload inspection. This allowed bypassing checks by supplying malicious payloads with an `application/pdf` header.
**Learning:** Checking headers is insufficient; APIs consuming binary data must validate content via magic bytes (e.g., `b"%PDF-"`) to ensure structural expectations are met before processing.
**Prevention:** Always inspect magic bytes for binary upload endpoints. Ensure FastAPI upload models are paired with byte-level validation for security boundaries.

## 2025-02-14 - Prevent Denial of Service via Large File Uploads
**Vulnerability:** The `/parse` endpoint did not restrict file sizes for uploaded payloads. An attacker could intentionally submit gigabytes of data as a PDF, causing Out of Memory (OOM) errors or consuming significant disk space/CPU while processing or saving the file.
**Learning:** By verifying the `size` attribute of the `UploadFile` immediately within the route logic, large payloads can be rejected quickly before attempting to read them into memory or write them to temporary directories.
**Prevention:** Implement file size limits early in file upload handlers in FastAPI via `file.size` inspection, returning HTTP 413 Payload Too Large if the size exceeds a defined threshold (e.g., 15MB).
