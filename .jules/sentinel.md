## 2025-02-14 - Fix Insecure File Upload via Missing Magic Byte Check
**Vulnerability:** The `/parse` endpoint verified file types exclusively using the `Content-Type` header, omitting payload inspection. This allowed bypassing checks by supplying malicious payloads with an `application/pdf` header.
**Learning:** Checking headers is insufficient; APIs consuming binary data must validate content via magic bytes (e.g., `b"%PDF-"`) and structural parsing before processing.
**Prevention:** Always inspect magic bytes for binary upload endpoints and reject structurally invalid payloads before handing data to downstream parsers.

## 2024-06-25 - Prevent DoS from unbounded file read
**Vulnerability:** The `/parse` API reads the entire uploaded PDF into memory using `await file.read()`. If an attacker uploads a massive file, it can cause an Out-Of-Memory (OOM) error, leading to Denial of Service (DoS).
**Learning:** FastAPI `UploadFile.read()` loads the entire file into memory unless limited. Even if it's spooled to disk by FastAPI initially, calling `.read()` buffers it fully into memory. Since this goes to MinerU which might process it for a while, large files cause severe memory exhaustion.
**Prevention:** Implement an application-level file size limit during the upload read process using `file.size`.

## 2025-02-14 - Enhance Upload Filename Sanitization with Strict Regex
**Vulnerability:** The client-supplied upload filename was only checked against basic path traversal techniques without restricting the character set. Special characters (like shell control characters or invisible characters) could potentially bypass weak filters and reach downstream subsystems, presenting a command injection or path traversal risk.
**Learning:** Basic normalization (like stripping null bytes and replacing backslashes) is insufficient. Security at the boundary requires strict validation of character sets for client-provided data.
**Prevention:** Sanitize user inputs such as filenames using strict regex (e.g., `re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)`) before passing them to backend functions.
