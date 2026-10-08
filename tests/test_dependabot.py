import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml


def _assert_dependabot_version_updates_stopped(root: Path = Path(__file__).resolve().parents[1]) -> None:
    """Repository-managed Dependabot version updates stay intentionally absent."""
    for relative in (Path(".github/dependabot.yml"), Path(".github/dependabot.yaml")):
        candidate = root / relative
        if candidate.exists() or candidate.is_symlink():
            raise AssertionError(
                f"Dependabot version updates must remain stopped; remove {relative}"
            )


def test_dependabot_version_update_policy_is_stopped_in_repository_source():
    _assert_dependabot_version_updates_stopped()


def _dependabot_package_ecosystems(data: dict) -> set[str]:
    """Read ecosystem entries structurally from parsed fixture data."""
    return {
        update["package-ecosystem"]
        for update in data.get("updates", [])
        if "package-ecosystem" in update
    }


def test_yaml_package_ecosystems_are_loaded_structurally_from_fixture():
    fixture = """
updates:
  - package-ecosystem: github-actions
    directory: /
  - package-ecosystem: pip
    directory: /
"""
    data = yaml.safe_load(fixture)
    assert isinstance(data.get("updates"), list)
    assert _dependabot_package_ecosystems(data) == {"github-actions", "pip"}


def test_dependabot_stop_policy_accepts_absence_and_rejects_reappearance():
    """Both recognized config extensions must reject even empty/comment files."""
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        root = Path(directory)
        _assert_dependabot_version_updates_stopped(root)
        (root / ".github").mkdir()
        _assert_dependabot_version_updates_stopped(root)
        for extension in ("yml", "yaml"):
            config = root / ".github" / f"dependabot.{extension}"
            for content in ("", "# stopped version updates\n", "version: 2\nupdates: []\n"):
                config.write_text(content, encoding="utf-8")
                try:
                    _assert_dependabot_version_updates_stopped(root)
                except AssertionError as error:
                    assert "Dependabot version updates must remain stopped" in str(error)
                else:
                    raise AssertionError(f"restored {config.name} was accepted")
                finally:
                    config.unlink()
            config.symlink_to(root / "missing-target")
            try:
                _assert_dependabot_version_updates_stopped(root)
            except AssertionError:
                pass
            else:
                raise AssertionError("dangling config symlink was accepted")
            finally:
                config.unlink()
        _assert_dependabot_version_updates_stopped(root)


@pytest.mark.parametrize("extension", [None, "yml", "yaml"], ids=["absence", "yml", "yaml"])
@pytest.mark.parametrize("caller", ["source", "outside"])
def test_stop_policy_actual_pytest_consumer_is_bound_to_source_root(tmp_path, extension, caller):
    """Run only the real absence consumer in a byte-identical private module copy."""
    source = tmp_path / "source"
    tests = source / "tests"
    tests.mkdir(parents=True)
    module = tests / "test_dependabot.py"
    module.write_bytes(Path(__file__).read_bytes())
    outside = tmp_path / "outside"
    outside.mkdir()
    if extension is not None:
        github = source / ".github"
        github.mkdir()
        (github / f"dependabot.{extension}").write_text("# restored config\n", encoding="utf-8")
    # Do not inherit plugin/selection or private Git-index state into the child.
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith(("PYTEST_", "PYTHON", "GIT_"))
    }
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-m", "pytest", "--noconftest",
         "-p", "no:cacheprovider", "-c", os.devnull, "-q",
         f"{module}::test_dependabot_version_update_policy_is_stopped_in_repository_source"],
        cwd=source if caller == "source" else outside,
        env=env, capture_output=True, text=True, timeout=30,
    )
    output = result.stdout + result.stderr
    if extension is None:
        assert result.returncode == 0, output
        assert "1 passed" in output, output
    else:
        assert result.returncode == 1, output
        assert "1 failed" in output, output
        assert (
            "AssertionError: Dependabot version updates must remain stopped; remove "
            f".github/dependabot.{extension}"
        ) in output, output
