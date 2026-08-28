## 2026-08-28 - Missing length limits on Form fields (DoS risk)
**Vulnerability:** The `/parse` endpoint in `src/newsdom_api/main.py` accepts `language` and `mode` as `Form` fields but does not impose a `max_length`. Since `python-multipart` parses all form data into memory before payload limits are evaluated, this allows a Denial-of-Service (DoS) attack via memory exhaustion if extremely large strings are submitted for these fields.
**Learning:** In FastAPI, always add `max_length` limits to textual `Form` fields (e.g., `Form(max_length=...)`) to prevent memory exhaustion DoS, even when `file.read()` processes data in chunks.
**Prevention:** Include `max_length=50` (or similar reasonable limits) in `Form` annotations for textual inputs to ensure they cannot consume excessive memory.

## 2026-08-28 - Missing length limits on Form fields (DoS risk)
**Vulnerability:** The `/parse` endpoint in `src/newsdom_api/main.py` accepts `language` and `mode` as `Form` fields but does not impose a `max_length`. Since `python-multipart` parses all form data into memory before payload limits are evaluated, this allows a Denial-of-Service (DoS) attack via memory exhaustion if extremely large strings are submitted for these fields.
**Learning:** In FastAPI, always add `max_length` limits to textual `Form` fields (e.g., `Form(max_length=...)`) to prevent memory exhaustion DoS, even when `file.read()` processes data in chunks.
**Prevention:** Include `max_length=50` (or similar reasonable limits) in `Form` annotations for textual inputs to ensure they cannot consume excessive memory.
