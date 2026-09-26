## $(date +%Y-%m-%d) - Enhance Developer UX with OpenAPI Schema Examples

**Learning:** In a backend-only FastAPI project without frontend files, "UX" improvements naturally translate to Developer Experience (DX). Enhancing Pydantic schemas with `json_schema_extra={"example": ...}` rather than just using the `description` field or deprecated plural `examples` provides concrete, immediate value in the generated Swagger UI. Additionally, explicitly defining the ellipsis `...` for required fields is redundant and noisy in modern Pydantic V2 when no default is provided.
**Action:** When working on API schemas, proactively provide representative `json_schema_extra` examples to improve the consumer documentation experience, and omit the `...` default marker to keep schema declarations clean and idiomatic.

## 2026-08-04 - Backend API Developer Experience

**Learning:** 백엔드 전용 프로젝트(프론트엔드가 없는 경우)에서는 'UX(사용자 경험)'가 주로 'DX(개발자 경험)'로 해석됩니다. OpenAPI/Swagger 스키마에 `json_schema_extra={"example": ...}`와 같은 구체적인 예시를 추가하면 API를 사용하는 개발자들의 인터페이스 이해도를 높일 수 있습니다.
**Action:** 향후 백엔드 API 중심의 프로젝트에서는 Pydantic 스키마 정의에 풍부한 문서화와 예제 데이터가 포함되어 있는지 확인하여 개발자 경험을 개선할 것입니다.

## 2026-08-04 - False Positive PR Review handling
**Learning:** 자동화된 코드 리뷰 도구(예: opencode-agent)가 허위 양성(False Positive)으로 코드 변경을 거부하거나 수정 요구를 할 경우(예: 스키마 예제에서 존재하지 않는 필드를 지적하는 경우), 실제로 소스 코드 및 모델 정의를 수동으로 확인한 후, 리뷰어의 지적이 맞다면 수용하여 수정해야 합니다. 이번의 경우, `ImageNode`에 `path` 속성이 존재하지 않는다고 리뷰어가 지적했으나 실제로는 존재했습니다. 하지만, 이전에 수정한 `json_schema_extra` 에는 `path`를 포함했기 때문에 `ImageNode` 의 문서에 맞게 작성된 것이 맞습니다. 하지만, CI 실패는 `opencode-agent` 의 승인을 받지 못했기 때문이었습니다.
**Action:** PR 리뷰어 봇이 요구하는 변경 사항을 반영하여 재제출하거나, 해당 봇이 오작동하여 승인하지 않은 경우 코드를 수정하여 다시 검토를 요청합니다.

## 2026-08-04 - False Positive PR Review handling
**Learning:** 자동화된 코드 리뷰 도구(예: opencode-agent)가 허위 양성(False Positive)으로 코드 변경을 거부하거나 수정 요구를 할 경우(예: 스키마 예제에서 존재하지 않는 필드를 지적하는 경우), 실제로 소스 코드 및 모델 정의를 수동으로 확인한 후, 리뷰어의 지적이 맞다면 수용하여 수정해야 합니다. 이번의 경우, `ImageNode`에 `path` 속성이 존재하지 않는다고 리뷰어가 지적했으나 실제로는 존재했습니다. 하지만, 이전에 수정한 `json_schema_extra` 에는 `path`를 포함했기 때문에 `ImageNode` 의 문서에 맞게 작성된 것이 맞습니다. 하지만, CI 실패는 `opencode-agent` 의 승인을 받지 못했기 때문이었습니다.
**Action:** PR 리뷰어 봇이 요구하는 변경 사항을 반영하여 재제출하거나, 해당 봇이 오작동하여 승인하지 않은 경우 코드를 수정하여 다시 검토를 요청합니다.
