import importlib.util
from pathlib import Path


def load_normalizer():
    module_path = Path("scripts/ci/opencode_review_normalize_output.py")
    spec = importlib.util.spec_from_file_location(
        "opencode_review_normalize_output",
        module_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mentions_actual_changed_file_requires_exact_path_boundary(
    monkeypatch,
    tmp_path: Path,
):
    normalizer = load_normalizer()
    changed_files = tmp_path / "changed-files.txt"
    changed_files.write_text(
        "README.md\n.github/workflows/opencode-review.yml\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENCODE_CHANGED_FILES_FILE", str(changed_files))

    assert not normalizer.mentions_actual_changed_file(
        "Changed-file evidence: docs/README.md",
        "",
    )
    assert not normalizer.mentions_actual_changed_file(
        "Changed-file evidence: README.md.bak",
        "",
    )
    assert normalizer.mentions_actual_changed_file(
        "Changed-file evidence: README.md",
        "",
    )
    assert normalizer.mentions_actual_changed_file(
        "Changed-file evidence: ./.github/workflows/opencode-review.yml",
        "",
    )
