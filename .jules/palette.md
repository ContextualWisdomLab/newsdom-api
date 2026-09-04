## $(date +%Y-%m-%d) - Enhance Developer UX with OpenAPI Schema Examples

**Learning:** In a backend-only FastAPI project without frontend files, "UX" improvements naturally translate to Developer Experience (DX). Enhancing Pydantic schemas with `json_schema_extra={"example": ...}` rather than just using the `description` field or deprecated plural `examples` provides concrete, immediate value in the generated Swagger UI. Additionally, explicitly defining the ellipsis `...` for required fields is redundant and noisy in modern Pydantic V2 when no default is provided.
**Action:** When working on API schemas, proactively provide representative `json_schema_extra` examples to improve the consumer documentation experience, and omit the `...` default marker to keep schema declarations clean and idiomatic.

## 2026-08-04 - Backend API Developer Experience

**Learning:** 백엔드 전용 프로젝트(프론트엔드가 없는 경우)에서는 'UX(사용자 경험)'가 주로 'DX(개발자 경험)'로 해석됩니다. OpenAPI/Swagger 스키마에 `json_schema_extra={"example": ...}`와 같은 구체적인 예시를 추가하면 API를 사용하는 개발자들의 인터페이스 이해도를 높일 수 있습니다.
**Action:** 향후 백엔드 API 중심의 프로젝트에서는 Pydantic 스키마 정의에 풍부한 문서화와 예제 데이터가 포함되어 있는지 확인하여 개발자 경험을 개선할 것입니다.

## 2026-07-08 - Preserve required field status in FastAPI File dependencies with Pydantic V2
**Learning:** When using FastAPI's `File` dependency for OpenAPI documentation with `description` properties, `File(..., description="...")` ensures the field is explicitly marked as required (not optional). Adding `json_schema_extra=...` inside `File` (like `File(..., description="...", json_schema_extra=...)`) is not natively supported directly by FastAPI's File wrapper in older versions or can cause parsing errors if not done properly via Pydantic annotations.
**Action:** However, looking at the repo we just successfully preserved the required status without modifying the file since it was already `File(..., description="...")`. My modification was to add `json_schema_extra` to the `Annotated[UploadFile, File(...)]` but `FastAPI` file upload swagger actually doesn't strictly need a sample example as the UI natively handles file uploads. I'll revert it, actually I did revert it. But wait, I DID modify `src/newsdom_api/main.py`. I changed `File(..., description="...")` to include `json_schema_extra=...` but actually the replace statement didn't do anything because the target string was missing an ending parenthesis in the replace script. Wait, my replace did nothing because it was identical.
