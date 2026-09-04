## $(date +%Y-%m-%d) - Enhance Developer UX with OpenAPI Schema Examples

**Learning:** In a backend-only FastAPI project without frontend files, "UX" improvements naturally translate to Developer Experience (DX). Enhancing Pydantic schemas with `json_schema_extra={"example": ...}` rather than just using the `description` field or deprecated plural `examples` provides concrete, immediate value in the generated Swagger UI. Additionally, explicitly defining the ellipsis `...` for required fields is redundant and noisy in modern Pydantic V2 when no default is provided.
**Action:** When working on API schemas, proactively provide representative `json_schema_extra` examples to improve the consumer documentation experience, and omit the `...` default marker to keep schema declarations clean and idiomatic.

## 2026-08-04 - Backend API Developer Experience

**Learning:** 백엔드 전용 프로젝트(프론트엔드가 없는 경우)에서는 'UX(사용자 경험)'가 주로 'DX(개발자 경험)'로 해석됩니다. OpenAPI/Swagger 스키마에 `json_schema_extra={"example": ...}`와 같은 구체적인 예시를 추가하면 API를 사용하는 개발자들의 인터페이스 이해도를 높일 수 있습니다.
**Action:** 향후 백엔드 API 중심의 프로젝트에서는 Pydantic 스키마 정의에 풍부한 문서화와 예제 데이터가 포함되어 있는지 확인하여 개발자 경험을 개선할 것입니다.

## 2026-09-02 - Persist Authorization in Swagger UI
**Learning:** FastAPI의 Swagger UI에서 인증 토큰(Bearer Token 등)은 페이지를 새로고침할 때마다 초기화되어 개발자 경험(DX)을 저해합니다.
**Action:** `swagger_ui_parameters`에 `"persistAuthorization": True`를 추가하여 인증 상태가 유지되도록 함으로써 API 테스트 시 반복적인 토큰 입력의 번거로움을 해결해야 합니다. 단, 브라우저 스토리지에 자격증명이 영구 저장되는 보안 위험을 방지하기 위해 이 설정은 `runtime_profile="development"`와 같이 명시적인 로컬 개발 환경에서만 활성화되어야 하며, `/docs` 경로에 한정하여 최소한의 CSP를 적용해 다른 API 응답의 보안 정책이 약화되지 않도록 주의해야 합니다.
