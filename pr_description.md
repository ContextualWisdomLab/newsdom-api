🎯 **무엇을 변경했나요:**
`src/newsdom_api/dom_builder.py`의 `build_dom` 함수 메인 루프를 리팩토링했습니다. 페이지 인덱스가 없는 경우의 폴백 처리와 페이지 집계 로직을 별도의 헬퍼 함수들(`_extract_page_info_by_idx`, `_group_blocks_by_page_idx`, `_build_pages_without_page_idx`, `_build_pages_with_page_idx`)로 분리했습니다.

💡 **왜 변경했나요:**
기존의 `build_dom` 함수는 루프 내에 여러 조건에 따른 복잡한 폴백 및 처리 로직을 모두 포함하고 있어 가독성이 떨어졌습니다. 기능별로 작은 헬퍼 함수들로 분리함으로써 코드의 가독성과 유지보수성을 크게 향상시켰습니다.

✅ **검증:**
수정 후 `pytest tests/test_dom_builder.py` 및 전체 테스트(`pytest --cov=src/newsdom_api`)를 실행하여 기능이 동일하게 유지되고 커버리지(100%)가 만족되는 것을 확인했습니다.

✨ **결과:**
`build_dom` 함수의 본문이 크게 단순화되어 전반적인 흐름을 파악하기 훨씬 쉬워졌으며, 코드 상태가 개선되었습니다.
