## 2026-06-11 - Developer Experience (DX) as UX in APIs
**Learning:** In backend-only API repositories without a frontend UI, UX enhancements should focus on Developer Experience (DX) through auto-generated OpenAPI/Swagger documentation metadata.
**Action:** Always enrich the FastAPI app instance with `title`, `description`, and `version`, and assign `tags`, `summary`, and parameter descriptions to endpoint decorators to make the API intuitive and accessible for developers.
