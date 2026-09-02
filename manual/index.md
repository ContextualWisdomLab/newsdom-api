# NewsDOM API

[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/ContextualWisdomLab/newsdom-api/badge)](https://securityscorecards.dev/viewer/?uri=github.com/ContextualWisdomLab/newsdom-api)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ContextualWisdomLab/newsdom-api)

**NewsDOM API**는 PDF를 페이지·섹션·제목·본문 블록·이미지·캡션·바운딩 박스가 있는 안정적인 DOM형 JSON으로 정규화하는 API boundary입니다. 호출자는 특정 parser 내부 구조를 해석하는 대신 NewsDOM의 HTTP·schema·안전 계약을 사용합니다.

일본어 신문 OCR은 지원해 온 사례 중 하나이지만 제품 범위는 특정 언어 또는 강제 OCR에 한정되지 않습니다. 현재 API 계약은 `language` 선택과 `mode=auto | ocr | txt`를 구분하고, `/parse`의 fail-closed 인증과 `/health`·`/ready`의 서로 다른 의미를 유지합니다.

## 현재 commercial parser 상태

NewsDOM 자체 소스는 MIT입니다. 그러나 현재 소스의 legacy MinerU adapter가 사용하는 MinerU 3.x는 Apache-2.0에 추가 commercial 조건을 둔 MinerU Open Source License를 사용하므로 ContextualWisdomLab의 unrestricted commercial-inbound 정책과 호환되지 않습니다.

따라서 MinerU package 설치, customer-supplied MinerU binary, `Dockerfile.nvidia` 기반 번들 배포를 **승인된 상업 경로로 안내하지 않습니다**. 대체 parser boundary와 검증 기준은 [#671](https://github.com/ContextualWisdomLab/newsdom-api/issues/671)에서 관리합니다. 승인된 parser가 없을 때 `/ready`가 fail-closed인 것은 정상입니다.

## 제품 경계

- `POST /parse`는 PDF 업로드와 canonical NewsDOM response 계약을 소유합니다.
- `language`과 `mode`는 request compatibility surface이며 parser implementation detail과 분리되어야 합니다.
- `/parse`는 production profile에서 fail-closed Bearer 인증을 요구합니다.
- `GET /health`는 process liveness, `GET /ready`는 실제 traffic readiness입니다.
- parser admission은 process별 bounded non-waiting lease를 사용하며 포화 시 body 처리 전에 `429`로 거부합니다.
- 임시 workspace, parser failure 분류, schema validation, fixture provenance는 NewsDOM이 소유합니다.

## 요청 흐름

```text
client
  -> FastAPI request/auth boundary
  -> bounded parser admission
  -> request-scoped temporary PDF workspace
  -> approved parser adapter port
  -> NewsDOM normalization + schema validation
  -> canonical JSON response
```

현재 legacy adapter는 교체 대상입니다. downstream consumer는 parser-specific type이나 model identity가 아니라 NewsDOM contract에 의존해야 합니다.

## 시작하기

- [설치 가이드](installation.md) — NewsDOM 자체의 lockfile 기반 개발/검증 환경과 parser license boundary.
- [사용 방법 및 API](api-reference.md) — `/parse`, language/mode, 인증, 응답과 오류 계약.
- [개발 및 기여](development.md) — 로컬 검증과 기여 흐름.
- [GitHub 저장소](https://github.com/ContextualWisdomLab/newsdom-api) — README, architecture, security, releases, source history.
- [Commercial parser replacement #671](https://github.com/ContextualWisdomLab/newsdom-api/issues/671) — 현재 상업 라이선스 차단과 replacement acceptance.

## 릴리스와 공개 문서

`pyproject.toml`의 version은 source metadata이며 그 자체로 immutable release evidence가 아닙니다. 실제 릴리스는 [GitHub Releases](https://github.com/ContextualWisdomLab/newsdom-api/releases)와 해당 exact-head artifact/provenance evidence로 확인합니다.

이 `manual/` source가 병합되었다는 사실만으로 공개 사이트 배포가 완료된 것은 아닙니다. GitHub Pages workflow 성공과 live HTTPS content 재확인이 필요합니다.
