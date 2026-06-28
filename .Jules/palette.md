# Palette's UX/A11y Journal

## 2026-06-02 - OpenAPI/Swagger Tagging Grouping
**Learning:** Organizing API endpoints using `openapi_tags` significantly improves the readability of Swagger UI by logically grouping related endpoints (e.g., `Parser` vs `System`). This structural enhancement improves the Developer Experience (DX) for consumers of headless APIs.
**Action:** Always assign descriptive metadata to endpoints and utilize `openapi_tags` when building or enhancing FastAPI applications.

## 2026-06-01 - [Developer Experience as UX for APIs]
**Learning:** For backend-only services without a UI, UX is represented by Developer Experience (DX), specifically the OpenAPI/Swagger documentation.
**Action:** Enhance the Swagger UI for the API with a description and version to make it more intuitive and pleasant to use for developers.

## 2025-03-01 - Enhance OpenAPI/Swagger DX for Headless API
**Learning:** For a backend-only headless API where there is no frontend UI, the OpenAPI/Swagger documentation page acts as the primary user interface. Improving metadata such as `summary`, `description`, and parameter descriptions significantly improves Developer Experience (DX) and makes the API much more intuitive and accessible for developers testing or integrating the service.
**Action:** When working on backend-only services, prioritize adding rich, clear OpenAPI metadata (titles, descriptions, summaries, file parameter descriptions) to endpoints. This provides the most significant "UX" value for these types of repositories.

## 2026-06-03 - Describe Pydantic Schema Fields for Headless API
**Learning:** Adding descriptions to Pydantic Schema Fields significantly improves Developer Experience (DX) for headless APIs by enriching the generated OpenAPI documentation.
**Action:** Always add descriptions to fields in Pydantic V2 schemas when building APIs.
