## $(date +%Y-%m-%d) - Enhance Developer UX with OpenAPI Schema Examples
**Learning:** In a backend-only FastAPI project without frontend files, "UX" improvements naturally translate to Developer Experience (DX). Enhancing Pydantic schemas with `json_schema_extra={"example": ...}` rather than just using the `description` field or deprecated plural `examples` provides concrete, immediate value in the generated Swagger UI. Additionally, explicitly defining the ellipsis `...` for required fields is redundant and noisy in modern Pydantic V2 when no default is provided.
**Action:** When working on API schemas, proactively provide representative `json_schema_extra` examples to improve the consumer documentation experience, and omit the `...` default marker to keep schema declarations clean and idiomatic.
## 2024-07-29 - OpenAPI 스키마 예제 추가를 통한 DX 향상
**Learning:** 백엔드 전용 FastAPI 프로젝트에서는 Pydantic 스키마에 `json_schema_extra={"example": ...}`를 추가하여 OpenAPI 문서 품질을 높이는 것이 중요한 사용자 경험(DX) 향상 요소임을 확인했습니다.
**Action:** 향후 Pydantic 모델 작성 시 API 소비자의 이해를 돕기 위해 필드에 구체적인 예제 값을 기본적으로 추가하도록 합니다.
