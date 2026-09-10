# Product–technical gap baseline

기준일: 2026-09-10

`newsdom-api`는 MinerU OCR 결과를 canonical NewsDOM JSON으로 변환하는 문서 구조 인식 sidecar입니다. `tools/filter_dom.py`는 이 canonical response를 임의 JSON으로 취급하지 않고, `ParseResponse` 계약을 검증한 뒤 선택한 page/content projection을 만드는 CLI read-model 경계로 취급합니다.

## PR #837 — Filtered NewsDOM projection

### Bounded context와 계약

- **Subdomain / Bounded Context:** NewsDOM Consumption Utilities / Filtered Projection.
- **Aggregate input:** 검증 가능한 `ParseResponse` 한 문서.
- **Invariant:** filter 전후의 `document_id`, quality provenance, page/article 순서와 선택되지 않은 필드는 의미상 보존되어야 합니다.
- **Page selector:** NewsDOM `page_number`는 one-based 의미를 가지므로 CLI selector도 양의 page number와 순방향 range만 허용합니다.
- **Input boundary:** 파일이 존재하더라도 읽기 또는 UTF-8 decode에 실패하면 Python traceback으로 경계를 벗어나지 않고 CLI 오류와 exit 1로 수렴해야 하며 output을 만들지 않습니다.
- **Output:** 같은 filesystem directory에서 exclusive temporary file을 완성한 뒤 replace하여 소비자가 부분 JSON을 관찰하지 않게 합니다. destination 이름이 `.tmp`로 끝나거나 과거 고정 임시 이름과 충돌해도 기존 destination 또는 무관한 sibling을 선행 truncate하지 않아야 하며, replace 실패 시 생성한 temporary artifact만 정리합니다.

### 이번 fleet repair

초기 PR에는 `filter_dom.py`와 직접 테스트 외에도 auth/schema 테스트의 전역 formatting churn, `uv.lock` 재잠금, dependency-security CHANGELOG 문구, 그리고 실제 수리를 수행하지 않는 `patch_dependencies.py`가 함께 들어 있었습니다. feature와 독립적인 dependency/security delta는 별도 owner lane에서 다뤄야 하므로 protected `develop` bytes로 복원하거나 제거했습니다. 같은 unrelated delta가 descendants `ddd63e224275337ae4c52da6189a5efacf43771f`, `eb80b4cf67bcc8cffcd2b1ba88c9d5e1a11fd7be`에서 재유입됐지만 history를 rewrite하지 않고 각각 ordinary descendants `c28e3df7952f70e0f7011c957f5bc1b74d0a6285`, `896ea25ce73d3882853a8798ba4f4c375edc1f4b`에서 직전 code-current tree를 승계했습니다.

Page selector는 test-first `33bd8257ccccdb23596e55646231dd024dda897c`에서 `0`, 음수, zero-based range와 역방향 range를 RED로 고정한 뒤 `8babc1edee55048e5ecb852b8030fa9667a3cc8b`에서 one-based forward-only 계약으로 수리했습니다.

Output 경계도 별도 TDD로 수리했습니다. test-first `acc85d76c6aa89f5d1ca667fc263a0bfa876e7f5`는 과거 고정 `<output>.tmp` 경로에 symbolic link를 선점하면 무관한 victim file이 overwrite되는 동작을 재현합니다. source-fix `6b9d7ac5ff1f7905e8a374caa9239a6ce6999536`은 output과 같은 directory에 `NamedTemporaryFile(delete=False)`로 exclusive temporary file을 만들고 JSON write와 flush/fsync를 마친 뒤 replace합니다. review 후 `d14426e3f2b95642903a4d4e06094801466de4ed`에서 destination 자체가 `report.tmp`인 경우 publish 실패 시 기존 destination이 보존되는지, 과거 predictable sibling `report.tmp`가 이미 존재해도 무관한 artifact를 덮어쓰지 않는지 regression을 추가했고 Ruff `RUF043` 지적에 맞춰 regex assertion도 raw string으로 정리했습니다.

Review에서 확인한 input-read 경계도 TDD로 보강했습니다. test-first `dcb4f18c6d3fe14e650927c8009ec64d04b154b9`는 `Path.read_text()`의 `OSError`와 `UnicodeDecodeError`가 현재 CLI의 `SystemExit(1)` 계약으로 수렴해야 함을 요구하고 기존 구현에서 실패합니다. source-fix `b9ca4596a7c6e858281ae4ab310e2eb8d591aa7f`는 file read/decode와 JSON parse를 분리해 전자는 `Error reading input file` + exit 1, 후자는 기존 `Error reading JSON` + exit 1 의미를 유지합니다.

이 조치는 **fixed temporary-path collision/symlink overwrite, 부분 output 관찰, input read/decode 예외의 CLI 경계 이탈**을 좁혀 고친 것입니다. output directory 자체가 공격자에 의해 교체되는 모든 pathname race, directory metadata durability, 여러 writer가 같은 최종 output을 동시에 publish할 때의 business-level arbitration까지 해결했다고 주장하지 않습니다.

### 남은 correctness/performance gap

매우 큰 page range를 즉시 `set`으로 materialize하는 방식은 CLI 입력 크기에 비해 큰 메모리를 사용할 수 있습니다. 실제 NewsDOM page-count 분포와 buyer workload를 기준으로 selector representation의 상한 또는 interval 표현이 필요한지 별도 profiling 후 결정합니다. 임의 sample 축소나 근거 없는 최대 페이지 수를 계약으로 넣지 않습니다.

### Acceptance

1. 입력 file read/UTF-8 decode failure와 `ParseResponse` validation failure는 output을 부분적으로 쓰지 않고 non-zero exit로 끝납니다.
2. image/caption, ad, header/footer/page-number 제외와 page projection이 순서·provenance를 보존합니다.
3. page selector의 one-based semantics와 invalid/reversed range failure regression이 GREEN이어야 합니다.
4. predictable temp symlink·regular-file 선점에서 무관한 artifact가 변경되지 않아야 하고, destination 이름 자체가 `.tmp`여도 publish failure가 기존 destination을 선행 truncate하지 않아야 합니다.
5. replace/write failure 시 partial output을 publish하지 않고 생성한 temporary artifact를 정리해야 합니다.
6. unrelated auth/schema formatting, dependency lock churn, scanner suppression 또는 one-shot source-fix helper가 feature PR에 섞이지 않습니다.
7. 동일 exact head에서 pytest/100% coverage, docs build, Security Scan, SAST, CodeQL이 terminal GREEN이고 current-head review가 완료돼야 Ready를 검토합니다.

## 후속 조치

- exact-head CI에서 page selector, input-read failure, secure temp-write/collision regression을 검증합니다.
- 실제 buyer document page-count 분포를 확보하면 large-range allocation을 profile하고 필요할 때만 interval representation을 도입합니다.
- 실제 dependency finding은 이 feature lane과 분리해 exact Trivy log → canonical lock regeneration → exact-head GREEN으로 처리합니다.
