from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from newsdom_api.config import bootstrap_runtime_config  # noqa: E402


@pytest.fixture(autouse=True)
def allow_anonymous_test_instance(monkeypatch):
    """Make anonymous parsing explicit in unit tests without weakening deploys."""

    monkeypatch.setenv("NEWSDOM_ALLOW_ANONYMOUS", "true")
    bootstrap_runtime_config()
    yield
    bootstrap_runtime_config({})
