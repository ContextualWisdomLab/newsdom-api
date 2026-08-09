## $(date +%Y-%m-%d) - HTTP 예외 응답의 사용자 가이드 개선

**Learning:** 파일 업로드 시 발생하는 HTTP 415 (Unsupported Media Type) 및 413 (Payload Too Large) 에러의 경우, "Unsupported Media Type"처럼 단순한 에러 메시지보다는 사용자가 문제를 해결할 수 있는 구체적인 가이드(Actionable Feedback)를 제공하는 것이 더 나은 UX(DX)를 만듭니다.
**Action:** API 응답 에러 메시지 작성 시 상태 코드에 대한 기술적 설명뿐만 아니라 사용자 입장에서 "어떤 파일을 업로드해야 하는지", "어떤 크기 제한이 있는지" 등의 해결책을 포함할 것입니다.
