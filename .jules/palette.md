## $(date +%Y-%m-%d) - Enhance Developer UX with OpenAPI Schema Examples

**Learning:** In a backend-only FastAPI project without frontend files, "UX" improvements naturally translate to Developer Experience (DX). Enhancing Pydantic schemas with `json_schema_extra={"example": ...}` rather than just using the `description` field or deprecated plural `examples` provides concrete, immediate value in the generated Swagger UI. Additionally, explicitly defining the ellipsis `...` for required fields is redundant and noisy in modern Pydantic V2 when no default is provided.
**Action:** When working on API schemas, proactively provide representative `json_schema_extra` examples to improve the consumer documentation experience, and omit the `...` default marker to keep schema declarations clean and idiomatic.

## 2026-08-04 - Backend API Developer Experience

**Learning:** 백엔드 전용 프로젝트(프론트엔드가 없는 경우)에서는 'UX(사용자 경험)'가 주로 'DX(개발자 경험)'로 해석됩니다. OpenAPI/Swagger 스키마에 `json_schema_extra={"example": ...}`와 같은 구체적인 예시를 추가하면 API를 사용하는 개발자들의 인터페이스 이해도를 높일 수 있습니다.
**Action:** 향후 백엔드 API 중심의 프로젝트에서는 Pydantic 스키마 정의에 풍부한 문서화와 예제 데이터가 포함되어 있는지 확인하여 개발자 경험을 개선할 것입니다.
## 2026-08-08 - 백엔드 전용 API 환경에서의 DX 개선(OpenAPI Schema)
**Learning:** 프론트엔드가 없는 백엔드 전용 FastAPI 서비스에서는 '사용자 경험(UX)'이 사실상 API 사용자(개발자)를 위한 '개발자 경험(DX)'을 의미합니다. Swagger UI 등에 노출되는 Pydantic 모델에 명시적인 `json_schema_extra` 예시(example) 데이터를 추가하면, 사용자가 요청/응답 형태를 더 쉽고 정확하게 파악할 수 있어 DX가 크게 향상된다는 점을 배웠습니다.
**Action:** 향후 백엔드 API 중심의 프로젝트에서 UX 개선 과제가 주어질 경우, 프론트엔드 변경을 억지로 시도하기보다는 OpenAPI 문서, Pydantic 모델, Swagger UI를 위한 예시 데이터 및 명확한 에러 메시지 제공 등을 최우선으로 검토하고 적용하겠습니다.
