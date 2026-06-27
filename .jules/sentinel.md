## 2025-02-14 - Fix Insecure File Upload via Missing Magic Byte Check
**Vulnerability:** The `/parse` endpoint verified file types exclusively using the `Content-Type` header, omitting payload inspection. This allowed bypassing checks by supplying malicious payloads with an `application/pdf` header.
**Learning:** Checking headers is insufficient; APIs consuming binary data must validate content via magic bytes (e.g., `b"%PDF-"`) and structural parsing before processing.
**Prevention:** Always inspect magic bytes for binary upload endpoints and reject structurally invalid payloads before handing data to downstream parsers.

## 2024-06-25 - Prevent DoS from unbounded file read
**Vulnerability:** The `/parse` API reads the entire uploaded PDF into memory using `await file.read()`. If an attacker uploads a massive file, it can cause an Out-Of-Memory (OOM) error, leading to Denial of Service (DoS).
**Learning:** FastAPI `UploadFile.read()` loads the entire file into memory unless limited. Even if it's spooled to disk by FastAPI initially, calling `.read()` buffers it fully into memory. Since this goes to MinerU which might process it for a while, large files cause severe memory exhaustion.
**Prevention:** Implement an application-level file size limit during the upload read process using `file.size`.

## 2026-06-27 - Pydantic Schema Vulnerability: Injection & DoS risks via missing Field constraints
**Vulnerability:** String fields accepted unbounded input allowing injection, BoundingBox coordinates lacked min/max validations enabling coordinate bypasses, and recursive structures allowed deep nesting for potential DoS.
**Learning:** Unconstrained Pydantic schemas open application backdoors to payload abuses and denial of service. Validations must go beyond types to specify bounds and lengths.
**Prevention:** Strictly define `max_length` for all string fields, apply `ge` and `le` bounds for numeric data, and set `max_length` on Lists to prevent runaway recursion or memory exhaustion.
