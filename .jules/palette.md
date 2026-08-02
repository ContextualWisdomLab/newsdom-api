## $(date +%Y-%m-%d) - Enhance Developer UX with OpenAPI Schema Examples
**Learning:** In a backend-only FastAPI project without frontend files, "UX" improvements naturally translate to Developer Experience (DX). Enhancing Pydantic schemas with `json_schema_extra={"example": ...}` rather than just using the `description` field or deprecated plural `examples` provides concrete, immediate value in the generated Swagger UI. Additionally, explicitly defining the ellipsis `...` for required fields is redundant and noisy in modern Pydantic V2 when no default is provided.
**Action:** When working on API schemas, proactively provide representative `json_schema_extra` examples to improve the consumer documentation experience, and omit the `...` default marker to keep schema declarations clean and idiomatic.
## 2026-08-02 - OpenAPI 스키마 예제 추가
**Learning:** 백엔드 전용 FastAPI 프로젝트에서 Pydantic 스키마에 json_schema_extra를 추가하면 OpenAPI 문서의 가독성이 크게 향상되어 개발자 경험(DX)이 개선됨을 확인했다.
**Action:** 향후 새로운 스키마나 필드가 추가될 때 json_schema_extra를 이용해 구체적인 예제(example)를 기본적으로 포함하도록 한다.
