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
**Prevention:** Apply a strict regex allowlist (e.g., `re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)`) to user-supplied filenames before using them for temporary files or CLI arguments, and cap the sanitized basename below common filesystem component limits while preserving useful extensions.

## 2026-06-26 - Add Referrer-Policy Security Header
**Vulnerability:** The API lacked a `Referrer-Policy` header, potentially leaking sensitive information in the URL to external domains if a user navigates away from the application.
**Learning:** Adding a `Referrer-Policy: no-referrer` header is a simple yet effective defense-in-depth measure that prevents the browser from sending the `Referer` header.
**Prevention:** Include `Referrer-Policy: no-referrer` in the global security headers middleware to consistently enforce this protection across all endpoints.

## 2026-06-30 - Disable Caching for API Responses
**Vulnerability:** API responses can contain parsed document data that should remain ephemeral, but default HTTP caching behavior may allow browsers or intermediaries to retain sensitive response payloads.
**Learning:** Security headers should cover response storage as well as framing, MIME sniffing, and referrer leakage. `Cache-Control: no-store, max-age=0` explicitly opts sensitive API responses out of caching.
**Prevention:** Set a global no-store cache directive in the FastAPI security headers middleware so all endpoints inherit the response storage policy.

## 2026-06-30 - Suppress Public HTTP Exception Chains
**Vulnerability:** Chaining internal parser or runtime exceptions into public `HTTPException` instances can retain implementation details, dependency errors, or local path fragments in traceback material.
**Learning:** API handlers should return sanitized status codes and messages while suppressing internal exception causes at the public boundary.
**Prevention:** Raise generic client-facing `HTTPException` responses with `from None` after mapping parser and runtime failures to safe error details.

## 2026-06-30 - Reject Option-Like MinerU Arguments
**Vulnerability:** User-influenced paths or executable overrides that begin with `-` can be interpreted by downstream CLI tools as options even when subprocess execution uses `shell=False`.
**Learning:** Shell metacharacter filtering and argv lists reduce command injection risk, but option injection remains possible unless CLI arguments reject leading dashes or insert an explicit option terminator supported by the tool.
**Prevention:** Reject MinerU command arguments that begin with `-` before constructing the subprocess argv.

## 2026-06-30 - Preserve Security Headers on 500 Responses
**Vulnerability:** Unhandled FastAPI exceptions can produce sanitized 500 responses without the same defense-in-depth headers applied by normal middleware responses.
**Learning:** Error response paths need explicit coverage because exception handlers can bypass or duplicate header logic differently from successful request paths.
**Prevention:** Route both middleware responses and global 500 exception responses through a shared security-header helper.

## 2025-03-01 - Prevent Memory Exhaustion via Unbounded Stream Reading
**Vulnerability:** FastAPIs `UploadFile.read()` was called on the remainder of large files and accumulated entirely into an in-memory `bytes` object (or `bytearray` inside the event loop). Although it respected `file.size`, processing a maximum allowed payload size into memory before writing to disk could still cause memory exhaustion when under heavy load.
**Learning:** For large file uploads, loading the entire payload into a single Python object (even just to process or save it) creates a bottleneck where large chunks of contiguous memory are required simultaneously. The Strix security scanner will flag this as a Resource Exhaustion Vulnerability ("security theater") if you attempt to just bound a single `file.read()`.
**Prevention:** Stream the chunks (e.g. 8192 bytes) directly to a `NamedTemporaryFile` on disk while verifying the accumulation does not exceed the maximum allowed payload size. Ensure the temporary file is securely unlinked in a `finally` block or when an upload limit exception is raised.

## 2025-03-09 - Prevent Command/Log Injection via Newlines in Filenames
**Vulnerability:** The blocklist regex `_UNSAFE_CHARS_PATTERN` for CLI arguments did not explicitly filter newline (\n) or carriage return (\r) characters. This can allow command or log injection even when `shell=False` is used, by passing arguments containing newlines.
**Learning:** Shell metacharacter blocklists must include whitespace metacharacters like newlines and carriage returns, as these can bypass checks and manipulate logs or downstream argument parsing.
**Prevention:** Explicitly add \n and \r to the `_UNSAFE_CHARS_PATTERN` blocklist for CLI arguments.
