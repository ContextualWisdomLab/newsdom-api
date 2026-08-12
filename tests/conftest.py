from __future__ import annotations

import sys
from pathlib import Path

import pytest

from newsdom_api.config import bootstrap_runtime_config


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def reset_runtime_config():
    """Keep process-local credentials isolated between tests."""
    bootstrap_runtime_config({})
    yield
    bootstrap_runtime_config({})
