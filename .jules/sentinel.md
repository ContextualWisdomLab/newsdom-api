## 2025-02-14 - Fix Insecure File Upload via Missing Magic Byte Check
**Vulnerability:** The `/parse` endpoint verified file types exclusively using the `Content-Type` header, omitting payload inspection. This allowed bypassing checks by supplying malicious payloads with an `application/pdf` header.
**Learning:** Checking headers is insufficient; APIs consuming binary data must validate content via magic bytes (e.g., `b"%PDF-"`) and structural parsing before processing.
**Prevention:** Always inspect magic bytes for binary upload endpoints and reject structurally invalid payloads before handing data to downstream parsers.

## 2024-06-25 - Prevent DoS from unbounded file read
**Vulnerability:** The `/parse` API reads the entire uploaded PDF into memory using `await file.read()`. If an attacker uploads a massive file, it can cause an Out-Of-Memory (OOM) error, leading to Denial of Service (DoS).
**Learning:** FastAPI `UploadFile.read()` loads the entire file into memory unless limited. Even if it's spooled to disk by FastAPI initially, calling `.read()` buffers it fully into memory. Since this goes to MinerU which might process it for a while, large files cause severe memory exhaustion.
**Prevention:** Implement an application-level file size limit during the upload read process using `file.size`.

## 2025-02-14 - Prevent Unhandled OSError via Filename Length Validation
**Vulnerability:** The API accepted arbitrarily long client-provided filenames. When these were written to the filesystem, they could trigger an unhandled `OSError (ENAMETOOLONG)` that crashed the endpoint handler and returned a 500 error.
**Learning:** Path traversal normalization (`PurePosixPath.name`) is not sufficient for input validation; file names must also be bounded in length to match operating system and filesystem limits before attempting I/O operations.
**Prevention:** Always validate and bound the byte-length of client-supplied filenames (e.g., `< 255 bytes` for standard filesystems) or fall back to a safe default name.
