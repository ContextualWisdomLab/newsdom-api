## $(date +%Y-%m-%d) - Enhance Developer UX with OpenAPI Schema Examples
**Learning:** In a backend-only FastAPI project without frontend files, "UX" improvements naturally translate to Developer Experience (DX). Enhancing Pydantic schemas with `json_schema_extra={"example": ...}` rather than just using the `description` field or deprecated plural `examples` provides concrete, immediate value in the generated Swagger UI. Additionally, explicitly defining the ellipsis `...` for required fields is redundant and noisy in modern Pydantic V2 when no default is provided.
**Action:** When working on API schemas, proactively provide representative `json_schema_extra` examples to improve the consumer documentation experience, and omit the `...` default marker to keep schema declarations clean and idiomatic.

## 2026-08-01 - OpenAPI 스키마 예제 추가로 DX 개선
**Learning:** 백엔드 전용 FastAPI 프로젝트에서는 Pydantic 스키마의 `json_schema_extra` 속성을 통해 OpenAPI/Swagger UI에 풍부한 예제를 제공하는 것이 훌륭한 DX(Developer Experience) 개선이 될 수 있습니다.
**Action:** 향후 백엔드 API 모델을 작성할 때 사용자 인터페이스 역할을 하는 OpenAPI 문서의 가독성을 높이기 위해 주요 필드에 항상 `example` 값을 포함할 것입니다.
