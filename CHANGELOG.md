# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 파싱된 NewsDOM JSON 파일이 응답 스키마(`ParseResponse`)를 올바르게 준수하는지 검증하는 `tools/validate_dom.py` 도구를 추가했습니다.
- 파싱된 NewsDOM JSON 파일 내의 모든 텍스트 요소를 평문(Plain text)으로 쉽게 추출할 수 있도록 `tools/extract_text.py` 도구를 추가했습니다.

### Security
- 전역 500 에러 응답에도 표준 보안 헤더를 적용하여 예외 경로에서 header 누락을 방지
- MinerU subprocess argv 생성 시 `-`로 시작하는 option-like 인자를 거부하여 argument injection 위험을 낮춤
- API 에러 응답 생성 시 내부 예외 체인을 억제하여 의존성 오류나 내부 경로가 노출될 가능성을 줄임
- API 응답 미들웨어에 `Cache-Control: no-store, max-age=0` 헤더를 추가하여 민감한 파싱 데이터의 브라우저 및 중간 캐싱을 방지

### Performance
- `newsdom_api.dom_builder._html_safe_text` 함수에 early return과 타입 체크를 도입하여 불필요한 `str()` 캐스팅을 제거함으로써 처리 속도를 개선했습니다.

### Added
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
