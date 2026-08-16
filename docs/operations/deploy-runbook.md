# Deploy runbook

This repository ships reproducible local, container, and Kubernetes deployment
examples. The Kubernetes manifest under
`docs/operations/kubernetes-deployment.yaml` is an **Unreleased** reference
configuration, not a published production release artifact. Before applying it,
replace the `:unreleased` image placeholder with a verified image digest from the
release acceptance record.

## Local API smoke

1. `uv sync --frozen --all-extras`
2. Export the explicit production contract:

   ```text
   NEWSDOM_AUTH_MODE=required
   NEWSDOM_RUNTIME_PROFILE=production
   NEWSDOM_API_TOKEN=<local smoke secret>
   ```

3. `uv run uvicorn --app-dir src newsdom_api.main:app --host 127.0.0.1 --port 8000`
4. Verify:
   - `curl -fsS http://127.0.0.1:8000/health`
   - `curl -fsS http://127.0.0.1:8000/ready`
   - `http://127.0.0.1:8000/docs`
   - `http://127.0.0.1:8000/redoc`

`GET /health` proves process liveness. `GET /ready` proves that authentication
configuration and the MinerU executable are ready to accept traffic.

## Container smoke

1. `docker build -t newsdom-api:unreleased .`
2. Run with an explicit secret and production settings:

   ```bash
   docker run --rm -p 18080:8000 \
     -e NEWSDOM_AUTH_MODE=required \
     -e NEWSDOM_RUNTIME_PROFILE=production \
     -e NEWSDOM_API_TOKEN="$NEWSDOM_API_TOKEN" \
     newsdom-api:unreleased
   ```

3. Verify:
   - `curl -fsS http://127.0.0.1:18080/health`
   - `curl -fsS http://127.0.0.1:18080/ready`
   - `curl -fsS -H "Authorization: Bearer $NEWSDOM_API_TOKEN" -F "file=@sample.pdf" http://127.0.0.1:18080/parse`
     only after a compatible MinerU runtime is installed or exposed through
     `NEWSDOM_MINERU_BIN`.

The default image ships the API service only and does not bundle the MinerU
runtime, so container smoke should treat `/parse` as an external-runtime check
rather than a default-image contract. A container may be live while remaining
unready; never route production traffic from `/health` alone.

## Kubernetes smoke

1. Replace `ghcr.io/contextualwisdomlab/newsdom-api:unreleased` in
   `docs/operations/kubernetes-deployment.yaml` with the exact published
   `ghcr.io/contextualwisdomlab/newsdom-api@sha256:<digest>` accepted by the
   release workflow. Tags are not deployment identity.
2. Create `newsdom-api-runtime` in namespace `newsdom-system` with key
   `api_token`; never commit the secret value.
3. Ensure the MinerU executable and models are present in the deployed image or
   supplied through a separately reviewed read-only volume. The example exposes
   bounded writable `emptyDir` volumes only for `/tmp` and the runtime cache.
4. Apply the manifest and verify that the namespace enforces the Restricted Pod
   Security profile.
5. Confirm the pod runs as UID/GID 10001 with `RuntimeDefault` seccomp,
   privilege escalation disabled, all Linux capabilities dropped, and a
   read-only root filesystem.
6. Verify `GET /health` for liveness and `GET /ready` for Service endpoint
   readiness before sending authenticated parser traffic.

The repository-owned GHCR path is the intended image source. Production cluster
admission policy must allow only the reviewed organization/repository path and
must verify the accepted digest or signature; the example itself cannot declare
a cluster-specific registry trust policy.

## Release smoke

- Confirm `.github/workflows/release.yml` still builds artifacts, checksums,
  container images, and `*.intoto.jsonl` bundles.
- Confirm package metadata, FastAPI/OpenAPI version, image tag, CHANGELOG release
  section, checksums, and provenance all identify the same release.
- After a tag push or manual dispatch, verify the GitHub Release contains
  `SHA256SUMS.txt`, `release-manifest.json`, and `*.intoto.jsonl` assets.
- Record the accepted image digest and use that immutable digest in Kubernetes.

## Failure handling

- Capture sanitized logs outside request temporary directories when a delivery
  path fails.
- Expect `/parse` failures to stay sanitized: use generic client-facing details
  for `429 Too Many Requests` when this replica's parser admission cap is
  saturated (`Retry-After: 1`; wait and retry, then add replicas), `503
  Service Unavailable` when the backend runtime cannot execute, and `502
  Bad Gateway` when required OCR artifacts are missing or invalid.
- Size each replica with `NEWSDOM_MAX_CONCURRENT_PARSES` (default `1`,
  maximum `128`). The value is per process, not cluster-wide. Keep the
  8 KiB upload chunk until a reviewed upload-ingestion benchmark lands.
- Reconcile the failure against `README.md`, `CHANGELOG.md`, package/OpenAPI
  versions, and the relevant workflow before closing the task.

## Fail-closed authentication migration for planned 0.3.0

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
