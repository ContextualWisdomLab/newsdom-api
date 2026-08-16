# API security checklist

Apply this checklist whenever the FastAPI surface changes.

## In-scope endpoints

- `/health`
- `/parse`
- `/docs`
- `/redoc`

## Baseline checks

- validate upload handling and content-type expectations for `/parse`
- keep process-local `/parse` admission non-waiting and return `429`
  with `Retry-After` before multipart body reads when the replica is full
- ensure error messages do not leak private reference paths,
  secrets, or credentials
- keep synthetic fixtures in tests and examples; never use private
  reference inputs in public evidence
- verify request handling fails safely when MinerU is missing or
  returns incomplete outputs
- confirm docs endpoints remain informational and do not imply
  unsupported authentication or execution guarantees

## Verification expectations

- unit/integration tests for parsing and error handling
- live localhost smoke for `/health`, `/docs`, and `/redoc` when docs
  or screenshots change
- PR/workflow review whenever GitHub Actions, release, or code-scanning posture changes
