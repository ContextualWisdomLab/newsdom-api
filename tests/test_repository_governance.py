from pathlib import Path


def test_codeowners_exists_and_covers_repository() -> None:
    codeowners_path = Path(".github/CODEOWNERS")
    assert codeowners_path.exists()

    rules: dict[str, set[str]] = {}
    for raw_line in codeowners_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        pattern, *owners = line.split()
        rules[pattern] = set(owners)

    assert "@Seongho-Bae" in rules["*"]
    assert "@Seongho-Bae" in rules[".github/"]
    assert "@Seongho-Bae" in rules["docs/"]
    assert "@Seongho-Bae" in rules["manual/"]


def test_gitignore_declares_site_only_once() -> None:
    active_lines = [
        line.strip()
        for line in Path(".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert active_lines.count("site/") == 1
