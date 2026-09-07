# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- NewsDOM JSON을 schema validation 후 article/body-block 단위 JSONL로 변환하는 `tools/export_jsonl.py` 도구를 추가했습니다. 출력은 같은 디렉터리의 임시 파일에 완전히 기록된 뒤 교체되므로 encoding/write 실패 시 기존 published JSONL을 보존하고 partial 결과를 완료 산출물로 노출하지 않습니다.


> **Planned 0.3.0 deployment migration:** parser authentication changes from
> **default-open** to **default-required**. Production must configure
> `NEWSDOM_AUTH_MODE=required`, `NEWSDOM_RUNTIME_PROFILE=production`, and
> `NEWSDOM_API_TOKEN`; the explicit disabled mode is development-only. The
> Kubernetes manifest intentionally references the non-release `:unreleased`
> image placeholder until package, OpenAPI, image, provenance, and release
> acceptance are aligned for an actual 0.3.0 publication.

### Changed
- `/parse`를 언어 선택형 파서로 일반화: MinerU `-l japan`/`-m ocr` 하드코딩을 제거하고 optional form 필드 `language`(MinerU 3.4.4 공식 기본 `ch`, 공개 언어군/alias 검증)와 `mode`(`auto`/`ocr`/`txt`, 기본 `auto`)로 파라미터화. `mode=auto`는 born-digital PDF가 강제 OCR을 건너뛰도록 함. 기존 입력 `language=japan&mode=ocr`는 공식 규약대로 `ch`/`ocr`로 정규화됨.
- OpenAPI 제목/설명, README, `ArticleNode.headline` 문서를 일반 문서용 (section heading) 표현으로 재구성하여 특정 언어/신문 가정을 소비자에게 노출하지 않도록 함. 응답 스키마 필드는 하위 호환을 위해 변경하지 않음.

### Added
- [CLI] 단일 NewsDOM JSON 파일을 페이지 단위로 분리하는 `tools/split_dom.py` 도구를 추가했습니다.
- [CLI] NewsDOM JSON 파일의 모든 텍스트 내용을 마스킹하여 익명화하는 `tools/anonymize_dom.py` 도구를 추가했습니다.
- `/parse`에 기본 필수 bearer 인증 경계를 추가했습니다. `NEWSDOM_AUTH_MODE=required`, `NEWSDOM_RUNTIME_PROFILE=production`, `NEWSDOM_API_TOKEN`을 명시해야 하며, 인증 비활성화는 격리된 development 프로필에서만 허용됩니다. `/health`는 liveness 전용으로 미인증 상태를 유지하고 `/ready`가 인증 설정과 MinerU 가용성을 함께 검증합니다.
- 서브모듈/사이드카 배포용 `docker-compose.yml`: 필수 production 인증과 secret 주입을 요구하고 healthcheck가 `/ready`를 대상으로 하도록 구성했습니다. Kubernetes 예시는 Restricted Pod Security 설정, 비루트 실행, 권한 상승 금지, 모든 capability 제거, 읽기 전용 root filesystem, 제한된 임시 볼륨, liveness/readiness 분리를 적용합니다.
