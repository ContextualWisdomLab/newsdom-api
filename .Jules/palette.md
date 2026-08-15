# Palette's UX/A11y Journal

## 2026-06-27 - OpenAPI Contact and License Metadata
**Learning:** Contact and license metadata in generated OpenAPI documents helps API consumers quickly identify maintainers, support paths, and reuse terms without leaving the docs surface.
**Action:** Include clear `contact` and SPDX-aligned `license_info` metadata when maintaining FastAPI services intended for third-party integration.

## 2026-06-26 - Backend Services UX via OpenAPI Documentation
**Learning:** For backend-only services without a frontend UI, Developer Experience (DX) is the primary user experience. OpenAPI/Swagger documentation generated from Pydantic models plays a crucial role in providing a usable and intuitive interface for developers consuming the API.
**Action:** Enhance Pydantic model properties with detailed `description` fields using `Field()` to automatically generate rich, self-documenting OpenAPI schemas for developers.

## 2026-06-02 - OpenAPI/Swagger Tagging Grouping
**Learning:** Organizing API endpoints using `openapi_tags` significantly improves the readability of Swagger UI by logically grouping related endpoints (e.g. `Parser` vs `System`). This structural enhancement improves the Developer Experience (DX) for consumers of headless APIs.
**Action:** Always assign descriptive metadata to endpoints and utilize `openapi_tags` when building or enhancing FastAPI applications.

## 2026-06-01 - [Developer Experience as UX for APIs]
**Learning:** For backend-only services without a UI, UX is represented by Developer Experience (DX), specifically the OpenAPI/Swagger documentation.
**Action:** Enhance the Swagger UI for the API with a description and version to make it more intuitive and pleasant to use for developers.

## 2025-03-01 - Enhance OpenAPI/Swagger DX for Headless API
**Learning:** For a backend-only headless API where there is no frontend UI, the OpenAPI/Swagger documentation page acts as the primary user interface. Improving metadata such as `summary`, `description`, and parameter descriptions significantly improves Developer Experience (DX) and makes the API much more intuitive and accessible for developers testing or integrating the service.
**Action:** When working on backend-only services, prioritize adding rich, clear OpenAPI metadata (titles, descriptions, summaries, file parameter descriptions) to endpoints. This provides the most significant UX value for these types of repositories.

## 2024-05-18 - Preserve required field status in Pydantic V2 schemas for OpenAPI
**Learning:** When using Pydantic V2 schemas and FastAPI `File` dependency for OpenAPI documentation with `description` properties, `Field(description="...")` can silently mark fields as optional when no explicit required default is present.
**Action:** Explicitly use `Field(..., description="...")` or `File(..., description="...")` for mandatory API fields and verify the generated OpenAPI required array.

## 2024-05-18 - Improve Swagger UI DX with swagger_ui_parameters
**Learning:** The default Swagger UI configuration for FastAPI applications often lacks helpful features like request duration display and requires users to manually click "Try it out" for every endpoint.
**Action:** Configure only reviewed Swagger UI parameters that improve task completion without introducing remote assets or weakening the API security boundary.

## 2026-07-07 - [Use current JSON Schema examples metadata]
**Learning:** OpenAPI 3.1 aligns Schema Objects with JSON Schema Draft 2020-12. The singular Schema Object `example` field is retained for compatibility but deprecated; the standard `examples` array is preferred.
**Action:** Use FastAPI/Pydantic `examples=[...]` for schema-level examples and verify the generated `/openapi.json` document rather than relying on source declarations alone.

## 2026-08-15 - [Improve DX for multipart form parameters]
**Learning:** A headless API's generated OpenAPI document is a buyer-facing interface. Optional multipart form fields need realistic, schema-compatible examples, but the metadata must follow the current OpenAPI/JSON Schema contract.
**Action:** Add `examples=[...]` to FastAPI `Form` declarations and lock the emitted multipart request schema with an exact contract test. Do not add a filename example that implies browsers can pre-populate a local file picker.
