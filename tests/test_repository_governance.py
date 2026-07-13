from pathlib import Path

import yaml


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


def test_codeql_scans_python_and_actions_with_required_check_name() -> None:
    workflow = yaml.safe_load(
        Path(".github/workflows/codeql.yml").read_text(encoding="utf-8")
    )
    analyze_job = workflow["jobs"]["analyze"]
    assert analyze_job["name"] == "codeql (python, actions)"

    init_step = next(
        step
        for step in analyze_job["steps"]
        if step.get("uses", "").startswith("github/codeql-action/init@")
    )
    languages = init_step["with"]["languages"]
    if isinstance(languages, str):
        normalized_languages = {
            language.strip().lower()
            for language in languages.split(",")
            if language.strip()
        }
    else:
        normalized_languages = {
            str(language).strip().lower()
            for language in languages
            if str(language).strip()
        }

    assert normalized_languages == {"python", "actions"}


def test_gitignore_declares_site_only_once() -> None:
    active_lines = [
        line.strip()
        for line in Path(".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert active_lines.count("site/") == 1
