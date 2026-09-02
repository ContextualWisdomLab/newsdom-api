# Product / Technical Gap Baseline

이 문서는 NewsDOM API의 상용화 Gap을 live code, protected branch, 열린 PR, 실행 테스트와 공식 upstream 계약을 기준으로 관리한다. 서로 다른 PR의 아직 병합되지 않은 변경은 현재 branch의 기능으로 간주하지 않는다.

## Bearer authentication comparison boundary

### 문제

`hmac.compare_digest()`는 내용 기반 short-circuit을 피하지만 Python 공식 문서는 두 operand의 길이가 다르면 type·length 정보가 이론적으로 timing을 통해 드러날 수 있다고 명시한다. 기존 branch의 `len(credentials) != len(expected_token)` 뒤 `compare_digest(credentials, credentials)` 방식은 configured token과 presented credential의 비교 길이를 정규화하지 않는다. caller가 자신의 입력 길이만큼 self-comparison을 한 뒤 실패할 뿐이다.

### 제약과 선택

- Authorization header 전체는 `MAX_BEARER_HEADER_BYTES=4096`에서 먼저 제한한다.
- configured token은 immutable `RuntimeSettings` 생성 시 UTF-8 정규화·길이 검증을 끝낸 뒤 SHA-256 digest를 한 번 계산한다. secret length에 따른 hash 작업을 request path에서 반복하지 않는다.
- request credential은 이미 제한된 bytes를 SHA-256으로 digest한다.
- 실제 equality check는 두 개의 고정 32-byte digest에 대해 `hmac.compare_digest()`를 정확히 한 번 수행한다.
- 이 경계는 wall-clock 시간이 완전히 동일하다고 주장하지 않는다. HTTP stack, hashing, scheduling 등 전체 request latency에는 변동이 있으므로 acceptance는 operand contract와 인증 semantics를 실행 테스트로 검증한다.

### RED → GREEN evidence

- RED `faedf8d9103f8a510b35b49570124071cc875a36`: runtime settings가 fixed-size token digest를 미리 보유하고, 길이가 다른 presented token도 `compare_digest()`에 같은 digest 길이로 들어가며, 정확한 configured token은 인증 경계를 통과해야 한다는 regression을 추가했다.
- GREEN `1d4e61de2a879561cfeeb7871c1d01cc37114fad`: configured token digest를 immutable runtime configuration에서 사전 계산한다.
- GREEN `139c8440b894690a2f0d6dea2d183409bbf5361f`: request credential을 SHA-256 digest로 정규화하고 fixed-size digest끼리 비교한다.
- Documentation repair `e35b37e858b8fafd272d1428b5bceb97e16ae45c`: `credentials` self-comparison이 constant-time 보장을 만든다는 이전 설명을 제거하고 실제 boundary와 Python 문서의 제한을 기록한다.

### 현재 acceptance

현재 branch의 exact head에서 authentication tests, full repository tests, lint/type checks와 security checks가 terminal GREEN이어야 한다. 단순히 서로 다른 길이의 token이 401을 반환한다는 사실은 timing mitigation 증거가 아니다. predecessor head의 checks, source-neutral retrigger, self-approval, scanner suppression, required-gate 완화는 acceptance가 아니다.

### 남은 Gap

현재 bootstrap bearer token은 단일 shared secret이다. 다중 주체·회전·폐기·감사·권한 범위가 필요한 상용 identity 계약은 NewsDOM 내부 source copy나 별도 user store로 확장하지 않고 CWL canonical identity owner인 Keyverse의 released contract를 소비하는 ADR로 분리해야 한다.

## Traceability

Python Software Foundation. (2026). *hmac — Keyed-hashing for message authentication*. Python 3.14.7 documentation. Retrieved September 3, 2026, from https://docs.python.org/3/library/hmac.html
