## 2025-02-28 - Avoid 500 Errors in `hmac.compare_digest` with Non-ASCII Headers
**Vulnerability:** Passing non-ASCII strings to `hmac.compare_digest()` raises a `TypeError`, leading to a 500 Internal Server Error (DoS). This is possible when evaluating an `Authorization` header provided by an attacker.
**Learning:** `hmac.compare_digest()` only supports comparing bytes or ASCII-only strings. The Python standard library explicitly throws an exception when non-ASCII inputs are encountered.
**Prevention:** Always encode strings to bytes (e.g., using `.encode("utf-8")`) before using `hmac.compare_digest()` on arbitrary user inputs (like HTTP headers).
