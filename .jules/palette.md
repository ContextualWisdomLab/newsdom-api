## $(date +%Y-%m-%d) - Enhance Developer UX with OpenAPI Schema Examples

**Learning:** In a backend-only FastAPI project without frontend files, "UX" improvements naturally translate to Developer Experience (DX). Enhancing Pydantic schemas with `json_schema_extra={"example": ...}` rather than just using the `description` field or deprecated plural `examples` provides concrete, immediate value in the generated Swagger UI. Additionally, explicitly defining the ellipsis `...` for required fields is redundant and noisy in modern Pydantic V2 when no default is provided.
**Action:** When working on API schemas, proactively provide representative `json_schema_extra` examples to improve the consumer documentation experience, and omit the `...` default marker to keep schema declarations clean and idiomatic.

## 2026-08-04 - Backend API Developer Experience

**Learning:** 백엔드 전용 프로젝트에서는 Swagger UI와 OpenAPI 스키마도 실제 사용자 인터페이스입니다. 예제와 설명은 개발자가 계약을 이해하는 데 직접 영향을 주므로, Pydantic 스키마의 실제 제약과 어긋나지 않는 범위에서 구체적으로 제공해야 합니다.
**Action:** API 스키마를 바꿀 때는 생성된 OpenAPI와 `/docs` 동작을 함께 검증하고, 예제 데이터가 실제 검증 규칙을 통과하는지 확인합니다.

## 2026-09-01 - Swagger UI authorization persistence

**Learning:** Swagger UI의 `persistAuthorization`은 새로고침 뒤에도 인증 값을 유지하지만 기본값은 `false`입니다. 개발 편의를 위해 이를 켜더라도 운영·공용 브라우저까지 일괄 적용하면 Bearer 토큰의 브라우저 잔존 범위를 불필요하게 늘립니다. 또한 FastAPI 기본 Swagger UI는 외부 정적 자산과 인라인 초기화 스크립트를 사용하므로 `default-src 'none'`만 적용하면 UI 자체가 실행되지 않습니다.
**Action:** `persistAuthorization`은 명시적 development runtime에서만 활성화합니다. `/docs`에 필요한 CSP 예외는 문서 경로에만 한정하고, API 응답의 기본 `default-src 'none'` 경계는 유지합니다. 설정 변경은 생성된 Swagger HTML, CSP 헤더, 비문서 경로의 보안 헤더 회귀 테스트로 검증합니다.
