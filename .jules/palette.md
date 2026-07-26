## $(date +%Y-%m-%d) - Enhance Developer UX with OpenAPI Schema Examples
## 2025-02-27 - OpenAPI 스키마 예제(DX)
**Learning:** 프론트엔드가 없는 백엔드 전용 FastAPI 프로젝트에서는 "UX" 개선이 곧 개발자 경험(DX) 개선으로 이어집니다. Pydantic 스키마에 명시적인 `json_schema_extra={"example": ...}`(또는 `examples=[...]`)를 추가하면, 생성되는 Swagger UI 문서를 직관적이고 즉시 활용 가능하게 만들 수 있습니다.
**Action:** 백엔드 서비스의 API 스키마를 작업할 때에는 항상 대표적인 예제(`example` 값)를 추가하여 API 소비자의 문서 경험(UX/DX)을 향상시켜야 합니다.
