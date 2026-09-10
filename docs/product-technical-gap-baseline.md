# Product–technical gap baseline

기준일: 2026-09-10

`newsdom-api`는 MinerU OCR 결과를 canonical NewsDOM JSON으로 변환하는 문서 구조 인식 sidecar입니다. `tools/filter_dom.py`는 이 canonical response를 다시 파싱하지 않고 임의 JSON으로 가공하는 도구가 아니라, `ParseResponse` 계약을 검증한 뒤 선택한 page/content projection을 만드는 CLI read-model 경계로 취급합니다.

## PR #837 — Filtered NewsDOM projection

### Bounded context와 계약

- **Subdomain / Bounded Context:** NewsDOM Consumption Utilities / Filtered Projection.
- **Aggregate input:** 검증 가능한 `ParseResponse` 한 문서.
- **Invariant:** filter 전후의 `document_id`, quality provenance, page/article 순서와 선택되지 않은 필드는 의미상 보존되어야 합니다.
- **Page selector:** NewsDOM `page_number`는 one-based 의미를 가지므로 CLI selector도 양의 page number와 순방향 range만 허용해야 합니다.
- **Output:** 같은 filesystem directory에서 임시 파일을 완성한 뒤 replace하여 소비자가 부분 JSON을 관찰하지 않게 해야 합니다. 실패 시 임시 산출물은 정리해야 합니다.

### 이번 fleet repair

초기 PR에는 `filter_dom.py`와 직접 테스트 외에도 auth/schema 테스트의 전역 formatting churn, `uv.lock` 재잠금, dependency-security CHANGELOG 문구, 그리고 실제 수리를 수행하지 않는 `patch_dependencies.py`가 함께 들어 있었습니다. feature와 독립적인 dependency/security delta는 별도 owner lane에서 다뤄야 하므로 protected `develop` bytes로 복원하거나 제거했습니다. 특히 `patch_dependencies.py`는 실행 가능한 remediation이 아니라 내부 작업 메모를 source tree에 남긴 one-shot helper이므로 product code로 유지하지 않습니다.

현재 filter implementation의 유효 delta는 `tools/filter_dom.py`, `tests/test_tools_filter_dom.py`, 그리고 이 기능을 설명하는 CHANGELOG에 한정해야 합니다. dependency CVE remediation은 fresh Security Scan/trivy evidence를 읽고 canonical `uv lock --upgrade-package ...` 경로로 별도 causal repair를 수행합니다.

### 남은 correctness gap

현재 `parse_page_ranges()`는 `0`, 음수 또는 `5-3`과 같은 역방향 범위를 명시적으로 거부하지 않습니다. canonical schema 문서는 `page_number`를 one-based로 정의하므로 selector syntax도 같은 Ubiquitous Language를 가져야 합니다. 또한 매우 큰 range를 즉시 `set`으로 materialize하는 방식은 CLI 입력 크기에 비해 불필요하게 큰 메모리를 사용할 수 있으므로, 현실적인 page-count 경계와 selector representation을 별도 test-first repair로 결정해야 합니다.

### Acceptance

1. `ParseResponse` validation failure는 입력 JSON을 부분적으로 쓰지 않고 non-zero exit로 끝납니다.
2. image/caption, ad, header/footer/page-number 제외와 page projection이 순서·provenance를 보존합니다.
3. page selector는 one-based semantics와 invalid/reversed range failure를 regression으로 고정합니다.
4. output write failure 시 기존 output을 부분 파일로 대체하지 않고 임시 파일을 정리합니다.
5. unrelated auth/schema formatting, dependency lock churn, scanner suppression 또는 one-shot source-fix helper가 feature PR에 섞이지 않습니다.
6. 동일 exact head에서 pytest/100% branch coverage, docs build, Security Scan, SAST, CodeQL이 terminal GREEN이고 current-head review가 완료돼야 Ready를 검토합니다.

## 후속 조치

- page-range parser의 one-based/reversed-range RED를 먼저 추가하고 최소 causal GREEN을 구현합니다.
- output temp-file 경계는 concurrent invocation과 symlink-prone directory를 포함해 검증합니다. 위험이 재현되면 same-directory securely-created temporary file + atomic replace로 수리합니다.
- 실제 dependency finding은 이 feature lane과 분리해 exact Trivy log → canonical lock regeneration → exact-head GREEN으로 처리합니다.
