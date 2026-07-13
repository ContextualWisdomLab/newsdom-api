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


def test_clusterfuzzlite_build_script_uses_locked_uv_fuzz_extra():
    text = _repo_path(".clusterfuzzlite", "build.sh").read_text(encoding="utf-8")
    assert "uv sync --frozen --extra fuzz" in text
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
