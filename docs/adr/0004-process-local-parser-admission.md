# ADR-0004: Use non-waiting process-local parser admission as a leaf safety boundary

**Status:** Proposed — implemented on active stacked PR #548, not protected `develop`  
**Date:** 2026-08-09

## Context

MinerU parsing is CPU/memory/disk intensive. An API process that accepts unlimited concurrent parses can exhaust resources before downstream product gateways or cluster autoscaling react. A process-local queue would merely move the overload inside the process and increase cancellation/recovery complexity. Authentication must also happen before scarce parser capacity is consumed.

## Decision

If PR #548 is refreshed onto its accepted authentication predecessor and integrated:

- each FastAPI application owns one finite parser-admission limiter;
- admission is non-waiting: capacity is acquired immediately or the request receives bounded `429 Too Many Requests` plus explicit retry advice;
- authentication/configuration checks run before admission;
- admission runs before multipart body consumption, temporary-file allocation, PDF validation, and MinerU execution;
- the lease is released exactly once after every success, validation failure, parser/runtime failure, unexpected exception, and cancellation path;
- no in-process waiting queue is created;
- per-process capacity remains a leaf safety boundary even if a future gateway, durable queue, or cluster scheduler adds stronger global fairness;
- replica capacity is documented as multiplicative rather than pretending one process-local semaphore is a distributed quota.

## Alternatives rejected

### Unbounded concurrency

Rejected because expensive parser work can exhaust CPU/RAM/temp storage and deny service.

### Blocking in-process semaphore queue

Rejected as the primary overload behavior because request tasks would accumulate in process without durable ownership, bounded queue age, cancellation recovery, or restart persistence.

### Redis/distributed limiter in the leaf as the first control

Rejected for this slice because NewsDOM must remain independently deployable and process-local admission still protects each instance even when external coordination fails. Global fairness/tenant scheduling belongs to the future durable orchestration boundary.

## Consequences

- Exact concurrent ASGI tests must prove no more than configured capacity reaches downstream parsing and rejected requests do not read bodies/create temp files.
- Capacity defaults must be conservative and tuned only from reproducible resource evidence; this ADR does not select an upload chunk size or promise throughput.
- A 429 is an explicit overload state, not a generic internal failure.
- The future durable job service may accept jobs while leaf workers remain protected by this limiter.
- This ADR remains Proposed until #548 is rebuilt on the accepted predecessor/current `develop`, earns fresh exact-head CI/security/review, and merges.