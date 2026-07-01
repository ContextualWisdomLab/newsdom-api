from pathlib import Path


def test_changelog_exists_and_uses_keep_a_changelog_format():
    text = Path("CHANGELOG.md").read_text(encoding="utf-8")
    assert text.startswith("# Changelog")
    assert "Keep a Changelog" in text
    assert "## [Unreleased]" in text
    assert "Semantic Versioning" in text


def test_changelog_prepares_the_initial_0_1_0_release_entry():
    text = Path("CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [0.1.0] - 2026-04-09" in text


def test_initial_release_entry_keeps_added_section_and_links():
    text = Path("CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [0.1.0] - 2026-04-09\n\n### Added" in text
    assert "- MinerU-backed DOM parsing API for scanned Japanese newspaper PDFs" in text
    assert (
        "- Synthetic newspaper fixture generation and structural equivalence checks"
        in text
    )
    assert (
        "- Protected-branch CI, security gates, release provenance workflow, and Git Flow documentation"
        in text
    )
    assert (
        "[Unreleased]: https://github.com/Seongho-Bae/newsdom-api/compare/v0.2.0...HEAD"
        in text
    )
    assert (
        "[0.1.0]: https://github.com/Seongho-Bae/newsdom-api/releases/tag/v0.1.0"
        in text
    )


def test_changelog_prepares_the_0_1_1_release_entry():
    text = Path("CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [0.1.1] - 2026-04-11" in text
    assert "### Added" in text
    assert "*.intoto.jsonl" in text
    assert (
        "[Unreleased]: https://github.com/Seongho-Bae/newsdom-api/compare/v0.2.0...HEAD"
        in text
    )
    assert (
        "[0.1.1]: https://github.com/Seongho-Bae/newsdom-api/compare/v0.1.0...v0.1.1"
        in text
    )
