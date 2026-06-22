1. **Implement Security Fix in `src/newsdom_api/main.py`:** Use `replace_with_git_merge_diff` on `src/newsdom_api/main.py` to add a magic byte check. The diff will be:
```
<<<<<<< SEARCH
    try:
        pdf_bytes = await file.read()
        return await asyncio.to_thread(
            parse_pdf_bytes, pdf_bytes, filename=file.filename or "upload.pdf"
        )
=======
    try:
        pdf_bytes = await file.read()
        if not pdf_bytes.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=415, detail="Unsupported Media Type: missing PDF magic bytes"
            )
        return await asyncio.to_thread(
            parse_pdf_bytes, pdf_bytes, filename=file.filename or "upload.pdf"
        )
>>>>>>> REPLACE
```
2. **Verify Security Fix:** Run `run_in_bash_session` with `git diff src/newsdom_api/main.py` to verify the code edit.
3. **Write test:** Use `run_in_bash_session` to append a test to `tests/test_parse_endpoint.py`:
```
cat << 'EOF' >> tests/test_parse_endpoint.py

def test_parse_endpoint_rejects_missing_magic_bytes():
    client = TestClient(app)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"MZ\x90\x00\x03\x00\x00\x00", "application/pdf")},
    )
    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported Media Type: missing PDF magic bytes"
