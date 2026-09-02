# Product / Technical Gap Baseline

이 문서는 NewsDOM API의 상용화 Gap을 live code, protected branch, 열린 PR과 실행 테스트를 기준으로 관리한다. 아직 병합되지 않은 다른 branch의 변경을 현재 기능으로 간주하지 않는다.

## Canonical NewsDOM JSONL export

### 문제

JSONL exporter는 NewsDOM JSON을 받는다고 설명하면서 실제로는 dict를 직접 순회했다. malformed page/article를 조용히 건너뛰고 필수 identifier가 없으면 임의의 `Unknown` 값을 만들었으며, canonical `ArticleNode`의 bounding box, images, captions, footnotes를 출력에서 삭제했다. 이 방식은 학습·분석 데이터셋에서 원문 위치와 이미지·캡션 provenance가 사라졌는데도 성공한 export처럼 보이게 한다.

### 선택

- 입력 문서는 production API와 동일한 `ParseResponse` schema로 먼저 검증한다.
- canonical schema를 만족하지 않는 입력은 output file을 만들기 전에 명시적으로 실패한다. malformed node를 silent skip하거나 synthetic identifier로 대체하지 않는다.
- 각 JSONL line은 `document_id`, `page_number`와 `ArticleNode.model_dump(mode="json")` 전체를 결합한다. `bbox`, `images`, `captions`, `footnotes`, `body_blocks` 등 canonical article provenance를 유지한다.
- exporter는 새로운 별도 schema truth를 만들지 않는다. production response model이 Ubiquitous Language와 serialization contract의 owner다.

### RED → GREEN evidence

- RED `e1f6e0c85ab886e4d403acb8b452c5222cbcc061`: article/page provenance가 JSONL에 보존되고 malformed page가 silent drop 대신 export failure가 되어야 한다는 contract를 추가했다.
- GREEN `6894960e6b67d25a32dfce7d98cf66a0c6497a46`: `ParseResponse.model_validate()`를 export boundary에 적용하고 canonical `ArticleNode` 전체를 JSONL record에 보존한다.
- Test repair `1c0955327a97207532963865c41b98a4a3657bc4`: 기존 테스트의 intentionally malformed fixture를 canonical fixture로 바꾸고 optional provenance fields의 serialized defaults도 검증한다.

### 현재 acceptance

exact head의 JSONL contract tests와 전체 repository test/lint/type/security checks가 terminal GREEN이어야 한다. 단순 line count, synthetic fixture coverage percentage, predecessor head의 check 성공은 canonical fidelity 증거를 대신하지 않는다.

### 남은 Gap

현재 구현은 `read_text()`와 `json.loads()`로 전체 JSON document를 메모리에 올린다. 따라서 이 PR은 “대규모 데이터 streaming”을 완료했다고 주장하지 않는다. 실제 대용량 export acceptance에는 canonical schema fidelity를 잃지 않는 incremental parse/write 경로, bounded-memory profile, real/right-cleared NewsDOM corpus의 peak RSS와 throughput evidence가 필요하다.
