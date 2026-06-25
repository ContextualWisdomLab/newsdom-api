## 2025-02-14 - Fix Insecure File Upload via Missing Magic Byte Check
**Vulnerability:** The `/parse` endpoint verified file types exclusively using the `Content-Type` header, omitting payload inspection. This allowed bypassing checks by supplying malicious payloads with an `application/pdf` header.
**Learning:** Checking headers is insufficient; APIs consuming binary data must validate content via magic bytes (e.g., `b"%PDF-"`) and structural parsing before processing.
**Prevention:** Always inspect magic bytes for binary upload endpoints and reject structurally invalid payloads before handing data to downstream parsers.

## 2024-06-25 - Prevent DoS from unbounded file read
**Vulnerability:** The `/parse` API reads the entire uploaded PDF into memory using `await file.read()`. If an attacker uploads a massive file, it can cause an Out-Of-Memory (OOM) error, leading to Denial of Service (DoS).
**Learning:** FastAPI `UploadFile.read()` loads the entire file into memory unless limited. Even if it's spooled to disk by FastAPI initially, calling `.read()` buffers it fully into memory. Since this goes to MinerU which might process it for a while, large files cause severe memory exhaustion.
**Prevention:** Implement an application-level file size limit during the upload read process using `file.size`.
## 2025-02-14 - [Filename Command Injection Risk]
**Vulnerability:** Client-supplied filenames uploaded via FastAPI were passed to an underlying CLI tool (`mineru`) without strict sanitization, potentially allowing command injection or path traversal if `shutil.which` or similar execution strategies fallback to shell execution, or arguments leak to the shell.
**Learning:** Relying on basic replacements (like removing null bytes and slashes) is insufficient for CLI integration where shell control characters could be interpreted by the environment.
**Prevention:** Apply a strict regex allowlist (e.g., `re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)`) to all user-supplied filenames before using them as arguments in backend `subprocess` calls or CLI integrations.
