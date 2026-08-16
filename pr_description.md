🎨 Palette: OpenAPI Swagger UI 문서 내 예제 데이터(DX/UX) 추가 및 개선

💡 What:
`parse` 엔드포인트의 `language` 및 `mode` 매개변수에 대한 OpenAPI 폼 스키마에 `json_schema_extra={"example": ...}`를 추가하고, 기본값이 없는 필수 매개변수 선언에서 불필요한 `...`를 제거했습니다.

🎯 Why:
프론트엔드가 없는 백엔드 전용 API 서비스에서는 Swagger UI와 같은 API 문서가 가장 중요한 개발자 경험(DX)이자 사용자 경험(UX)입니다. 구체적인 예제 데이터를 포함하면 API 사용자들이 올바른 형식의 요청을 쉽게 테스트할 수 있습니다. 불필요한 `...` 생략을 통해 코드를 더 간결하고 일관성 있게 유지합니다.

📸 Before/After:
Before: `language` 및 `mode` 필드에 대한 예제가 Swagger UI에 나타나지 않음.
After: Swagger UI에서 `language`에는 `ch`, `mode`에는 `auto`가 예시 값으로 제공됨.

♿ Accessibility:
N/A (백엔드 API 문서 개선)

✅ Verification:
- 모든 기존 483개의 단위/통합 테스트가 성공적으로 통과했습니다.
- 소스 및 브랜치 테스트 커버리지를 100%로 완벽하게 유지했습니다.
