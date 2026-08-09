# ADR-0005: Use durable idempotent jobs for long-running parse orchestration

**Status:** Proposed — accepted target architecture, no protected implementation yet  
**Date:** 2026-08-09

## Context

A synchronous HTTP request is a poor ownership boundary for long/high-cost PDF parsing. Client disconnects, process restarts, duplicate retries, parser crashes, overload, cancellation, and operator replay all need durable state if NewsDOM is to support commercial batch/large-document processing without losing work or duplicating expensive execution. A process-local admission semaphore protects one instance but does not provide a queue, idempotency, replay, or cross-restart ownership.

## Decision

The future durable processing boundary will use NewsDOM-owned persistent job state and a bounded durable queue with these invariants:

- submission is tenant/principal scoped and idempotent across the exact tuple of caller idempotency key, source digest, parse options, API/schema/model/runtime contract version;
- one accepted logical submission receives one opaque `parse_job_id`;
- each execution is an immutable numbered `parse_attempt`;
- a worker publishes state/result only while holding the current fenced lease/ownership token for the job;
- stale/expired workers cannot overwrite a later attempt;
- automatic retry is permitted only for explicitly classified transient failure classes and is bounded by count/backoff/time budget;
- deterministic validation/parser-contract failures do not enter a retry storm;
- exhausted/permanent failures move to an explicit quarantine/dead-letter state;
- cancellation is a durable intent that requires worker acknowledgement/cleanup at safe interruption points; it is not implemented as merely changing a status string;
- operator replay creates a new attempt and retains prior failure/audit evidence;
- source, parser/runtime, configuration, dependency/release and result digests are captured in immutable reproducibility evidence;
- persistent NewsDOM job/artifact state remains behind a versioned API and never writes directly into a consuming product's private database;
- process-local admission remains a leaf worker safety control after durable orchestration is added.

## Alternatives rejected

### Keep synchronous requests only

Rejected for the commercial long-running path because client/network lifetime would remain the effective job owner and restart/retry/cancel/replay semantics would be ambiguous.

### Add an in-memory queue

Rejected because it is not durable across process loss, cannot safely own replay/idempotency/audit, and would reintroduce unbounded or hard-to-recover wait states.

### Let the consuming host own NewsDOM's internal parse queue/database directly

Rejected because it destroys standalone operation and creates hidden cross-repository persistence coupling. Hosts may orchestrate through the public API, but NewsDOM owns the state required to make its own durable job contract true.

## Consequences

- A physical persistent schema, migrations/rollback, backup/restore, retention/deletion, tenant authorization, queue capacity, worker fencing and replay tests are required before this ADR can move to Accepted/implemented.
- Public synchronous `/parse` may remain as a bounded convenience path, but it cannot be relabelled as the durable job API.
- New endpoints/events need an explicit versioned contract for submission/status/cancel/replay/result and clear failure/degraded semantics.
- Operator metrics include queue depth/age, running leases, retries/quarantine/cancellation and cleanup, without copying customer document content into telemetry.
- No RPO/RTO/SLO is invented here; operational objectives require measured deployment evidence.

## Acceptance evidence

Before promotion require realistic tests for duplicate submissions, changed-option submissions, queue saturation, worker crash/restart, stale lease publication, transient retry, permanent failure, retry exhaustion, cancellation races, replay, cross-tenant denial, result/provenance binding, migrations/rollback and backup/restore; then exact-head CI/security/coverage/review and protected-main operational acceptance.
