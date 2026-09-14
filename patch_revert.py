with open("src/newsdom_api/main.py", "r") as f:
    content = f.read()

search = """
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temporary_file:
            tmp_path = Path(temporary_file.name)

            header = await file.read(5)
            if header != b"%PDF-":
                raise HTTPException(status_code=415, detail=UNSUPPORTED_MEDIA_DETAIL)
"""

replace = """
    tmp_path: Path | None = None
    try:
        header = await file.read(5)
        if header != b"%PDF-":
            raise HTTPException(status_code=415, detail=UNSUPPORTED_MEDIA_DETAIL)

        with tempfile.NamedTemporaryFile(delete=False) as temporary_file:
            tmp_path = Path(temporary_file.name)
"""

if search in content:
    content = content.replace(search, replace)
    with open("src/newsdom_api/main.py", "w") as f:
        f.write(content)
    print("Reverted successfully")
else:
    print("Could not find search block")
