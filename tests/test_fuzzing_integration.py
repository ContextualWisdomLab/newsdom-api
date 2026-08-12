import importlib.util
import os
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _repo_path(*parts: str) -> Path:
    return REPO_ROOT.joinpath(*parts)


def _load_dom_builder_fuzzer_module():
    spec = importlib.util.spec_from_file_location(
        "test_dom_builder_fuzzer",
        _repo_path("fuzzers", "dom_builder_fuzzer.py"),
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# (fuzzer script, corpus seed) pairs whose smoke mode must stay runnable in CI.
# build.sh auto-discovers every ``*_fuzzer.py`` under fuzzers/, so each entry
# here is also a live ClusterFuzzLite target.
FUZZ_SMOKE_TARGETS = [
    ("dom_builder_fuzzer", "dom_builder_fuzzer", "mineru_sample.json"),
    ("schema_response_fuzzer", "schema_response_fuzzer", "valid_parse_response.json"),
    (
        "equivalence_metrics_fuzzer",
        "equivalence_metrics_fuzzer",
        "structural_metrics.json",
    ),
]


def test_clusterfuzzlite_integration_files_exist(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)

    assert _repo_path(".clusterfuzzlite", "project.yaml").exists()
    assert _repo_path(".clusterfuzzlite", "Dockerfile").exists()
    assert _repo_path(".clusterfuzzlite", "build.sh").exists()
    assert _repo_path(".github", "workflows", "clusterfuzzlite.yml").exists()
    assert _repo_path("fuzzers", "dom_builder_fuzzer.py").exists()
    assert _repo_path(
        "fuzzers", "corpus", "dom_builder_fuzzer", "mineru_sample.json"
    ).exists()


@pytest.mark.parametrize("fuzzer,corpus_dir,seed", FUZZ_SMOKE_TARGETS)
def test_fuzz_target_and_seed_corpus_exist(fuzzer: str, corpus_dir: str, seed: str):
    assert _repo_path("fuzzers", f"{fuzzer}.py").exists()
    assert _repo_path("fuzzers", "corpus", corpus_dir, seed).exists()


def test_clusterfuzzlite_workflow_runs_pinned_python_code_change_fuzzing():
    text = _repo_path(".github", "workflows", "clusterfuzzlite.yml").read_text(
        encoding="utf-8"
    )
    assert (
        "google/clusterfuzzlite/actions/build_fuzzers@52ecc61cb587ee99c26825a112a21abf19c7448c"
        in text
    )
    assert (
        "google/clusterfuzzlite/actions/run_fuzzers@52ecc61cb587ee99c26825a112a21abf19c7448c"
        in text
    )
    assert "language: python" in text
    assert "mode: code-change" in text
    assert "fuzz-seconds: 300" in text
    assert "github-token: ${{ github.token }}" in text


def test_clusterfuzzlite_dockerfile_places_build_script_at_src_root():
    text = _repo_path(".clusterfuzzlite", "Dockerfile").read_text(encoding="utf-8")
    assert "gcr.io/oss-fuzz-base/base-builder-python@sha256:" in text
    assert "ghcr.io/astral-sh/uv@sha256:" in text
    assert "COPY .clusterfuzzlite/build.sh /src/build.sh" in text


def test_clusterfuzzlite_root_builder_exception_is_documented():
    text = _repo_path(".clusterfuzzlite", "Dockerfile").read_text(encoding="utf-8")

    assert "USER 10001:10001" not in text
    ignore_text = _repo_path(".trivyignore").read_text(encoding="utf-8")
    assert "ClusterFuzzLite mounts /github/workspace/build-out" in ignore_text
    assert "2026-10-31" in ignore_text
    assert "DS-0002" in ignore_text


def _parse_trivyignore_entries(path: Path | None = None) -> list[tuple[str, str]]:
    """Return (entry id, preceding comment block) pairs from .trivyignore.

    A blank line ends a comment block, so only the comment lines directly
    above an entry count as that entry's documentation.
    """
    entries: list[tuple[str, str]] = []
    comment_lines: list[str] = []
    ignore_path = path or _repo_path(".trivyignore")
    for line in ignore_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            comment_lines = []
            continue
        if stripped.startswith("#"):
            comment_lines.append(stripped.lstrip("#").strip())
            continue
        entries.append((stripped.split()[0], " ".join(comment_lines)))
        comment_lines = []
    return entries


def test_trivyignore_parser_does_not_inherit_comments_between_entries(
    tmp_path: Path,
):
    ignore_path = tmp_path / ".trivyignore"
    ignore_path.write_text(
        "# DS-0001 documented suppression\nDS-0001\nDS-0002\n",
        encoding="utf-8",
    )

    assert _parse_trivyignore_entries(ignore_path) == [
        ("DS-0001", "DS-0001 documented suppression"),
        ("DS-0002", ""),
    ]


def test_trivyignore_entries_each_carry_reason_and_revisit_condition():
    # The central trivy-fs gate (security-scan.yml in ContextualWisdomLab/
    # .github) honours this file via trivy's default --ignorefile, so every
    # suppression silently weakens a required merge gate. Each entry must be
    # documented inline: the id itself, the affected artifact / why it is
    # unfixable here, and a revisit condition.
    entries = _parse_trivyignore_entries()

    assert entries, ".trivyignore lost its documented entries unexpectedly"
    required_labels = (
        "affected artifact:",
        "why unfixable here:",
        "revisit condition:",
    )
    for entry, documentation in entries:
        assert documentation, (
            f".trivyignore entry {entry} has no comment block above it; "
            "document the finding, why it is unfixable here, and a revisit "
            "condition before suppressing it"
        )
        assert entry in documentation, (
            f".trivyignore entry {entry} must be named in the comment block "
            "directly above it"
        )
        normalized_documentation = documentation.lower()
        for label in required_labels:
            assert label in normalized_documentation, (
                f".trivyignore entry {entry} must document the labeled field "
                f"{label!r} directly above the entry"
            )


def test_trivyignore_does_not_suppress_go_ecosystem_cves():
    # Regression guard for PR #315: automation once added CVE-2021-4238
    # (github.com/Masterminds/goutils) and CVE-2022-26945
    # (github.com/hashicorp/go-getter) to .trivyignore while the actual
    # trivy-fs blocker was DS-0002 on a stale PR base. Those are Go-module
    # vulnerabilities and this repository ships no Go code, so `trivy fs .`
    # can never legitimately report them here. Suppressions that do not map
    # to a reproduced finding must stay out.
    entry_ids = {entry for entry, _ in _parse_trivyignore_entries()}

    assert "CVE-2021-4238" not in entry_ids
    assert "CVE-2022-26945" not in entry_ids

    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    go_artifacts = [
        path
        for path in tracked
        if Path(path).name in {"go.mod", "go.sum"} or path.endswith(".go")
    ]
    assert not go_artifacts, (
        "Go artifacts appeared in the repository; re-evaluate whether "
        "Go-ecosystem CVE suppressions in .trivyignore are now legitimate: "
        f"{go_artifacts}"
    )


def test_clusterfuzzlite_build_script_uses_locked_uv_fuzz_extra():
    text = _repo_path(".clusterfuzzlite", "build.sh").read_text(encoding="utf-8")
    assert "uv sync --frozen --extra fuzz" in text
    assert "--paths src" in text
    assert "--collect-submodules newsdom_api" in text
    assert "pip3 install . pyinstaller atheris" not in text


def test_clusterfuzzlite_build_script_marks_wrapper_as_discoverable_fuzz_target():
    text = _repo_path(".clusterfuzzlite", "build.sh").read_text(encoding="utf-8")
    assert 'chmod -x "$OUT/$fuzzer_package"' in text
    assert "LLVMFuzzerTestOneInput for fuzzer detection." in text
    assert r'chmod +x "\$this_dir/$fuzzer_package"' in text


def test_clusterfuzzlite_build_script_iterates_fuzzers_with_null_delimited_find():
    text = _repo_path(".clusterfuzzlite", "build.sh").read_text(encoding="utf-8")
    assert "find fuzzers -type f -name '*_fuzzer.py' -print0" in text
    assert "while IFS= read -r -d '' fuzzer; do" in text
    assert "for fuzzer in $(find fuzzers -name '*_fuzzer.py')" not in text


def test_clusterfuzzlite_build_script_fails_when_no_fuzzers_are_found():
    text = _repo_path(".clusterfuzzlite", "build.sh").read_text(encoding="utf-8")
    assert "No *_fuzzer.py files found under fuzzers/" in text
    assert "exit 1" in text


def test_dom_builder_fuzzer_loader_uses_path_relative_to_test_file(
    monkeypatch, tmp_path: Path
):
    monkeypatch.chdir(tmp_path)

    module = _load_dom_builder_fuzzer_module()

    assert Path(module.__file__).name == "dom_builder_fuzzer.py"


def test_dom_builder_fuzzer_forwards_libfuzzer_args(monkeypatch):
    module = _load_dom_builder_fuzzer_module()
    observed = {}

    fake_atheris = SimpleNamespace(
        Setup=lambda argv, callback: observed.update(
            argv=list(argv), callback=callback
        ),
        Fuzz=lambda: observed.update(fuzz_called=True),
    )
    monkeypatch.setitem(sys.modules, "atheris", fake_atheris)
    monkeypatch.setattr(sys, "argv", ["dom_builder_fuzzer", "--", "-runs=4"])

    assert module.main(["--", "-runs=4", "-seed=1337"]) == 0
    assert observed["argv"] == ["dom_builder_fuzzer", "-runs=4", "-seed=1337"]
    assert observed["fuzz_called"] is True


def test_dom_builder_fuzzer_only_swallows_json_decode_errors(monkeypatch):
    module = _load_dom_builder_fuzzer_module()

    def raise_runtime_error(_: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(module.json, "loads", raise_runtime_error)

    with pytest.raises(RuntimeError, match="boom"):
        module.exercise_dom_builder(b"[]")


def test_dom_builder_fuzzer_rejects_fuzz_args_in_smoke_mode():
    module = _load_dom_builder_fuzzer_module()

    with pytest.raises(SystemExit) as excinfo:
        module.main(["--smoke", "tests/fixtures/mineru_sample.json", "--", "-runs=4"])

    assert excinfo.value.code == 2


def test_dom_builder_fuzzer_smoke_mode_runs_without_cluster(
    monkeypatch, tmp_path: Path
):
    monkeypatch.chdir(tmp_path)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(_repo_path("src"))

    try:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(_repo_path("src"))
        completed = subprocess.run(
            [
                sys.executable,
                str(_repo_path("fuzzers", "dom_builder_fuzzer.py")),
                "--smoke",
                str(_repo_path("tests", "fixtures", "mineru_sample.json")),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError("smoke-mode fuzzer subprocess timed out") from exc

    assert completed.returncode == 0, completed.stderr
    assert "Traceback" not in completed.stderr


@pytest.mark.parametrize("fuzzer,corpus_dir,seed", FUZZ_SMOKE_TARGETS)
def test_fuzzer_smoke_mode_runs_without_cluster(
    monkeypatch, tmp_path: Path, fuzzer: str, corpus_dir: str, seed: str
):
    monkeypatch.chdir(tmp_path)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(_repo_path("src"))

    try:
        completed = subprocess.run(
            [
                sys.executable,
                str(_repo_path("fuzzers", f"{fuzzer}.py")),
                "--smoke",
                str(_repo_path("fuzzers", "corpus", corpus_dir, seed)),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(
            f"smoke-mode fuzzer {fuzzer} subprocess timed out"
        ) from exc

    assert completed.returncode == 0, completed.stderr
    assert "Traceback" not in completed.stderr
