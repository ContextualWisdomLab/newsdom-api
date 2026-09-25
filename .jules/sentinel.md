# Sentinel's Security Journal

## Automated-agent coordination

Before starting work, check this journal and the repository's open pull
requests. Do not open a PR for an issue that already has an open PR or a
journal entry marked **In progress**. Pick a different topic instead, and
keep one PR per distinct issue.

## In progress

- Token-comparison timing issue (src/newsdom_api/main.py): canonical PR #790; other open duplicates are being closed.

## 2023-10-27 - Fix naive absolute path traversal protection
**Vulnerability:** The codebase rejected all absolute paths indiscriminately (for example, using `is_absolute()`) rather than whitelist-validating them, causing CI breakages when legitimate absolute paths within safe temporary directories were provided.
**Learning:** Naively blocking absolute paths can disrupt legitimate CI and test automation tools that rely on paths pointing to temporary system directories such as `/tmp`.
**Prevention:** Rather than rejecting all absolute paths out of hand, allow them when validated to fall within a safe directory whitelist such as `tempfile.gettempdir()`, preventing arbitrary file writes while supporting standard testing mechanisms.

## 2024-05-24 - Fix temporary-file cleanup to prevent DoS via disk exhaustion
**Vulnerability:** Incomplete temporary-file cleanup on asynchronous file uploads could leave files orphaned when a client disconnected or an exception occurred before or during the read loop, causing disk exhaustion.
**Learning:** Context managers and nested cleanup blocks are insufficient when manual temporary-file persistence (`delete=False`) is used with asynchronous streams; cleanup must cover file creation, initialization, the entire read loop, and processing regardless of where failure occurs.
**Prevention:** Initialize `tmp_path = None` before the main `try` block, create the temporary file and perform network reads inside that block, and unlink the path in `finally` with a guard such as `if tmp_path and tmp_path.exists(): tmp_path.unlink(missing_ok=True)`.

## 2024-06-25 - Prevent DoS from unbounded file read
**Vulnerability:** The `/parse` API read the entire uploaded PDF into memory using `await file.read()`. A massive upload could cause an out-of-memory error and denial of service.
**Learning:** `UploadFile.read()` loads the entire file into memory unless limited. Even when FastAPI initially spools the upload to disk, calling `.read()` buffers it fully before MinerU processes it.
**Prevention:** Implement an application-level file-size limit during the upload read process using `file.size`.

## 2025-02-14 - Fix insecure file upload via missing magic-byte check
**Vulnerability:** The `/parse` endpoint verified file types exclusively using the `Content-Type` header, omitting payload inspection. This allowed malicious payloads to bypass checks by supplying an `application/pdf` header.
**Learning:** Headers are insufficient for binary uploads; APIs must validate magic bytes such as `b"%PDF-"` and perform structural parsing before processing.
**Prevention:** Inspect magic bytes for binary upload endpoints and reject structurally invalid payloads before handing data to downstream parsers.

## 2025-02-14 - Prevent unsafe upload filenames
**Vulnerability:** Client-supplied filenames were used to name temporary files passed to the MinerU CLI. Even with `shell=False`, weak normalization could leave path traversal fragments, unsafe filesystem characters, confusing option-like names, or brittle artifact names.
**Learning:** Removing null bytes and path separators is not enough at filesystem and CLI integration boundaries; filenames should use a small, predictable character set before influencing paths or downstream arguments.
**Prevention:** Apply a strict regex allowlist such as `re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)` and cap the sanitized basename below common filesystem component limits while preserving useful extensions.

## 2025-02-28 - Prevent subprocess and log injection via newlines
**Vulnerability:** Unsanitized user inputs containing newline (`\n`) or carriage return (`\r`) characters passed as subprocess arguments could cause command or log injection, even with `shell=False`. The `_UNSAFE_CHARS_PATTERN` blocklist omitted these characters, allowing the same risk through filenames.
**Learning:** Shell metacharacter filters are insufficient when they omit whitespace control characters that downstream CLI tools or log processors may interpret line by line.
**Prevention:** Explicitly reject newline and carriage-return characters in subprocess arguments and restrict inputs to safe paths and alphanumeric characters.

## 2025-02-28 - Prevent denial of service in upload filename handling
**Vulnerability:** `_safe_upload_filename` applied `replace`, `PurePosixPath`, and `re.sub` to unbounded client input, enabling CPU or memory exhaustion when filenames were extremely long.
**Learning:** Even fast standard-library string operations can become expensive when chained over megabytes of untrusted input.
**Prevention:** Cap client-provided filename strings early, for example with `filename = filename[-512:]`, before parsing or regex replacement when only the basename suffix is relevant.

## 2025-03-01 - Prevent memory exhaustion via unbounded stream reading
**Vulnerability:** `UploadFile.read()` accumulated the remainder of large files into an in-memory `bytes` or `bytearray` even when `file.size` was bounded, creating a large contiguous allocation under load.
**Learning:** Bounding a single read is not enough for large uploads; processing the maximum permitted payload in memory can still create a resource-exhaustion vulnerability.
**Prevention:** Stream chunks such as 8192 bytes directly to a `NamedTemporaryFile` while enforcing the maximum payload size, and securely unlink the file in `finally` or when the limit is exceeded.

## 2026-06-26 - Add Referrer-Policy security header
**Vulnerability:** The API lacked a `Referrer-Policy` header, potentially leaking sensitive URL information when a user navigated to an external domain.
**Learning:** `Referrer-Policy: no-referrer` is a simple defense-in-depth measure that prevents browsers from sending the `Referer` header.
**Prevention:** Include `Referrer-Policy: no-referrer` in the global security-headers middleware so all endpoints consistently enforce this protection.

## 2026-06-30 - Disable caching for API responses
**Vulnerability:** Parsed document responses could be retained by browsers or intermediaries under default HTTP caching behavior.
**Learning:** Security headers must cover response storage as well as framing, MIME sniffing, and referrer leakage. `Cache-Control: no-store, max-age=0` explicitly opts sensitive API responses out of caching.
**Prevention:** Set a global no-store cache directive in the FastAPI security-headers middleware.

## 2026-06-30 - Suppress public HTTP exception chains
**Vulnerability:** Chaining internal parser or runtime exceptions into public `HTTPException` instances could retain dependency errors or local path fragments in traceback material.
**Learning:** API handlers should return sanitized status codes and messages while suppressing internal exception causes at the public boundary.
**Prevention:** Raise generic client-facing `HTTPException` responses with `from None` after mapping parser and runtime failures to safe details.

## 2026-06-30 - Reject option-like MinerU arguments
**Vulnerability:** User-influenced paths or executable overrides beginning with `-` could be interpreted by downstream CLI tools as options even when subprocess execution used `shell=False`.
**Learning:** Shell metacharacter filtering and argv lists reduce command injection risk, but option injection also requires rejecting leading dashes or using a supported option terminator.
**Prevention:** Reject MinerU command arguments that begin with `-` before constructing the subprocess argv.

## 2026-06-30 - Preserve security headers on 500 responses
**Vulnerability:** Unhandled FastAPI exceptions could produce sanitized 500 responses without the defense-in-depth headers applied to normal middleware responses.
**Learning:** Error response paths need explicit coverage because exception handlers can bypass or duplicate header logic differently from successful requests.
**Prevention:** Route both middleware responses and global 500 exception responses through a shared security-header helper.

## 2026-07-09 - Keep upload cleanup non-fatal and observable
**Vulnerability:** Temporary-file cleanup can fail after a successful parse because of filesystem races, antivirus locks, or platform-specific deletion semantics. Propagating cleanup exceptions can turn a successful parse into a 500 while leaving unclear forensic evidence.
**Learning:** Cleanup must be guaranteed on all upload paths, but cleanup failure handling should be isolated from the user-facing parse result and logged with enough context for operators.
**Prevention:** Run temporary-file unlinking in the endpoint `finally` block, catch `OSError`, and log the temporary path at exception level without exposing it in public API responses.
