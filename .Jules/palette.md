# Palette's UX/A11y Journal

## 2026-06-27 - OpenAPI Contact and License Metadata
**Learning:** Contact and license metadata in generated OpenAPI documents helps API consumers quickly identify maintainers, support paths, and reuse terms without leaving the docs surface.
**Action:** Include clear `contact` and SPDX-aligned `license_info` metadata when maintaining FastAPI services intended for third-party integration.

## 2026-06-26 - Backend Services UX via OpenAPI Documentation
**Learning:** For backend-only services without a frontend UI, Developer Experience (DX) is the primary user experience. OpenAPI/Swagger documentation generated from Pydantic models plays a crucial role in providing a usable and intuitive interface for developers consuming the API.
**Action:** Enhance Pydantic model properties with detailed `description` fields using `Field()` to automatically generate rich, self-documenting OpenAPI schemas for developers.

## 2026-06-02 - OpenAPI/Swagger Tagging Grouping
**Learning:** Organizing API endpoints using `openapi_tags` significantly improves the readability of Swagger UI by logically grouping related endpoints (e.g., `Parser` vs `System`). This structural enhancement improves the Developer Experience (DX) for consumers of headless APIs.
**Action:** Always assign descriptive metadata to endpoints and utilize `openapi_tags` when building or enhancing FastAPI applications.

## 2026-06-01 - [Developer Experience as UX for APIs]
**Learning:** For backend-only services without a UI, UX is represented by Developer Experience (DX), specifically the OpenAPI/Swagger documentation.
**Action:** Enhance the Swagger UI for the API with a description and version to make it more intuitive and pleasant to use for developers.

## 2025-03-01 - Enhance OpenAPI/Swagger DX for Headless API
**Learning:** For a backend-only headless API where there is no frontend UI, the OpenAPI/Swagger documentation page acts as the primary user interface. Improving metadata such as `summary`, `description`, and parameter descriptions significantly improves Developer Experience (DX) and makes the API much more intuitive and accessible for developers testing or integrating the service.
**Action:** When working on backend-only services, prioritize adding rich, clear OpenAPI metadata (titles, descriptions, summaries, file parameter descriptions) to endpoints. This provides the most significant "UX" value for these types of repositories.
## 2024-05-18 - Preserve required field status in Pydantic V2 schemas for OpenAPI
**Learning:** When using Pydantic V2 schemas and FastAPI `File` dependency for OpenAPI documentation with `description` properties, `Field(description="...")` will silently mark fields as optional (not required) in the generated OpenAPI specs since there's an implicit `default=None` when `default` or `default_factory` are not defined.
**Action:** Always explicitly use `Field(..., description="...")` (or `File(..., description="...")`) to properly preserve the required status for mandatory API fields and enhance Developer Experience (DX).
## 2024-05-18 - Improve Swagger UI DX with swagger_ui_parameters
**Learning:** The default Swagger UI configuration for FastAPI applications often lacks helpful features like request duration display or dark-themed syntax highlighting, and requires users to manually click "Try it out" for every endpoint.
**Action:** Always configure `swagger_ui_parameters` in the `FastAPI()` instantiation with options like `{"displayRequestDuration": True, "syntaxHighlight.theme": "monokai", "tryItOutEnabled": True}` to significantly improve the Developer Experience (DX) when interacting with the API documentation.
## 2025-02-17 - Improve OpenAPI DX
**Learning:** For backend-only services without UI, the Developer Experience (DX) via OpenAPI docs is the primary user experience. Adding Pydantic examples and omitting unnecessary explicit ellipses (`...`) makes schemas cleaner and APIs significantly more intuitive.
**Action:** Always enrich Pydantic schemas with examples to improve OpenAPI visualization in FastAPI.
