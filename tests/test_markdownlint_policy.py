import json
from pathlib import Path


EXPECTED_LEGACY_MARKDOWNLINT_IGNORES = [
    "docs/plans/2026-04-08-git-flow-design.md",
    "docs/plans/2026-04-08-git-flow.md",
    "docs/plans/2026-04-08-newsdom-design.md",
    "docs/plans/2026-04-08-newsdom-implementation.md",
    "docs/plans/2026-04-08-quality-gate-design.md",
    "docs/plans/2026-04-08-quality-gate.md",
]


def test_contributing_documents_markdownlint_scope() -> None:
    text = Path("CONTRIBUTING.md").read_text(encoding="utf-8").lower()
    for expected in (
        "markdownlint",
        "legacy",
        "agents.md",
        "architecture.md",
        "contributing.md",
        "docs/**/*.md",
        "git-flow-design",
        "newsdom-implementation",
        "quality-gate",
    ):
        assert expected in text


def test_markdownlint_config_limits_ignores_to_legacy_plan_files() -> None:
    config = json.loads(Path(".markdownlint-cli2.jsonc").read_bytes())
    assert config == {"ignores": EXPECTED_LEGACY_MARKDOWNLINT_IGNORES}
    for path in EXPECTED_LEGACY_MARKDOWNLINT_IGNORES:
        assert Path(path).exists(), f"ignored markdown file missing: {path}"
