# NewsDOM API Operability, Recovery, and Release Guide

**Status:** Accepted documentation baseline  
**Last reviewed:** 2026-08-09

This cross-cutting guide supplements the existing `docs/operations/deploy-runbook.md`. The existing runbook remains the procedure-level authority for current deployment/release commands; this document defines product state, failure, SLI, recovery, and future durable-job operating semantics.

## Health model

Never collapse these states:

1. **process liveness** — FastAPI can serve `/health`;
2. **traffic readiness** — required auth/runtime prerequisites can accept parse traffic; PR #539 active-PR;
3. **parser execution success** — one submitted document produced required parser artifacts;
4. **NewsDOM normalization success** — parser output became the public typed response;
5. **representative product acceptance** — approved document classes meet fidelity/security/performance criteria.

A lower state does not prove the next one.

## Key current SLIs

- request count/latency by sanitized outcome class;
- `503` parser-unavailable and `502` parser-contract failure rates;
- input validation rejection counts;
- parse subprocess duration/timeout rate;
- temporary-workspace cleanup failures;
- artifact/result size buckets without source content;
- package/container/runtime version and deployment identity;
- required security/check/release evidence state.

After #539/#548 integrate add auth-configuration readiness, unauthorized requests, readiness failure reason class, 429 saturation count, active parse count and lease-release anomaly evidence.

## Current deployment checklist

1. deploy a reviewed NewsDOM API package/container;
2. provision/configure the MinerU executable/runtime explicitly;
3. verify liveness without interpreting it as parser readiness;
4. after #539 integration, verify production auth configuration and `/ready` separately;
5. execute a controlled representative parse smoke in the approved environment;
6. verify sanitized errors, temp cleanup, package/runtime identities, logs and supply-chain evidence;
7. only then route intended traffic.

The current default API image does not bundle MinerU; deployment documentation/configuration must remain truthful about that dependency.

## Current incident classes

### API live, parser unavailable

Do not restart blindly. Verify configured executable path/runtime provisioning and version, permission to execute, container/host difference, and recent dependency/runtime changes. Keep traffic unready after #539; do not change `/health` to lie about parser availability.

### Parser non-zero/timeout/incomplete artifacts

Preserve bounded internal diagnostics, verify input validity and parser version, reproduce with approved fixture, separate deterministic parser-contract failure from transient host pressure, and fix/retry based on evidence. Never retry malformed deterministic input indefinitely.

### Temporary artifact leakage

Stop/reduce traffic if leakage risks cross-request/content exposure or disk exhaustion. Identify the terminal path that failed cleanup, add a regression, remove leaked artifacts according to retention/incident policy, and verify the next exact release.

### Security dependency finding

Prefer a reviewed dependency-floor/lock remediation with a regression over scanner suppression. PR #575 is the current pypdf 6.15.0 example. Re-run the exact current head; predecessor check success is not evidence for a changed lock.

## Capacity and overload

Before #548 integrates, do not claim application-level parse admission/backpressure. After integration:

- configure per-process capacity from measured environment/document evidence;
- verify authentication occurs before capacity and body allocation;
- treat 429 as explicit overload, not an internal error;
- scale replicas only with awareness that configured capacity multiplies per process;
- do not use process-local admission as a global fair queue.

## Durable async operations — accepted target

A future production job service requires the following operator-visible states and actions:

- accepted/queued/running/cancel_requested/succeeded/failed/cancelled/quarantined
  status, where `cancel_requested` is operator-visible and non-terminal while
  `cancelled` records acknowledged terminal completion;
- immutable attempts and failure classification;
- queue/admission depth and age;
- active fenced worker lease;
- idempotent duplicate-submission outcome;
- cancel request and acknowledged terminal result;
- bounded automatic retry count/backoff for transient classes;
- explicit quarantine/dead-letter and manual replay;
- source/result/parser/provenance digests;
- tenant-scoped audit and protected artifact retention.

A queue outage blocks new execution but must not lose already accepted durable jobs. Recovery re-observes durable state before retry/requeue rather than trusting the last worker response.

## Backup/recovery target

Current synchronous NewsDOM has no durable application database to back up; host data and release artifacts follow host/repository policy. Once durable NewsDOM job state exists:

- back up the owned control database and protected artifact metadata/store according to measured deployment RPO/RTO;
- test restore into an isolated environment;
- reconcile accepted/running jobs and invalidate stale worker leases;
- verify artifact digests and tenant authorization;
- replay only explicit safe states;
- retain immutable historical attempt/audit evidence rather than rewriting failed attempts as success.

Do not invent RPO/RTO values in architecture prose; publish them only from measured deployment/recovery evidence.

## Upgrade/rollback

- inspect CHANGELOG, dependency/security changes and parser compatibility;
- run exact-head full tests/security/build/container/provenance;
- canary with approved document fixtures;
- for public schema changes use explicit compatibility/versioning;
- preserve previous image/package/runtime compatibility and, after persistence exists, database rollback/backup strategy;
- on rollback re-run liveness/readiness and representative parse smoke.

## Observability/privacy

General metrics/traces/logs may include bounded status, timings, release/parser version, size buckets and opaque scoped IDs. They must not contain raw PDFs, extracted body text, auth headers, credentials, internal temp paths or cross-tenant job/source identifiers. Detailed protected diagnostics require purpose-bound operator access and retention.

## Release gate

Release only from one exact integrated protected release head with required independent review where policy requires it, CI/security/100% coverage/docstrings, package/container reinstall/smoke, representative parser-runtime acceptance, SBOM/provenance/attestation/checksums, rollback/recovery coherence, and truthful documentation. A feature or docs PR becoming green is not a release by itself.
