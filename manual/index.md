# NewsDOM API

[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/ContextualWisdomLab/newsdom-api/badge)](https://securityscorecards.dev/viewer/?uri=github.com/ContextualWisdomLab/newsdom-api)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ContextualWisdomLab/newsdom-api)

**NewsDOM API**는 PDF를 페이지·섹션·제목·본문 블록·이미지·캡션·바운딩 박스를 포함한 표준화된 DOM형 JSON 문서 트리로 변환하는 다국어 PDF 파싱 사이드카입니다. FastAPI 서비스가 요청 경계를 소유하고, MinerU 파이프라인이 문서 분석을 수행하며, NewsDOM이 결과를 안정적인 응답 스키마로 정규화합니다.

일본어 신문 OCR은 여전히 지원되는 사용 사례이지만 제품의 전체 범위는 특정 언어나 강제 OCR 모드에 한정되지 않습니다. 호출자는 지원되는 `language` 값을 선택할 수 있고, `mode=auto`를 기본값으로 사용해 텍스트 레이어가 있는 PDF는 불필요한 강제 OCR을 피할 수 있습니다. 필요할 때 `ocr` 또는 `txt` 모드를 명시적으로 선택할 수 있습니다.

## 제품 경계

- `POST /parse`는 PDF 업로드를 받아 정규화된 NewsDOM JSON을 반환합니다.
- `language`은 MinerU가 지원하는 언어 계열과 호환 별칭을 선택하며 기본값은 다국어 `ch` 계열입니다.
- `mode`는 `auto`, `ocr`, `txt`를 지원하며 기본값은 `auto`입니다.
- `/parse`는 기본적으로 fail-closed Bearer 인증을 요구합니다.
- `GET /health`는 프로세스 liveness만 나타내고, `GET /ready`는 인증 설정과 MinerU 런타임이 실제 트래픽을 받을 수 있는지를 나타냅니다.
- 기본 서비스 이미지는 API를 제공하며, 실제 파싱을 위해서는 호환되는 MinerU 런타임을 이미지에 포함하거나 `NEWSDOM_MINERU_BIN`으로 제공해야 합니다.

## 아키텍처

일반적인 요청은 다음 경계를 통과합니다.

1. FastAPI가 인증과 요청 계약을 검증합니다.
2. 요청별 임시 작업 공간에 PDF를 안전하게 준비합니다.
3. MinerU 런타임이 선택된 언어와 파싱 모드로 문서를 분석합니다.
4. NewsDOM 변환 계층이 MinerU 출력을 페이지·섹션·본문·이미지·캡션 등 표준 응답 노드로 정규화합니다.
5. 요청 작업 공간을 정리한 뒤 스키마 검증된 응답을 반환합니다.

상세한 현재/목표 아키텍처와 운영·보안 결정은 저장소의 `ARCHITECTURE.md`, `docs/adr/`, `docs/` 문서에서 관리합니다. 공개 매뉴얼은 현재 보호 브랜치에 존재하는 동작과 사용 방법을 우선 설명하며, 아직 병합되지 않은 PR의 기능을 출시된 동작으로 표시하지 않습니다.

## 시작하기

- [설치 가이드](installation.md)에서 `uv`, NewsDOM API, MinerU 런타임을 준비합니다.
- [사용 방법 및 API](api-reference.md)에서 `/parse`, 언어/모드 선택, 인증 및 응답 계약을 확인합니다.
- [개발 및 기여](development.md)에서 로컬 검증과 기여 흐름을 확인합니다.
- [GitHub 저장소](https://github.com/ContextualWisdomLab/newsdom-api)의 README에는 Docker/Compose 실행, 테스트, 퍼징, 보안 및 저장소 구조가 정리되어 있습니다.

## 릴리스와 운영 증거

릴리스 이력과 변경 내용은 [GitHub Releases](https://github.com/ContextualWisdomLab/newsdom-api/releases) 및 저장소의 `CHANGELOG.md`에서 확인할 수 있습니다. 버전 태그 기반 릴리스 파이프라인은 배포 아티팩트와 체크섬·provenance 증거를 생성하며, 보안 보고 절차는 `SECURITY.md`에 기록되어 있습니다.

이 사이트의 소스가 병합되었다는 사실만으로 새 배포가 완료되었다고 간주하지 않습니다. GitHub Pages 배포 워크플로가 성공하고 게시된 사이트가 실제로 갱신된 뒤에만 공개 사이트 변경이 완료된 것으로 취급합니다.
