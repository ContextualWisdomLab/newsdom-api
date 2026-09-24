## $(date -u +%Y-%m-%d) - Fix 폼 필드 길이 제한 누락 취약점
**Vulnerability:** `src/newsdom_api/main.py`의 `/parse` 엔드포인트에서 `language`, `mode` 등 `Form` 파라미터에 `max_length`가 누락되어 있어, 악의적인 대용량 문자열이 메모리를 고갈시킬 수 있는 Denial of Service(DoS) 위험이 있었습니다.
**Learning:** `python-multipart`는 경로 실행 전에 전체 폼 데이터를 메모리에 로드하므로, 경계를 두지 않은 문자열 입력 필드는 애플리케이션의 메모리를 소모시키는 공격 벡터로 악용될 수 있습니다.
**Prevention:** 텍스트를 받는 모든 FastAPI의 `Form` 의존성에는 명시적으로 `max_length`를 지정하여 메모리 할당 상한을 엄격하게 통제해야 합니다.
