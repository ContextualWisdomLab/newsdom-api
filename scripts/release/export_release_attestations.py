"""Export GitHub attestation bundles as Scorecard-recognized release assets."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
from pathlib import Path


ATTESTATION_DOWNLOAD_TIMEOUT_SECONDS = 120


def _bundle_candidates(working_dir: Path, digest: str) -> tuple[Path, Path]:
    """Return possible attestation bundle filenames for a given digest."""

    return (
        working_dir / f"sha256:{digest}.jsonl",
        working_dir / f"sha256-{digest}.jsonl",
    )


def _sha256_file(path: Path) -> str:
    """Return a SHA-256 digest for a file without loading it fully into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_attestations(
    dist_dir: Path, repo: str, *, working_dir: Path | None = None
) -> list[Path]:
    """Download attestation bundles for release artifacts and rename them for Scorecard."""

    working_dir = (working_dir or Path.cwd()).resolve()
    gh_bin = shutil.which("gh")
    if gh_bin is None:
        raise FileNotFoundError("gh CLI executable not found in PATH")
    exported: list[Path] = []

    for artifact in sorted(dist_dir.iterdir()):
        if not artifact.is_file():
            continue
        if artifact.name in {"SHA256SUMS.txt", "release-manifest.json"}:
            continue
        if artifact.name.endswith(".intoto.jsonl"):
            continue

        artifact_path = artifact.resolve()
        try:
            subprocess.run(
                [gh_bin, "attestation", "download", str(artifact_path), "-R", repo],
                check=True,
                cwd=working_dir,
                timeout=ATTESTATION_DOWNLOAD_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                "Timed out downloading attestation bundle for "
                f"{artifact.name} after {ATTESTATION_DOWNLOAD_TIMEOUT_SECONDS} seconds"
            ) from exc

        digest = _sha256_file(artifact)
        bundle_path = next(
            (
                candidate
                for candidate in _bundle_candidates(working_dir, digest)
                if candidate.exists()
            ),
            None,
        )
        if bundle_path is None:
            raise FileNotFoundError(
                f"No attestation bundle downloaded for {artifact.name}"
            )

        output_path = dist_dir / f"{artifact.name}.intoto.jsonl"
        if output_path.exists():
            output_path.unlink()
        shutil.move(str(bundle_path), output_path)
        exported.append(output_path)

    return exported


def main() -> None:
    """Download and rename attestation bundles for the release dist directory."""

    parser = argparse.ArgumentParser(
        description="Export GitHub attestation bundles into dist/*.intoto.jsonl files"
    )
    parser.add_argument("dist_dir", type=Path)
    parser.add_argument("repo")
    args = parser.parse_args()

    export_attestations(args.dist_dir, args.repo)


if __name__ == "__main__":
    main()
