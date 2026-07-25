## $(date +%Y-%m-%d) - Enhance Developer UX with OpenAPI Schema Examples
**Learning:** In a backend-only FastAPI project without frontend files, "UX" improvements naturally translate to Developer Experience (DX). Enhancing Pydantic schemas with `json_schema_extra={"example": ...}` rather than just using the `description` field or deprecated plural `examples` provides concrete, immediate value in the generated Swagger UI. Additionally, explicitly defining the ellipsis `...` for required fields is redundant and noisy in modern Pydantic V2 when no default is provided.
**Action:** When working on API schemas, proactively provide representative `json_schema_extra` examples to improve the consumer documentation experience, and omit the `...` default marker to keep schema declarations clean and idiomatic.

## 2024-05-24 - OpenAPI 스키마 예제 추가
**Learning:** 백엔드 전용 프로젝트에서 UX 개선은 주로 OpenAPI/Swagger UI의 개발자 경험(DX) 개선으로 이어집니다. 스키마에 예제를 추가하면 직관성이 크게 향상됩니다.
**Action:** 앞으로 Pydantic 모델을 설계할 때는 항상 `json_schema_extra={"example": ...}`를 포함하여 API 문서의 유용성을 높일 것입니다.
