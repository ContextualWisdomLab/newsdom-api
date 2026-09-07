## $(date +%Y-%m-%d) - Enhance Developer UX with OpenAPI Schema Examples

**Learning:** In a backend-only FastAPI project without frontend files, "UX" improvements naturally translate to Developer Experience (DX). Enhancing Pydantic schemas with `json_schema_extra={"example": ...}` rather than just using the `description` field or deprecated plural `examples` provides concrete, immediate value in the generated Swagger UI. Additionally, explicitly defining the ellipsis `...` for required fields is redundant and noisy in modern Pydantic V2 when no default is provided.
**Action:** When working on API schemas, proactively provide representative `json_schema_extra` examples to improve the consumer documentation experience, and omit the `...` default marker to keep schema declarations clean and idiomatic.

## 2026-08-04 - Backend API Developer Experience

**Learning:** 백엔드 전용 프로젝트(프론트엔드가 없는 경우)에서는 'UX(사용자 경험)'가 주로 'DX(개발자 경험)'로 해석됩니다. OpenAPI/Swagger 스키마에 `json_schema_extra={"example": ...}`와 같은 구체적인 예시를 추가하면 API를 사용하는 개발자들의 인터페이스 이해도를 높일 수 있습니다.
**Action:** 향후 백엔드 API 중심의 프로젝트에서는 Pydantic 스키마 정의에 풍부한 문서화와 예제 데이터가 포함되어 있는지 확인하여 개발자 경험을 개선할 것입니다.

## 2026-09-07 - Swagger UI 개발자 경험(DX) 개선

**Learning:** FastAPI Swagger UI에서 `"persistAuthorization": True` 옵션을 활성화하면 페이지 새로고침 시 인증이 풀리는 현상을 방지하여 개발자 경험(DX)을 크게 향상시킬 수 있습니다. 하지만 프로덕션 환경의 보안을 유지하기 위해, 이 편의 기능은 개발 환경(예: `RuntimeProfile.DEVELOPMENT`)에서만 조건부로 활성화해야 합니다.
**Action:** 인증이 필요한 백엔드 프로젝트에서 Swagger UI를 구성할 때, 환경 변수나 런타임 프로필에 따라 `persistAuthorization`을 조건부로 활성화하여 개발 편의성과 프로덕션 보안의 균형을 맞춥니다.
