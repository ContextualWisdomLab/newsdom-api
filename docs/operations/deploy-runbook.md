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
     only after a compatible MinerU runtime is installed or exposed through
     `NEWSDOM_MINERU_BIN`

The default image ships the API service only and does not bundle the MinerU runtime,
so container smoke should treat `/parse` as an external-runtime check rather
than a default-image contract.

`/health` proves the API process is serving but does not validate a full `/parse` round-trip, MinerU execution, or OCR artifact production.

## Release smoke

- Confirm `.github/workflows/release.yml` still builds artifacts,
  checksums, and `*.intoto.jsonl` bundles.
- After a tag push or manual dispatch, verify the GitHub Release
  contains `SHA256SUMS.txt`, `release-manifest.json`, and
  `*.intoto.jsonl` assets.

## Failure handling

- Capture sanitized logs outside `tmp/` when a delivery path fails.
- Expect `/parse` failures to stay sanitized: use generic
  client-facing details for `503 Service Unavailable` when the backend
  runtime cannot execute and `502 Bad Gateway` when required OCR
  artifacts are missing or invalid.
- Reconcile the failure against `README.md`, `CHANGELOG.md`, and the
  relevant workflow before closing the task.

## Fail-closed authentication migration for 0.3.0

Parser authentication is required by default. The previous default-open behavior
must not be carried into a production or shared deployment. Configure all three
settings before routing traffic:

```text
NEWSDOM_AUTH_MODE=required
NEWSDOM_RUNTIME_PROFILE=production
NEWSDOM_API_TOKEN=<secret-store reference>
```

Use `GET /health` for process liveness and `GET /ready` for traffic readiness.
A process may be live while `/ready` returns 503 because the required token or
MinerU executable is unavailable. Keep it out of the load-balancer endpoint set
until readiness succeeds.

The development-only bypass requires both values below and must be confined to
an isolated local workstation:

```text
NEWSDOM_AUTH_MODE=disabled
NEWSDOM_RUNTIME_PROFILE=development
```

This bypass is not a production rollback. To roll back a failed production
upgrade, restore the previous release or repair secret/MinerU injection while
keeping required authentication. Never log the token, its length, or a hash that
could become a reusable credential oracle.
