## $(date +%Y-%m-%d) - Enhance Developer UX with OpenAPI Schema Examples

**Learning:** In a backend-only FastAPI project without frontend files, "UX" improvements naturally translate to Developer Experience (DX). Enhancing Pydantic schemas with `json_schema_extra={"example": ...}` rather than just using the `description` field or deprecated plural `examples` provides concrete, immediate value in the generated Swagger UI. Additionally, explicitly defining the ellipsis `...` for required fields is redundant and noisy in modern Pydantic V2 when no default is provided.
**Action:** When working on API schemas, proactively provide representative `json_schema_extra` examples to improve the consumer documentation experience, and omit the `...` default marker to keep schema declarations clean and idiomatic.

## 2026-08-04 - Backend API Developer Experience

**Learning:** 백엔드 전용 프로젝트(프론트엔드가 없는 경우)에서는 'UX(사용자 경험)'가 주로 'DX(개발자 경험)'로 해석됩니다. OpenAPI/Swagger 스키마에 `json_schema_extra={"example": ...}`와 같은 구체적인 예시를 추가하면 API를 사용하는 개발자들의 인터페이스 이해도를 높일 수 있습니다.
**Action:** 향후 백엔드 API 중심의 프로젝트에서는 Pydantic 스키마 정의에 풍부한 문서화와 예제 데이터가 포함되어 있는지 확인하여 개발자 경험을 개선할 것입니다.
## 2024-08-30 - OpenAPI 스키마 예제 추가로 백엔드 DX 개선

**학습:** Pydantic V2 및 FastAPI 환경에서 `UploadFile` 필드에 불필요한 `...`를 제거하고, `Form` 의존성에 `json_schema_extra={"example": "ch"}`와 같이 명시적으로 추가함으로써 Swagger UI의 자동 생성 문서 품질과 개발자 경험(DX)을 크게 향상시킬 수 있음을 확인했습니다.
**실행:** 향후 API 엔드포인트를 설계할 때는 항상 OpenAPI 명세에 반영될 직관적이고 구체적인 `example` 값을 포함시키도록 합니다.
