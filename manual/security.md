# 보안 및 취약점 제보

NewsDOM API에서 아직 공개되지 않은 취약점을 발견했다면 공개 이슈를 열지 말고 GitHub Security Advisory 초안으로 비공개 제보해 주세요.

- 비공개 제보: [GitHub Security Advisory draft](https://github.com/ContextualWisdomLab/newsdom-api/security/advisories/new)
- Maintainer: [seonghobae](https://github.com/seonghobae)

## 제보에 포함할 내용

- 영향을 받는 브랜치 또는 커밋
- 재현 단계와 기대 동작
- 영향 범위와 악용 가능성에 대한 설명
- 안전하게 재현할 수 있는 proof-of-concept 입력 또는 정제된 로그

## 안전한 증거 처리

가능하면 합성 fixture를 사용해 재현 자료를 구성하세요. 실제 서비스 secret, production credential, 비공개 참조 입력, 저작권이 있는 제3자 원문 문서는 제보에 포함하지 않습니다.

로그나 proof-of-concept 입력이 필요한 경우 민감한 식별자와 토큰을 제거하되, maintainer가 동일한 문제를 재현할 수 있을 만큼의 구조와 경로는 남겨 주세요.

## 지원 브랜치

- `develop`: 적극적으로 유지보수되는 통합 브랜치
- `main`: 안정 릴리스 브랜치

보안 수정은 Git Flow에 맞는 브랜치에서 진행하고 필요하면 `docs/workflow/git-flow.md` 절차에 따라 역병합합니다.

## 응답 기대치

- 접수 확인 목표: 7일 이내
- 수정 가능성이 있는 경우 triage 또는 상태 업데이트 목표: 30일 이내
- 수정 또는 완화책이 준비된 뒤 조율된 공개를 선호합니다.
