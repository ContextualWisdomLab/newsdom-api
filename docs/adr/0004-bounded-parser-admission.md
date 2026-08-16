# ADR-0004: Bound concurrent parser admission

## Status

Accepted

## Context

Issue #534 is the buyer-visible upload-ingestion gap: a replica can accept
an unbounded number of concurrent `/parse` bodies, each up to 20 MiB, and
then run MinerU. Closed PR #548 drafted process-local admission; this
record lands that contract on current `develop` without selecting a new
upload chunk size. Isolation of `pypdf` (#624 / #632) stays a separate
slice.

This sidecar has no browser UI. Storybook and design tokens belong in
clearfolio. NewsDOM stays independently deployable and reusable as a
naruon module. A gateway may add tenant fairness; bypassing the gateway
must not restore unbounded in-process admission.

## Decision

- Freeze `NEWSDOM_MAX_CONCURRENT_PARSES` on `RuntimeSettings` (default
  `1`, range `1..128`) when the FastAPI application is created.
- Bind one `ParseAdmissionLimiter` per application. Use a non-waiting
  `threading.BoundedSemaphore` so a double release cannot expand
  capacity.
- Authenticate first. Acquire one lease before multipart parsing,
  temporary-file allocation, PDF validation, or MinerU.
- When saturated, return the fixed `429 Too Many Requests` body and
  `Retry-After: 1`. Do not enqueue the request.
- Keep the production upload chunk at 8 KiB until a reviewed benchmark
  on representative PDFs selects another value.

## Consequences

### Positive

- One replica cannot start an unbounded number of MinerU jobs.
- Callers get a retryable 429 instead of a silent hang or a retried 503.
- naruon can apply outer backpressure without replacing this last-resort
  process cap.

### Negative

- Default capacity `1` is conservative. Operators must raise the cap or
  add replicas after measuring RSS under their PDF mix.
- Chunk size remains 8 KiB until #534's benchmark matrix is accepted.

## Rollback

Restore the previous image, or set `NEWSDOM_MAX_CONCURRENT_PARSES` to
the previous replica's value. There is no flag that disables admission.
