# Product / Technical Gap Baseline

이 문서는 NewsDOM API의 상용화 Gap을 live code, protected branch, 열린 PR과 실행 테스트를 기준으로 관리한다. 아직 병합되지 않은 다른 branch의 변경을 현재 기능으로 간주하지 않는다.

## Canonical NewsDOM JSONL export

### 문제

JSONL exporter는 NewsDOM JSON을 받는다고 설명하면서 실제로는 dict를 직접 순회했다. malformed page/article를 조용히 건너뛰고 필수 identifier가 없으면 임의의 `Unknown` 값을 만들었으며, canonical `ArticleNode`의 bounding box, images, captions, footnotes를 출력에서 삭제했다. 이 방식은 학습·분석 데이터셋에서 원문 위치와 이미지·캡션 provenance가 사라졌는데도 성공한 export처럼 보이게 한다.

또한 출력 경로가 입력 JSON 자체이거나 같은 파일을 가리키는 hard-link alias여도 export를 허용했다. 입력 전체를 메모리에 읽은 뒤 output을 `w` 모드로 열기 때문에 명령은 성공하면서 원본 canonical JSON을 JSONL 한 줄들로 덮어쓸 수 있었다. 이 동작은 export boundary의 비파괴 invariant와 맞지 않는다.

canonical validation을 통과한 뒤에도 기존 output을 곧바로 `w` 모드로 열면 두 번째 이후 record의 직렬화 또는 쓰기 실패가 이미 검증된 기존 export를 부분 JSONL로 바꿀 수 있다. export의 성공/실패가 artifact publish 상태와 원자적으로 일치해야 하므로 부분 replacement를 외부에 노출하지 않는 것이 같은 비파괴 invariant에 포함된다.

### 선택

- 입력 문서는 production API와 동일한 `ParseResponse` schema로 먼저 검증한다.
- canonical schema를 만족하지 않는 입력은 output file을 만들기 전에 명시적으로 실패한다. malformed node를 silent skip하거나 synthetic identifier로 대체하지 않는다.
- 각 JSONL line은 `document_id`, `page_number`와 `ArticleNode.model_dump(mode="json")` 전체를 결합한다. `bbox`, `images`, `captions`, `footnotes`, `body_blocks` 등 canonical article provenance를 유지한다.
- exporter는 새로운 별도 schema truth를 만들지 않는다. production response model이 Ubiquitous Language와 serialization contract의 owner다.
- output은 input과 다른 filesystem object여야 한다. resolved path가 같거나 기존 output이 input과 같은 inode인 경우에는 쓰기 전에 실패해 원본을 보존한다.
- 완성된 JSONL은 destination과 같은 directory의 임시 파일에 직렬화하고 flush/fsync가 끝난 뒤 `os.replace()`로 publish한다. 직렬화·write·fsync·replace 중 실패하면 임시 파일을 제거하고 기존 destination은 보존한다.

### RED → GREEN evidence

- RED `e1f6e0c85ab886e4d403acb8b452c5222cbcc061`: article/page provenance가 JSONL에 보존되고 malformed page가 silent drop 대신 export failure가 되어야 한다는 contract를 추가했다.
- GREEN `6894960e6b67d25a32dfce7d98cf66a0c6497a46`: `ParseResponse.model_validate()`를 export boundary에 적용하고 canonical `ArticleNode` 전체를 JSONL record에 보존한다.
- Test repair `1c0955327a97207532963865c41b98a4a3657bc4`: 기존 테스트의 intentionally malformed fixture를 canonical fixture로 바꾸고 optional provenance fields의 serialized defaults도 검증한다.
- RED `9fe476719b73befd6342e126c62571d4bf5bcd60` 및 `f341bb1f45625662506a1e718eebf94a11d356a6`: output이 input 자체이거나 hard-link alias인 경우 원본을 훼손하지 않고 거부해야 한다는 회귀 계약을 먼저 추가했다. 기존 구현은 이 조건을 검사하지 않아 input을 `w` 모드로 다시 열었다.
- GREEN `934da87ae774a46a80ff681555015370f63388d3`: resolved-path equality와 existing-target inode identity를 검사해 destructive alias를 쓰기 전에 차단했다. 일반적인 새 output 경로는 기존 export 흐름을 유지한다.
- RED `4ee1fe616bfd9986d12c12c980cba23546b8a36b`: 두 번째 record 직렬화가 실패했을 때 기존 destination 내용이 byte-for-byte 유지되고 임시 artifact가 남지 않아야 한다는 회귀 계약을 추가했다. 이전 구현은 destination을 먼저 truncate하므로 이 계약을 만족하지 못한다.
- GREEN `50fdd8170a3bcf4c24e6e9a3d0f8115013327615`: same-directory temporary artifact에 전체 record를 직렬화하고 flush/fsync 이후 `os.replace()`로 publish하며, 실패 경로는 임시 파일을 제거한다.

### 현재 acceptance

현재 branch의 JSONL contract tests와 전체 repository test/lint/type/security checks가 terminal GREEN이어야 한다. 단순 line count, synthetic fixture coverage percentage, predecessor head의 check 성공은 canonical fidelity나 publish atomicity 증거를 대신하지 않는다. 새 GREEN 이후 exact-head Actions evidence를 새로 확인하기 전에는 merge-ready로 간주하지 않는다.

### 남은 Gap

현재 구현은 `read_text()`와 `json.loads()`로 전체 JSON document를 메모리에 올린다. 따라서 이 PR은 “대규모 데이터 streaming”을 완료했다고 주장하지 않는다. 실제 대용량 export acceptance에는 canonical schema fidelity와 atomic publish invariant를 잃지 않는 incremental parse/write 경로, bounded-memory profile, real/right-cleared NewsDOM corpus의 peak RSS와 throughput evidence가 필요하다.
