# Palette's UX/A11y Journal

## Automated-agent coordination

Before starting work, check this journal and the repository's open pull
requests. Do not open a PR for an issue that already has an open PR or a
journal entry marked **In progress**. Pick a different topic instead, and
keep one PR per distinct issue.

## 2024-05-18 - Preserve required field status in Pydantic v2 schemas
**Learning:** In Pydantic v2 schemas and FastAPI `File` dependencies, adding a `description` without an explicit default can silently mark a field as optional in generated OpenAPI specifications.
**Action:** Use `Field(..., description="...")` or `File(..., description="...")` for mandatory fields so OpenAPI preserves required status.

## 2024-05-18 - Improve Swagger UI developer experience
**Learning:** Default Swagger UI lacks helpful features such as request-duration display, dark syntax highlighting, and automatic Try It Out behavior.
**Action:** Configure `swagger_ui_parameters` with options such as `displayRequestDuration`, `syntaxHighlight.theme`, and `tryItOutEnabled` when they improve the API documentation experience.

## 2025-03-01 - Enhance OpenAPI/Swagger DX for a headless API
**Learning:** For a backend-only service without a frontend UI, the OpenAPI/Swagger page is the primary user interface. Rich `summary`, `description`, version, parameter descriptions, and file-parameter guidance improve the developer experience for consumers.
**Action:** Prioritize clear, useful API metadata when maintaining a headless API so the documentation surface is intuitive for developers.

## 2026-06-02 - Group OpenAPI/Swagger tags
**Learning:** Organizing API endpoints with `openapi_tags` improves Swagger UI readability by grouping related endpoints such as `Parser` and `System`.
**Action:** Assign descriptive metadata to endpoints and use `openapi_tags` when enhancing a FastAPI application.

## 2026-06-26 - Document backend services through OpenAPI
**Learning:** For backend-only services without a frontend UI, developer experience is the primary user experience. OpenAPI/Swagger documentation generated from Pydantic models should be usable and intuitive for developers consuming the service.
**Action:** Enhance Pydantic model properties with detailed `Field()` descriptions to generate rich, self-documenting OpenAPI schemas.

## 2026-06-27 - Add OpenAPI contact and license metadata
**Learning:** Contact and license metadata in generated OpenAPI documents helps consumers identify maintainers, support paths, and reuse terms without leaving the documentation surface.
**Action:** Include clear `contact` and SPDX-aligned `license_info` metadata for FastAPI services intended for third-party integration.

## 2026-07-07 - Use Pydantic v2 schema examples
**Learning:** In a backend-only FastAPI project, UX naturally translates to developer experience. OpenAPI/Swagger documentation is the primary interface, so representative examples provide immediate value. `json_schema_extra={"example": ...}` is preferable to description-only documentation, deprecated plural `examples`, or the deprecated `example=...` form in Pydantic v2. Explicitly defining `...` is redundant and noisy when no default is provided.
**Action:** Apply `json_schema_extra` to Pydantic field definitions, include rich documentation and representative examples, and omit redundant required-field ellipses when Pydantic can infer requiredness.
**Source note:** The `.jules/palette.md` source included an unevaluated `$(date +%Y-%m-%d)` placeholder. Its date is unclear; the earliest credible date for this duplicate issue is retained here.
