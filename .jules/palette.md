## $(date +%Y-%m-%d) - Enhance Developer UX with OpenAPI Schema Examples
**Learning:** In a backend-only FastAPI project without frontend files, "UX" improvements naturally translate to Developer Experience (DX). Enhancing Pydantic schemas with `json_schema_extra={"example": ...}` rather than just using the `description` field or deprecated plural `examples` provides concrete, immediate value in the generated Swagger UI. Additionally, explicitly defining the ellipsis `...` for required fields is redundant and noisy in modern Pydantic V2 when no default is provided.
**Action:** When working on API schemas, proactively provide representative `json_schema_extra` examples to improve the consumer documentation experience, and omit the `...` default marker to keep schema declarations clean and idiomatic.

## 2026-07-31 - OpenAPI 스키마 DX 개선
**Learning:** 백엔드 전용 FastAPI 프로젝트에서는 OpenAPI/Swagger UI에 풍부한 예시(example) 데이터를 제공하는 것이 개발자 경험(DX)을 향상시키는 핵심적인 UX 개선이다. Pydantic 모델 필드에 `json_schema_extra`를 추가하면 API 사용자가 문서만으로도 응답 형식을 직관적으로 이해할 수 있다.
**Action:** API 응답 스키마(ParseQuality, HealthResponse 등)를 작성할 때, 기본값 외에도 실제 사용 시 반환될 수 있는 현실적인 데이터를 `json_schema_extra={"example": ...}` 형태로 반드시 명시한다.
