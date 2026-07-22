# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `tools/filter_dom.py`: JSON DOM 파일에서 특정 페이지(예: 1,3,5)만 남기거나, 이미지(`images`) 블록을 일괄 제거하여 경량화하는 필터링 도구 추가 (#345).
- `tools/extract_toc.py`: JSON DOM 파일 내의 아티클 제목(headline)을 기반으로 목차(Table of Contents)를 텍스트 또는 JSON 형태로 추출하는 도구 추가 (#345).
- `tools/shift_pages.py`: JSON DOM 파일 내 모든 페이지 번호(`page_number`)에 특정 오프셋(예: -2, +1)을 일괄 적용하는 도구 추가 (#345).

### Changed
- `/parse`를 언어 선택형 파서로 일반화: MinerU `-l japan`/`-m ocr` 하드코딩을 제거하고 optional form 필드 `language`(MinerU 3.4.4 공식 기본 `ch`, 공개 언어군/alias 검증)와 `mode`(`auto`/`ocr`/`txt`, 기본 `auto`)로 파라미터화. `mode=auto`는 born-digital PDF가 강제 OCR을 건너뛰도록 함. 기존 입력 `language=japan&mode=ocr`는 공식 규약대로 `ch`/`ocr`로 정규화됨.
- OpenAPI 제목/설명, README, `ArticleNode.headline` 문서를 일반 문서용 (section heading) 표현으로 재구성하여 특정 언어/신문 가정을 소비자에게 노출하지 않도록 함. 응답 스키마 필드는 하위 호환을 위해 변경하지 않음.

### Added
- [CLI] 단일 NewsDOM JSON 파일을 페이지 단위로 분리하는 `tools/split_dom.py` 도구를 추가했습니다.
- [CLI] NewsDOM JSON 파일의 모든 텍스트 내용을 마스킹하여 익명화하는 `tools/anonymize_dom.py` 도구를 추가했습니다.
- `/parse`에 대한 optional bearer 인증 게이트: 리프 서비스 자체 설정 `NEWSDOM_API_TOKEN`이 설정되면 `Authorization: Bearer <token>`을 요구(상수 시간 비교), 미설정 시 개방(개발용). `/health`는 항상 미인증 유지.
- 서브모듈/사이드카 배포용 `docker-compose.yml`: healthcheck가 `/health`를 대상으로 하며 MinerU 번들 이미지/`NEWSDOM_MINERU_BIN` 및 readiness 주의사항을 README에 문서화.
- [CLI] 파싱된 NewsDOM JSON에서 순수 텍스트 데이터를 추출하여 텍스트 파일 또는 stdout으로 출력하는 `tools/extract_text.py` 도구를 추가했습니다.

### Security
- 전역 500 에러 응답에도 표준 보안 헤더를 적용하여 예외 경로에서 header 누락을 방지
- MinerU subprocess argv 생성 시 `-`로 시작하는 option-like 인자를 거부하여 argument injection 위험을 낮춤
- API 에러 응답 생성 시 내부 예외 체인을 억제하여 의존성 오류나 내부 경로가 노출될 가능성을 줄임
- API 응답 미들웨어에 `Cache-Control: no-store, max-age=0` 헤더를 추가하여 민감한 파싱 데이터의 브라우저 및 중간 캐싱을 방지

### Performance
- `newsdom_api.dom_builder._html_safe_text` 함수에 early return과 타입 체크를 도입하여 불필요한 `str()` 캐스팅을 제거함으로써 처리 속도를 개선했습니다.

### Added
- [CLI] 여러 개의 분할된 NewsDOM JSON 파일을 하나의 문서로 병합하는 `tools/merge_dom.py` 도구를 추가했습니다.
- [CLI] 파싱된 NewsDOM JSON 데이터를 CSV 형식으로 추출하는 `tools/export_csv.py` 도구를 추가했습니다.
- [CLI] 파싱된 NewsDOM JSON을 HTML 포맷으로 변환하여 웹 브라우저에서 보기 쉽게 만들어주는 `tools/export_html.py` 도구를 추가했습니다.
- [CLI] 파싱된 NewsDOM JSON이 Pydantic 스키마(`ParseResponse`)와 일치하는지 엄격하게 검증하는 `tools/validate_dom.py` 도구 추가
- [CLI] 파싱된 NewsDOM JSON의 기사 제목(headline)과 본문(body_blocks)에서 텍스트를 검색하여 위치를 반환하는 `tools/search_dom.py` 도구 추가
- [CLI] 파싱된 NewsDOM JSON을 Markdown 포맷으로 변환하는 `tools/export_markdown.py` 도구를 추가했습니다.
- [CLI] `tools/batch_parse_pdf.py`에 하위 디렉터리의 PDF를 일괄 처리하고 상대 경로로 JSON을 저장하는 `--recursive` 옵션을 추가했습니다.
- OpenAPI 문서에 contact 및 MIT license metadata를 추가하여 API 소비자가 maintainer와 라이선스 정보를 더 쉽게 확인할 수 있도록 개선
- 여러 PDF를 일괄 파싱해 JSON 결과를 저장하는 `tools/batch_parse_pdf.py` 도구 추가
- 파싱된 NewsDOM JSON의 페이지, 기사, 본문 블록, 이미지 수를 집계하는 `tools/analyze_dom.py` 도구 추가
- [CLI] PDF 파일을 파싱하여 DOM 구조를 JSON으로 추출하는 `tools/parse_pdf.py` 도구 추가
- [CLI] 합성 신문 PDF와 정답 데이터를 대량으로 생성하는 `tools/generate_synthetic.py` 도구 추가
- `tools/benchmark_ocr.py`에 `--recursive` 인자를 추가하여 하위 디렉토리에 있는 PDF 파일도 재귀적으로 탐색할 수 있도록 기능 보강.
- `tools/benchmark_ocr.py`에 `--format` 인자를 추가하여 벤치마크 결과를 `json` 및 `csv` 포맷으로 내보낼 수 있는 기능 추가.
- `tools/derive_private_baseline.py`에 `--recursive` 인자를 추가하여 하위 디렉토리에 있는 PDF 파일 재귀 탐색 기능 추가.
- `tools/derive_private_baseline.py`에 `--strict` / `--no-strict` 인자를 추가하여 일부 PDF 파일 파싱 실패 시 진행을 계속할 수 있는 장애 허용성 옵션 추가.
- 관련된 코드의 단위 테스트 작성 및 코드 커버리지 100% 달성.
- `tools` 패키지에 대한 단위 테스트 커버리지를 100%로 향상
  - `tests/test_benchmark_ocr.py`에 빈 디렉토리, 알 수 없는 엔진 지정, mocking된 엔진 동작 등 새로운 테스트 케이스 추가
  - `tests/test_derive_private_baseline.py`에 `FileNotFoundError`, `HTTPException` 상황 및 `main()` 실행 경로 전체에 대한 테스트 추가
- `tools/benchmark_ocr.py` 및 `tools/derive_private_baseline.py`의 `if __name__ == "__main__":` 구문에 커버리지 측정 예외 마커(`pragma: no cover`) 추가

### Changed

- Improved OpenAPI metadata for the `/parse` endpoint by documenting 415, 502, and 503 error responses.

## [0.2.0] - 2026-04-24

### Added

- Added `benchmark_ocr.py` tool to measure OCR engine performance and structural accuracy on private datasets.
- Deployed a GHCR prebuilt CI container image (`ghcr.io/seongho-bae/newsdom-api/ci-env`) to stabilize test environments and resolve timeout/dependency installation issues.

### Changed

- Updated `dom_builder.py` to preserve multi-page MinerU structure instead of collapsing multi-page outputs into a single page.
- Adjusted the `/parse` endpoint to return specific HTTP error codes (`502` and `503`) mapped to `MineruIncompleteOutputError` and `MineruRuntimeUnavailableError` rather than raw `500` errors.

### Fixed

- Mitigated infinite hang issues when processing specific PDFs by enforcing a strict timeout (300 seconds) in the `mineru` subprocess runner.
- Resolved permission (`EACCES`) issues in GitHub Actions by running tests locally instead of inside a non-root container context for GitHub's restricted runner environment.


## [0.1.1] - 2026-04-11

### Added

- GHCR-ready multi-arch API image delivery, ClusterFuzzLite coverage, and exported `*.intoto.jsonl` provenance bundles for stable releases
- Verified `/docs` and `/redoc` manual screenshots plus canonical engineering policy docs that describe the live repository workflow

### Changed

- Protected-branch governance documentation now reflects the current single-maintainer exception while preserving required checks and history protections
- Public setup guidance, docs-toolchain policy, and markdownlint scope now match the merged `develop` / `main` delivery paths

### Fixed

- Patched `pypdf` lockfile coverage to `6.10.0` for GHSA-3crg-w4f6-42mx / CVE-2026-40260

## [0.1.0] - 2026-04-09

### Added

- MinerU-backed DOM parsing API for scanned Japanese newspaper PDFs
- Synthetic newspaper fixture generation and structural equivalence checks
- Protected-branch CI, security gates, release provenance workflow, and Git Flow documentation

[Unreleased]: https://github.com/Seongho-Bae/newsdom-api/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Seongho-Bae/newsdom-api/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/Seongho-Bae/newsdom-api/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Seongho-Bae/newsdom-api/releases/tag/v0.1.0
