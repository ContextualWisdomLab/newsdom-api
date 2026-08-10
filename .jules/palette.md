## $(date +%Y-%m-%d) - Enhance Developer UX with OpenAPI Schema Examples

**Learning:** In a backend-only FastAPI project without frontend files, "UX" improvements naturally translate to Developer Experience (DX). Enhancing Pydantic schemas with `json_schema_extra={"example": ...}` rather than just using the `description` field or deprecated plural `examples` provides concrete, immediate value in the generated Swagger UI. Additionally, explicitly defining the ellipsis `...` for required fields is redundant and noisy in modern Pydantic V2 when no default is provided.
**Action:** When working on API schemas, proactively provide representative `json_schema_extra` examples to improve the consumer documentation experience, and omit the `...` default marker to keep schema declarations clean and idiomatic.

## 2026-08-04 - Backend API Developer Experience

**Learning:** 백엔드 전용 프로젝트(프론트엔드가 없는 경우)에서는 'UX(사용자 경험)'가 주로 'DX(개발자 경험)'로 해석됩니다. OpenAPI/Swagger 스키마에 `json_schema_extra={"example": ...}`와 같은 구체적인 예시를 추가하면 API를 사용하는 개발자들의 인터페이스 이해도를 높일 수 있습니다.
**Action:** 향후 백엔드 API 중심의 프로젝트에서는 Pydantic 스키마 정의에 풍부한 문서화와 예제 데이터가 포함되어 있는지 확인하여 개발자 경험을 개선할 것입니다.

## 2026-08-10 - OpenAPI Schema Example for List Types

**Learning:** Pydantic V2 스키마의 `List[str]`과 같은 배열 필드에도 `json_schema_extra={"example": [...]}`를 명시적으로 제공하면, 백엔드 API를 사용하는 개발자가 Swagger UI에서 빈 배열(`[]`) 대신 구체적인 데이터 형태를 바로 확인할 수 있어 개발자 경험(DX)이 크게 향상됩니다.
**Action:** 향후 스키마 작성 시 단일 값뿐만 아니라 배열이나 복합 타입에 대해서도 대표적인 예제(example) 데이터를 포함시켜 문서의 가독성과 유용성을 높일 것입니다.
