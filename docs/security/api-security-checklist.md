# API security checklist

Apply this checklist whenever the FastAPI surface changes.

## In-scope endpoints

- `/health`
- `/ready`
- `/parse`
- `/docs`
- `/redoc`

## Baseline checks

- validate upload handling and content-type expectations for `/parse`
- ensure error messages do not leak private reference paths, secrets,
  credentials, configured capacity, active lease counts, or another tenant's
  activity
- keep synthetic fixtures in tests and examples; never use private reference
  inputs in public evidence
- verify request handling fails safely when MinerU is missing or returns
  incomplete outputs
- confirm `/health` is liveness-only and `/ready` represents authentication
  configuration plus MinerU runtime availability
- authenticate `/parse` before admission so unauthenticated requests cannot
  consume parser leases or use overload behavior as a capacity oracle
- acquire a non-waiting process-local lease before the multipart body,
  temporary-file allocation, PDF validation, or MinerU execution
- return fixed `429 Too Many Requests`, exact `Retry-After: 1`, and no-store
  cache headers when every process lease is in use
- release admission leases after success, validation failure, backend failure,
  unhandled exception, and request cancellation
- keep `NEWSDOM_MAX_CONCURRENT_PARSES` immutable, bounded to `1..128`, and
  explicit in production deployment examples
- treat the process boundary as a last-resort resource control; retain
  gateway-level per-tenant rate limits, quotas, and cluster resource limits
- do not add an unbounded in-process request or upload queue
- confirm docs endpoints remain informational and do not imply unsupported
  authentication, execution, queueing, or durability guarantees

## Verification expectations

- unit and integration tests for parsing, authentication, readiness, overload,
  cancellation, and sanitized error handling
- a realistic concurrent burst proving active parser count never exceeds the
  configured process budget and excess work never reaches multipart parsing
- OpenAPI evidence for 401, 413, 415, 422, 429, 502, and 503 responses
- live localhost smoke for `/health`, `/ready`, `/docs`, and `/redoc` when docs
  or screenshots change
- deployment smoke that holds every lease, verifies one fixed pre-body 429,
  releases one request, and proves capacity recovery
- resource evidence for any capacity increase: peak RSS/VRAM, temporary storage,
  parser latency, error rate, replica count, and rollback threshold
- PR and workflow review whenever GitHub Actions, release, or code-scanning
  posture changes
