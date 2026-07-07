# Deploy runbook

This repository does not ship a long-lived production cluster
definition in-tree and has no in-tree Kubernetes manifests, so
deployment verification focuses on reproducible local and GitHub-hosted
delivery paths.

## Local API smoke

1. `uv sync --frozen --all-extras`
2. `uv run uvicorn --app-dir src newsdom_api.main:app --host 127.0.0.1 --port 8000`
3. Verify:
   - `curl -fsS http://127.0.0.1:8000/health`
   - `http://127.0.0.1:8000/docs`
   - `http://127.0.0.1:8000/redoc`

## Container smoke

1. `docker build -t newsdom-api .`
2. `docker run --rm -p 18080:8000 newsdom-api`
3. Verify:
   - `curl -fsS http://127.0.0.1:18080/health`
   - `curl -fsS -F "file=@sample.pdf" http://127.0.0.1:18080/parse`

The default image already includes the MinerU runtime and sets
`NEWSDOM_MINERU_BIN=mineru`, so container smoke should treat `/parse`
as part of the supported contract instead of a docs-only shell.

`/health` proves the API process is serving but does not validate a full `/parse` round-trip, MinerU execution, or OCR artifact production.

## Release smoke

- Confirm `.github/workflows/release.yml` still builds artifacts,
  checksums, and `*.intoto.jsonl` bundles.
- After a tag push or manual dispatch, verify the GitHub Release
  contains `SHA256SUMS.txt`, `release-manifest.json`, and
  `*.intoto.jsonl` assets.

## Failure handling

- Capture sanitized logs outside `tmp/` when a delivery path fails.
- Expect `/parse` failures to stay sanitized: `503 MinerU runtime
  unavailable` when the runtime cannot execute, and `502 MinerU output
  was incomplete` when required OCR artifacts are missing or invalid.
- Reconcile the failure against `README.md`, `CHANGELOG.md`, and the
  relevant workflow before closing the task.
