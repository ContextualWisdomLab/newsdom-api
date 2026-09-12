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

    assert "@seonghobae" in rules["*"]
    assert "@seonghobae" in rules[".github/"]
    assert "@seonghobae" in rules["docs/"]
    assert "@seonghobae" in rules["manual/"]


def test_codeql_backstop_scans_python_and_actions() -> None:
    workflow = yaml.safe_load(
        Path(".github/workflows/codeql.yml").read_text(encoding="utf-8")
    )
    analyze_job = workflow["jobs"]["analyze"]
    init_step = next(
        step
        for step in analyze_job["steps"]
        if step.get("uses", "").startswith("github/codeql-action/init@")
    )

    assert analyze_job["name"] == "codeql (python, actions)"
    assert init_step["with"]["languages"] == "python, actions"


def test_gitignore_declares_site_only_once() -> None:
    active_lines = [
        line.strip()
        for line in Path(".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert active_lines.count("site/") == 1
