1. **Refactor `src/newsdom_api/schemas.py` and `src/newsdom_api/main.py`** to apply developer experience improvements from the `.jules/palette.md` memory.
   - In `src/newsdom_api/schemas.py`, remove the explicit ellipsis (`...`) from `headline = Field(...)` inside `ArticleNode`.
   - In `src/newsdom_api/main.py`, remove the explicit ellipsis (`...`) from `file = File(...)` inside the `parse` endpoint.
   - In `src/newsdom_api/schemas.py`, add `json_schema_extra={"example": ...}` for fields missing examples to improve the generated Swagger documentation. For example, add examples for `width`, `height`, `ads`, `headers`, `footers`, and `page_numbers` in `PageNode`.

2. **Complete pre-commit steps** to ensure proper testing, verification, review, and reflection are done. (e.g. running the full test suite).

3. **Submit the PR** with a Korean title and description.
