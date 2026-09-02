# 시스템 환경 및 설치 가이드

이 문서는 **NewsDOM API 자체**를 개발·검증하기 위한 설치 절차를 설명합니다. 현재 소스의 legacy MinerU adapter는 별도 parser runtime을 호출하지만, MinerU 3.x의 추가 상업 라이선스 조건은 ContextualWisdomLab의 unrestricted commercial-inbound 정책과 호환되지 않습니다. 따라서 이 문서는 MinerU 설치를 지원 경로로 안내하지 않습니다. 대체 parser boundary는 [#671](https://github.com/ContextualWisdomLab/newsdom-api/issues/671)에서 추적합니다.

## 시스템 요구사항

- **Python**: Required: `>=3.10, <3.14`
- **운영체제**: Linux, macOS, Windows의 지원 Python 환경
- **패키지 관리자**: `uv`
- **NewsDOM 의존성**: `pyproject.toml` / `uv.lock`이 권위 있는 설치 계약

GPU, OCR model, parser model weight는 NewsDOM 자체 설치 요구사항으로 간주하지 않습니다. 승인된 parser backend가 도입되면 해당 backend의 플랫폼·리소스·라이선스 요구사항을 별도 profile로 문서화해야 합니다.

## 1. 저장소 환경 설치

예시는 `python3.10`을 사용하지만, 지원 범위 안의 다른 인터프리터도 사용할 수 있습니다. `uv`를 이용한 canonical setup은 다음과 같습니다.

```bash
uv sync --frozen --all-extras
```

동일한 가상환경 위치를 직접 확인해야 하는 경우 macOS/Linux에서는 `.venv/bin/python`, Windows에서는 `.venv\Scripts\python.exe`를 사용합니다.

과거 수동 설치 예시인 `python3.10 -m venv .venv`와 `pip install -e ".[dev]"`는 호환성 참고용일 뿐 canonical repository setup이 아닙니다. 현재 검증과 CI는 lockfile 기반 `uv` 환경을 기준으로 합니다.

## 2. parser runtime 정책

현재 repository source에는 legacy MinerU adapter가 남아 있지만 다음 경로는 **상업 배포 승인 경로가 아닙니다**.

- MinerU Python package 직접 설치
- `NEWSDOM_MINERU_BIN`으로 고객이 공급한 MinerU binary 연결
- `Dockerfile.nvidia`를 이용한 MinerU-bundled image 빌드/배포
- MinerU를 별도 container/process/service로 옮긴 뒤 NewsDOM의 필수 runtime으로 사용하는 구성

이 제한은 단순 attribution 문제가 아니라 upstream의 추가 commercial threshold 조건과 조직의 inbound 정책 차이 때문입니다. MIT로 배포되는 NewsDOM 자체가 제3자 parser를 재라이선스하지 않습니다.

승인된 parser backend가 아직 없는 환경에서 `/ready`가 실패하는 것은 올바른 fail-closed 상태입니다. parser를 우회하거나 readiness를 강제로 green으로 만들지 마십시오.

## 3. 테스트와 API shell 확인

저장소 테스트를 실행합니다.

```bash
uv run pytest
```

API shell은 parser 설치 없이도 liveness, 인증 설정, 요청 계약을 개발·검증하는 데 사용할 수 있습니다.

```bash
uv run uvicorn --app-dir src newsdom_api.main:app --host 0.0.0.0 --port 8000 --reload
```

다른 터미널에서 liveness를 확인합니다.

```bash
curl -sS http://127.0.0.1:8000/health
```

정상 프로세스는 HTTP 200을 반환합니다. `/health` 성공은 parser readiness를 의미하지 않습니다. 실제 트래픽 라우팅 판단에는 `/ready`를 사용하고, 승인된 parser가 없는 동안에는 fail-closed 상태를 유지합니다.

## 4. 다음 단계

- [API 레퍼런스 및 사용 방법](api-reference.md)
- [개발 및 기여](development.md)
- [Commercial parser replacement #671](https://github.com/ContextualWisdomLab/newsdom-api/issues/671)
- [GitHub repository README](https://github.com/ContextualWisdomLab/newsdom-api)
