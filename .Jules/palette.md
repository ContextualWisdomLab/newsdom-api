## 2024-05-18 - Improve DX with OpenAPI Metadata
**Learning:** For backend-only services (like NewsDOM API), the primary "UI" for developers is often the auto-generated Swagger/OpenAPI documentation. Missing descriptions, versions, tags, and parameter details lead to a poorer developer experience (DX).
**Action:** Consistently add metadata (description, version, tags, summary) to FastAPI app initializations and endpoint definitions to create a richer, more accessible developer interface.
