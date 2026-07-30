## $(date +%Y-%m-%d) - Enhance Developer UX with OpenAPI Schema Examples
**Learning:** In a backend-only FastAPI project without frontend files, "UX" improvements naturally translate to Developer Experience (DX). Enhancing Pydantic schemas with `json_schema_extra={"example": ...}` rather than just using the `description` field or deprecated plural `examples` provides concrete, immediate value in the generated Swagger UI. Additionally, explicitly defining the ellipsis `...` for required fields is redundant and noisy in modern Pydantic V2 when no default is provided.
**Action:** When working on API schemas, proactively provide representative `json_schema_extra` examples to improve the consumer documentation experience, and omit the `...` default marker to keep schema declarations clean and idiomatic.
## 2026-07-30 - OpenAPI Schema Developer Experience 강화
**Learning:** 백엔드 전용 FastAPI 프로젝트에서는 프론트엔드 UI 대신 OpenAPI/Swagger UI가 개발자 경험(DX)의 핵심이며, Pydantic 스키마에 명시적인 `example`을 추가하면 API 사용자의 이해도와 사용성이 크게 향상됨을 확인했습니다.
**Action:** 향후 백엔드 API 개발 시, 모든 Pydantic 모델의 `Field`에 `json_schema_extra={"example": ...}` 속성을 기본적으로 포함하여 풍부한 API 문서를 제공하도록 합니다.
