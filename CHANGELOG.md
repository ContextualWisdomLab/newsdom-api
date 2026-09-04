# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

> **Planned 0.3.0 deployment migration:** parser authentication changes from
> **default-open** to **default-required**. Production must configure
> `NEWSDOM_AUTH_MODE=required`, `NEWSDOM_RUNTIME_PROFILE=production`, and
> `NEWSDOM_API_TOKEN`; the explicit disabled mode is development-only. The
> Kubernetes manifest intentionally references the non-release `:unreleased`
> image placeholder until package, OpenAPI, image, provenance, and release
> acceptance are aligned for an actual 0.3.0 publication.

### Changed
- `/parse` 업로드의 PDF header 이후 비동기 read 요청 단위를 8 KiB에서 1 MiB(`UPLOAD_READ_CHUNK_SIZE_BYTES`)로 변경했습니다. 호출 횟수 감소는 코드 계약으로 검증하되 latency, thread-pool 부하, 메모리 효과는 대표 workload의 재현 benchmark 전까지 성능 개선으로 단정하지 않습니다.
- `/parse`를 언어 선택형 파서로 일반화: MinerU `-l japan`/`-m ocr` 하드코딩을 제거하고 optional form 필드 `language`(MinerU 3.4.4 공식 기본 `ch`, 공개 언어군/alias 검증)와 `mode`(`auto`/`ocr`/`txt`, 기본 `auto`)로 파라미터화. `mode=auto`는 born-digital PDF가 강제 OCR을 건너뛰도록 함. 기존 입력 `language=japan&mode=ocr`는 공식 규약대로 `ch`/`ocr`로 정규화됨.
- OpenAPI 제목/설명, README, `ArticleNode.headline` 문서를 일반 문서용 (section heading) 표현으로 재구성하여 특정 언어/신문 가정을 소비자에게 노출하지 않도록 함. 응답 스키마 필드는 하위 호환을 위해 변경하지 않음.

### Added
- [CLI] 단일 NewsDOM JSON 파일을 페이지 단위로 분리하는 `tools/split_dom.py` 도구를 추가했습니다.
- [CLI] NewsDOM JSON 파일의 모든 텍스트 내용을 마스킹하여 익명화하는 `tools/anonymize_dom.py` 도구를 추가했습니다.
- `/parse`에 기본 필수 bearer 인증 경계를 추가했습니다. `NEWSDOM_AUTH_MODE=required`, `NEWSDOM_RUNTIME_PROFILE=production`, `NEWSDOM_API_TOKEN`을 명시해야 하며, 인증 비활성화는 격리된 development 프로필에서만 허용됩니다. `/health`는 liveness 전용으로 미인증 상태를 유지하고 `/ready`가 인증 설정과 MinerU 가용성을 함께 검증합니다.
- 서브모듈/사이드카 배포용 `docker-compose.yml`: 필수 production 인증과 secret 주입을 요구하고 healthcheck가 `/ready`를 대상으로 하도록 구성했습니다. Kubernetes 예시는 Restricted Pod Security 설정, 비루트 실행, 권한 상승 금지, 모든 capability 제거, 읽기 전용 root filesystem, 제한된 임시 볼륨, liveness/readiness 분리를 적용합니다.
- [CLI] 파싱된 NewsDOM JSON에서 순수 텍스트 데이터를 추출하여 텍스트 파일 또는 stdout으로 출력하는 `tools/extract_text.py` 도구를 추가했습니다.

### Security
- `/parse` authentication is now immutable per application instance and fails closed before multipart body parsing when required configuration is missing. Hostile missing, invalid, Unicode, oversized, and duplicated Authorization headers return one non-sensitive response.
- Added unauthenticated `/ready` traffic readiness that combines authentication configuration with MinerU executable availability while `/health` remains liveness-only.
- Hardened the Kubernetes deployment example with a restricted namespace policy, explicit non-root UID/GID, `RuntimeDefault` seccomp, disabled privilege escalation, dropped Linux capabilities, a read-only root filesystem, and bounded writable runtime volumes.
- 전역 500 에러 응답에도 표준 보안 헤더를 적용하여 예외 경로에서 header 누락을 방지
- MinerU subprocess argv 생성 시 `-`로 시작하는 option-like 인자를 거부하여 argument injection 위험을 낮춤
- API 에러 응답 생성 시 내부 예외 체인을 억제하여 의존성 오류나 내부 경로가 노출될 가능성을 줄임
- API 응답 미들웨어에 `Cache-Control: no-store, max-age=0` 헤더를 추가하여 민감한 파싱 데이터의 브라우저 및 중간 캐싱을 방지
- `uv.lock`의 의존성을 재잠금하여 실제 `pip-audit`/`trivy-fs` CVE를 제거: 런타임 경로의 `pillow` 12.2.0→12.3.0 (PYSEC-2026-3451/3452/3453/3454/3493/3494/3495/3496, 이미지 파서 취약점 8건), `pypdf>=6.15.0,<7.0` (lock 6.15.0; CVE-2026-59935/59936/59937/59938/71852/71870, PDF 파싱 경로), `click` 8.3.2→8.4.2 (PYSEC-2026-2132) — 모두 스캔 PDF/이미지 파싱 런타임에 직접 관련되며 선언 범위와 lock을 함께 고정함. 빌드 도구 `setuptools` 81.0.0→83.0.0 (CVE-2026-59890). 문서 툴체인의 `pymdown-extensions` 10.21.3→11.0.1 (CVE-2026-61632, MEDIUM)은 `mkdocs-material` 9.6.x의 `pymdown-extensions~=10.2`(`<11`) 상한 때문에 막혀 있었으므로, docs extra 핀을 `mkdocs-material>=9.7,<9.8`로 올려(9.7.x는 상한을 `>=10.2`로 완화) 해소함. `uv run mkdocs build --strict` 통과 확인. 조치 후 전체 잠금(런타임+extras) `pip-audit`: 취약점 0건.

### Performance
- `newsdom_api.dom_builder._html_safe_text` 함수에 early return과 타입 체크를 도입하여 불필요한 `str()` 캐스팅을 제거함으로써 처리 속도를 개선했습니다.

### Added
- [CLI] 여러 개의 분할된 NewsDOM JSON 파일을 하나의 문서로 병합하는 `tools/merge_dom.py` 도구를 추가했습니다.
- [CLI] 파싱된 NewsDOM JSON 데이터를 CSV 형식으로 추출하는 `tools/export_csv.py` 도구를 추가했습니다.
- [CLI] 파싱된 NewsDOM JSON을 HTML 포맷으로 변환하여 웹 브라우저에서 보기 쉽게 만들어주는 `tools/export_html.py` 도구를 추가했습니다.
- [CLI] NewsDOM JSON이 Pydantic 스키마(`ParseResponse`)와 일치하는지 엄격하게 검증하는 `tools/validate_dom.py` 도구 추가
- [CLI] 파싱된 NewsDOM JSON의 기사 제목(headline)과 본문(body_blocks)에서 텍스트를 검색하여 위치를 반환하는 `tools/search_dom.py` 도구 추가
- [CLI] 파싱된 NewsDOM JSON을 Markdown 포맷으로 변환하는 `tools/export_markdown.py` 도구를 추가했습니다.
- [CLI] `tools/batch_parse_pdf.py`에 하위 디렉터리의 PDF를 일괄 처리하고 상대 경로로 JSON을 저장하는 `--recursive` 옵션을 추가했습니다.
- OpenAPI 문서에 contact 및 MIT license metadata를 추가하여 API 소비자가 maintainer와 라이선스 정보를 더 쉽게 확인할 수 있도록 개선
- 여러 PDF를 일괄 파싱해 JSON 결과를 저장하는 `tools/batch_parse_pdf.py` 도구 추가
- 파싱된 NewsDOM JSON의 페이지, 기사, 본문 블록, 이미지 수를 집계하는 `tools/analyze_dom.py` 도구 추가
- [CLI] PDF 파일을 파싱하여 DOM 구조를 JSON으로 추출하는 `tools/parse_pdf.py` 도구 추가
- [CLI] 합성 신문 PDF와 정답 데이터를 대량으로 생성하는 `tools/generate_synthetic.py` 도구 추가
- `tools/benchmark_ocr.py`에 `--recursive` 인자를 추가하여 하위 디렉토리의 PDF 파일도 재귀적으로 탐색할 수 있도록 기능 보강.
- `tools/benchmark_ocr.py`에 `--format` 인자를 추가하여 벤치마크 결과를 `json` 및 `csv` 포맷으로 내보낼 수 있는 기능 추가.
- `tools/derive_private_baseline.py`에 `--recursive` 인자를 추가하여 하위 디렉토리의 PDF 파일 재귀 탐색 기능 추가.
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
