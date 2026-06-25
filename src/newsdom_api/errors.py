"""Typed application errors for MinerU execution and output handling."""

from __future__ import annotations


class MineruRuntimeUnavailableError(RuntimeError):
    """MinerU could not be executed successfully."""

    def __init__(
        self,
        *,
        returncode: int | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
    ) -> None:
        """Store internal diagnostics while exposing a sanitized public message."""

        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__("MinerU runtime unavailable")


class MineruIncompleteOutputError(RuntimeError):
    """MinerU finished without producing the required artifacts."""

    def __init__(self) -> None:
        """Expose a stable sanitized message for incomplete MinerU artifacts."""

        super().__init__("MinerU output was incomplete")
