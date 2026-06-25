## 2025-02-14 - Fix Insecure File Upload via Missing Magic Byte Check
**Vulnerability:** The `/parse` endpoint verified file types exclusively using the `Content-Type` header, omitting payload inspection. This allowed bypassing checks by supplying malicious payloads with an `application/pdf` header.
**Learning:** Checking headers is insufficient; APIs consuming binary data must validate content via magic bytes (e.g., `b"%PDF-"`) to ensure structural expectations are met before processing.
**Prevention:** Always inspect magic bytes for binary upload endpoints. Ensure FastAPI upload models are paired with byte-level validation for security boundaries.

## 2026-06-25 - XSS Vulnerability in MinerU Block Text Extraction
**Vulnerability:** The `_block_text` function in `src/newsdom_api/dom_builder.py` returned raw user-controlled text from MinerU blocks without HTML encoding. When this DOM payload was subsequently rendered in frontend web views, any embedded `<script>` tags would execute, creating a DOM-based Cross-Site Scripting (XSS) vulnerability.
**Learning:** Downstream renderers inherently trust API payloads unless strictly typed. When an API aggregates raw string content from external, untrusted parsers (like MinerU on user-provided PDFs), it must treat the content as malicious.
**Prevention:** All text extraction pathways (e.g. `_block_text`) that emit strings into canonical DOM models intended for generic rendering must HTML-escape the text (using `html.escape` or similar standard-library sanitization) at the boundary before inclusion in the response schema.
