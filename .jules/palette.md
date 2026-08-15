## $(date +%Y-%m-%d) - Enhance Developer UX with OpenAPI Schema Examples

**Learning:** In a backend-only FastAPI project without frontend files, "UX" improvements naturally translate to Developer Experience (DX). Enhancing Pydantic schemas with `json_schema_extra={"example": ...}` rather than just using the `description` field or deprecated plural `examples` provides concrete, immediate value in the generated Swagger UI. Additionally, explicitly defining the ellipsis `...` for required fields is redundant and noisy in modern Pydantic V2 when no default is provided.
**Action:** When working on API schemas, proactively provide representative `json_schema_extra` examples to improve the consumer documentation experience, and omit the `...` default marker to keep schema declarations clean and idiomatic.

## 2026-08-04 - Backend API Developer Experience

**Learning:** 백엔드 전용 프로젝트(프론트엔드가 없는 경우)에서는 'UX(사용자 경험)'가 주로 'DX(개발자 경험)'로 해석됩니다. OpenAPI/Swagger 스키마에 `json_schema_extra={"example": ...}`와 같은 구체적인 예시를 추가하면 API를 사용하는 개발자들의 인터페이스 이해도를 높일 수 있습니다.
**Action:** 향후 백엔드 API 중심의 프로젝트에서는 Pydantic 스키마 정의에 풍부한 문서화와 예제 데이터가 포함되어 있는지 확인하여 개발자 경험을 개선할 것입니다.
## 2026-08-15 - FastAPI Pydantic 모델의 OpenAPI 스키마 예제 추가
**Learning:** 프론트엔드가 없는 FastAPI 백엔드 프로젝트에서는 Pydantic 스키마(`Field`)에 `json_schema_extra={"example": ...}`를 추가하여 Swagger UI 등에서 제공되는 API 문서의 품질을 향상시키는 것이 중요한 개발자 경험(DX) 개선입니다.
**Action:** 비즈니스 로직에 영향을 주지 않으면서 API 소비자가 요청/응답 형식을 더 쉽게 이해할 수 있도록 누락된 스키마 예제를 적극적으로 추가합니다.
