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

## 2026-07-09 - Keep upload cleanup non-fatal and observable
**Vulnerability:** Temporary-file cleanup can fail after a successful parse because of filesystem races, antivirus locks, or platform-specific deletion semantics. If cleanup exceptions are allowed to propagate, a successful parse can become a 500 while still leaving unclear forensic evidence.
**Learning:** Cleanup must be guaranteed on all upload paths, but cleanup failure handling should be isolated from the user-facing parse result and logged with enough context for operators to see why disk hygiene failed.
**Prevention:** Run upload temporary-file unlinking in the endpoint `finally` block, catch `OSError`, and log the temporary path at exception level without exposing it in public API responses.

## 2025-02-28 - [Subprocess argument injection via newlines]
 **Vulnerability:** Unsanitized user inputs containing newline (`\n`) and carriage return (`\r`) characters passed as arguments to subprocesses can lead to command and log injection vulnerabilities, even when `shell=False` is used, depending on how downstream CLI tools process the inputs.
 **Learning:** Standard shell metacharacter filters (like `[\0&;|`$<>]`) are insufficient to prevent injection if they omit whitespace control characters. Attackers can inject newlines to manipulate tool behavior or spoof log entries if the downstream executable processes inputs line-by-line or uses them in script evaluation.
 **Prevention:** Explicitly include newline (`\n`) and carriage return (`\r`) characters in blocklists for subprocess arguments, ensuring inputs are restricted strictly to safe paths and alphanumeric characters.

## 2025-03-02 - Prevent Disk Exhaustion via Interrupted Uploads
**Vulnerability:** FastAPIs `UploadFile` payloads were streamed to a `NamedTemporaryFile` within a `with` block that did not cover the file initialization or have a global `finally` block for that path. If a network disconnect or client abort exception interrupted `await file.read()` inside this block, the temporary file path on disk was not properly unlinked, leading to disk space exhaustion over time.
**Learning:** Context managers alone are insufficient when dealing with manual temporary file persistence (`delete=False`) in async HTTP streams because exceptions inside the stream reading loop can bypass cleanup blocks that are positioned further down the control flow.
**Prevention:** Wrap the temporary file creation, stream reading, and processing stages in a single overarching `try...finally` block that guarantees explicit cleanup of the temporary file path regardless of when a network or application exception occurs.

## 2024-10-24 - Fix DoS vulnerability in file uploads
**Vulnerability:** Asynchronous file uploads created temporary files before entering a try/finally block. If the client disconnects or an error occurs during `await file.read()`, the temporary file is left orphaned on the filesystem, leading to disk exhaustion (DoS).
**Learning:** File instantiation and the subsequent read loop must be entirely enclosed within a unified `try...finally` block.
**Prevention:** Always initialize `tmp_path = None` before a `try` block, instantiate the file and perform network reads inside the `try` block, and handle cleanup in `finally` by checking `if tmp_path and tmp_path.exists()`.

## 2025-03-01 - Prevent Disk Exhaustion DoS via Orphaned Temp Files
**Vulnerability:** The `/parse` API streamed large uploaded files into a `NamedTemporaryFile(delete=False)`. If a read error or client disconnect occurred (e.g. an exception during `await file.read(8192)`), the execution flow would jump past the explicit `try...finally` cleanup block that was located *after* the read loop. This resulted in orphaned temporary files left on disk, creating a Disk Exhaustion DoS vulnerability when under attack.
**Learning:** File processing loops, especially those consuming asynchronous `UploadFile` streams, are vulnerable to unhandled exceptions like `ClientDisconnect`. Cleanup logic must guarantee removal regardless of *where* the failure occurs. The `NamedTemporaryFile(delete=False)` itself only guarantees a filename, not cleanup upon early exit.
**Prevention:** Wrap both the initialization of the `NamedTemporaryFile` and the *entire* file reading loop inside a single `try...finally` block that unlinks the temporary file path, ensuring safe cleanup even if network errors or client disconnects interrupt the read process.

## 2025-05-18 - [HIGH] Fix temporary file leak during PDF upload
**Vulnerability:** 파일 업로드 시 `await file.read(8192)`에서 클라이언트 연결 끊김이나 예외가 발생하면 `try...finally` 블록 바깥에 있어 임시 파일이 삭제되지 않고 디스크에 남음 (디스크 고갈 / DoS 위험).
**Learning:** FastAPI의 `UploadFile.read()`는 예외를 발생시킬 수 있으므로, 임시 파일을 생성하고 쓰는 로직은 생성 즉시 `try...finally` 블록 안에 위치시켜야 함.
**Prevention:** 임시 파일 경로를 할당하거나 파일을 여는 즉시 자원 정리(cleanup) 로직이 보장되도록 `try...finally` 블록으로 감싼다.

## 2025-03-09 - Prevent Command/Log Injection via Newlines in Filenames
**Vulnerability:** The blocklist regex `_UNSAFE_CHARS_PATTERN` for CLI arguments did not explicitly filter newline (\n) or carriage return (\r) characters. This can allow command or log injection even when `shell=False` is used, by passing arguments containing newlines.
**Learning:** Shell metacharacter blocklists must include whitespace metacharacters like newlines and carriage returns, as these can bypass checks and manipulate logs or downstream argument parsing.
**Prevention:** Explicitly add \n and \r to the `_UNSAFE_CHARS_PATTERN` blocklist for CLI arguments.

## 2024-05-24 - [CRITICAL] Fix temporary file cleanup to prevent DoS via disk exhaustion
**Vulnerability:** Incomplete temporary file cleanup on asynchronous file uploads.
**Learning:** When processing asynchronous file uploads in FastAPI (`await file.read()`), instantiating temporary files (`NamedTemporaryFile(delete=False)`) inside a nested `try` block while the initial read happens outside can leave temporary files orphaned if an exception occurs before the nested block or during the initial read. This can lead to disk exhaustion (DoS) if clients maliciously disconnect or send malformed data.
**Prevention:** Ensure the temporary path variable (`tmp_path = None`) is initialized before the main `try` block, and the read loop and file instantiation are entirely enclosed within a unified `try...finally` block. Verify cleanup in the `finally` block with `if tmp_path and tmp_path.exists(): tmp_path.unlink(missing_ok=True)`.
## 2023-10-27 - 🛡️ Fix naive absolute path traversal protection
**Vulnerability:** The codebase rejected all absolute paths indiscriminately (e.g., using `is_absolute()`) rather than whitelist-validating them, causing CI breakages when legitimate absolute paths within safe temp directories were provided.
**Learning:** Naively blocking absolute paths can disrupt legitimate CI and test automation tools that rely on paths pointing to temporary system directories like `/tmp`.
**Prevention:** Rather than rejecting all absolute paths out of hand, allow them if they are validated to fall within a safe directory whitelist (e.g., `tempfile.gettempdir()`) to prevent arbitrary file writes while supporting standard testing mechanisms.

## 2025-02-28 - [DoS in file upload handling]
**Vulnerability:** The `_safe_upload_filename` function used `filename.replace`, `PurePosixPath`, and `re.sub` on unbounded client input, making it vulnerable to ReDoS or CPU/memory exhaustion (DoS) when fed extremely long strings.
**Learning:** Even fast standard library functions like `PurePosixPath` and string replacements can cause significant lag when chained on strings in the megabytes. String processing operations should always bound their inputs first if the input is untrusted and can be arbitrarily large.
**Prevention:** Cap the length of client-provided filename strings early by slicing them (e.g. `filename = filename[-512:]`) before doing more complex string parsing or regex replacements, especially when only the basename suffix is relevant.

## 2026-08-14 - [CRITICAL] PDF 구조 검증 시 예외 처리 미흡으로 인한 DoS 취약점 해결
**Vulnerability:** 파일 파싱 엔드포인트(`/parse`)에서 `PdfReader`를 사용해 PDF 구조를 검증할 때, `PdfReadError`, `RecursionError` 등 특정 예외만 처리하고 있었습니다. 잘못된 형식의 파일이 입력되었을 때 `MemoryError`나 `TypeError` 같은 예상치 못한 예외가 발생할 경우, 이는 핸들링되지 않아 500 HTTP 상태 코드를 반환하게 되고, 이는 Strix 보안 스캐너에서 치명적인 서비스 거부(DoS) 취약점으로 간주됩니다.
**Learning:** 구조 검증 라이브러리(예: `PdfReader`)는 악의적으로 조작된 파일에 대해 예상치 못한 다양한 예외를 발생시킬 수 있습니다. 한정된 예외만 처리할 경우 엣지 케이스를 놓치고 어플리케이션 안정성을 해칠 수 있습니다.
**Prevention:** 외부 구조 검증 라이브러리의 호출을 광범위한 `except Exception:` 블록으로 감싸서 500 에러 발생을 방지하고 적절한 4xx 에러(예: 415 Unsupported Media Type)로 처리되도록 하여 DoS를 예방해야 합니다.
