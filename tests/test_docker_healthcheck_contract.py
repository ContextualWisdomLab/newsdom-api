"""Container liveness-probe contract tests."""

from pathlib import Path
import re


def _healthcheck_instruction(dockerfile: str) -> str:
    """Return the single HEALTHCHECK instruction including continuation lines."""

    matches = re.findall(
        r"^HEALTHCHECK\b(?P<body>[\s\S]*?)(?=^[A-Z][A-Z0-9_]*\b|\Z)",
        dockerfile,
        flags=re.MULTILINE,
    )
    assert len(matches) == 1
    return " ".join(matches[0].split())


def test_default_image_liveness_probe_is_bounded_and_loopback_only() -> None:
    """Keep liveness local, bounded, and independent of optional parser readiness."""

    instruction = _healthcheck_instruction(
        Path("Dockerfile").read_text(encoding="utf-8")
    )

    assert "--interval=30s" in instruction
    assert "--timeout=5s" in instruction
    assert "--start-period=10s" in instruction
    assert "--retries=5" in instruction
    assert "python -c" in instruction
    assert "http://127.0.0.1:8000/health" in instruction
    assert "/ready" not in instruction
    assert "0.0.0.0" not in instruction
