1. **Analyze Security Needs:**
   - I observed that the `parse` endpoint accepts files explicitly sent with the `application/pdf` Content-Type but it does not validate the magic bytes of the actual content. This means someone could send a malicious file (like an executable, `MZ...`) but claim it is a PDF using the HTTP header, which bypasses the `Content-Type` check. This is an insecure file upload handling vulnerability.
   - The checklist (`docs/security/api-security-checklist.md`) requires: `validate upload handling and content-type expectations for /parse`.

2. **Implement Security Fix in `src/newsdom_api/main.py`:**
   - Modify the `parse` function to explicitly check the magic bytes (`%PDF-`) of the uploaded file bytes before sending it to `parse_pdf_bytes`.
   - If the file does not start with `b"%PDF-"`, raise a `415 Unsupported Media Type` (or `422 Unprocessable Entity`) indicating that the file content does not match the expected PDF format. We will use `415 Unsupported Media Type` to be consistent with the existing Content-Type check.

3. **Write Tests:**
   - Add a test in `tests/test_parse_endpoint.py` to ensure that uploads with invalid magic bytes are rejected, even if the Content-Type header is `application/pdf`.

4. **Verify Fix:**
   - Run the test suite and ensure it passes, confirming the vulnerability is fixed.

5. **Pre-commit and PR Submission:**
   - Run `pre_commit_instructions` and format files.
   - Submit PR with the title formatted for Sentinel.
