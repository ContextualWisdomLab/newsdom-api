from __future__ import annotations

import os
import sys
from pathlib import Path

# Existing endpoint tests intentionally run under the explicit development-only
# bypass. Production defaults remain fail-closed and are covered through the
# application factory with isolated RuntimeSettings instances.
os.environ.setdefault("NEWSDOM_AUTH_MODE", "disabled")
os.environ.setdefault("NEWSDOM_RUNTIME_PROFILE", "development")


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
