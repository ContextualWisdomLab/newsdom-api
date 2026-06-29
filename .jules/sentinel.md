## 2025-02-14 - Fix Insecure File Upload via Missing Magic Byte Check
**Vulnerability:** The `/parse` endpoint verified file types exclusively using the `Content-Type` header, omitting payload inspection. This allowed bypassing checks by supplying malicious payloads with an `application/pdf` header.
**Learning:** Checking headers is insufficient; APIs consuming binary data must validate content via magic bytes (e.g., `b"%PDF-"`) and structural parsing before processing.
**Prevention:** Always inspect magic bytes for binary upload endpoints and reject structurally invalid payloads before handing data to downstream parsers.

## 2024-06-25 - Prevent DoS from unbounded file read
**Vulnerability:** The `/parse` API reads the entire uploaded PDF into memory using `await file.read()`. If an attacker uploads a massive file, it can cause an Out-Of-Memory (OOM) error, leading to Denial of Service (DoS).
**Learning:** FastAPI `UploadFile.read()` loads the entire file into memory unless limited. Even if it's spooled to disk by FastAPI initially, calling `.read()` buffers it fully into memory. Since this goes to MinerU which might process it for a while, large files cause severe memory exhaustion.
**Prevention:** Implement an application-level file size limit during the upload read process using `file.size`.
## 2025-02-14 - [Unsafe Upload Filename Risk]
**Vulnerability:** Client-supplied filenames uploaded via FastAPI were used to name temporary files passed to the MinerU CLI. Even with `subprocess.run(..., shell=False)`, weak filename normalization can leave path traversal fragments, unsafe filesystem characters, confusing option-like names, or brittle artifact names.
**Learning:** Removing null bytes and path separators is not enough for filesystem and CLI integration boundaries; filenames should be reduced to a small, predictable character set before they influence paths or downstream tool arguments.
**Prevention:** Apply a strict regex allowlist (e.g., `re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)`) to user-supplied filenames before using them for temporary files or CLI arguments.

## 2026-06-26 - Add Referrer-Policy Security Header
**Vulnerability:** The API lacked a `Referrer-Policy` header, potentially leaking sensitive information in the URL to external domains if a user navigates away from the application.
**Learning:** Adding a `Referrer-Policy: no-referrer` header is a simple yet effective defense-in-depth measure that prevents the browser from sending the `Referer` header.
**Prevention:** Include `Referrer-Policy: no-referrer` in the global security headers middleware to consistently enforce this protection across all endpoints.
