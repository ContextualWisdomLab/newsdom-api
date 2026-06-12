## 2024-06-12 - Improve auto-generated Swagger UI metadata
**Learning:** For backend-only API repositories like `newsdom-api` without a frontend UI, UX enhancements should focus on Developer Experience (DX) by improving auto-generated OpenAPI/Swagger documentation metadata.
**Action:** Always enrich FastAPI applications by adding `title`, `description`, and `version` to the `FastAPI` app instance, and assigning `tags`, `summary`, and parameter descriptions to endpoint decorators to improve the API consumer experience.
