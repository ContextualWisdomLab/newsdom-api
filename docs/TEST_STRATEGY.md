# NewsDOM API Test Strategy

**Status:** Accepted documentation baseline  
**Last reviewed:** 2026-08-09

## Mandatory repository gates

- Python compile/lint;
- full deterministic pytest suite;
- exact 100% owned production statement coverage;
- exact 100% owned production branch coverage;
- complete public shipped-symbol docstrings;
- package/build/install smoke;
- container/security/dependency/CodeQL/Semgrep/fuzz/release evidence as required by repository policy;
- exact-current-head review/check evidence before protected integration.

Queued, pending, skipped-required, cancelled, absent, stale, predecessor-head, synthetic-only, infrastructure-only, or failed evidence is never passing.

## Synchronous parse contract tests

### Input boundary

Cover valid PDFs, malformed headers, non-PDF bytes, oversized input, hostile filenames, Unicode/control characters, multipart anomalies, and configuration bounds. RED tests must prove the intended boundary rather than fail during fixture/setup.

### Parser runtime

Use deterministic test doubles/fixtures for unit behavior and bounded real integration where the runtime is approved. Cover executable absent, startup failure, non-zero exit, timeout, incomplete required artifacts, malformed/oversized JSON/output, and unexpected files. Public failures must remain sanitized.

### DOM normalization

Use synthetic and provenance-noted fixtures to test text/layout/page/article/image/header/footer/page-number structure, stable schema serialization, malformed parser blocks, missing optional fields, non-finite values, Unicode, and deterministic ordering.

### Cleanup

Every success/failure/cancellation path must prove temporary resources are removed or moved only to a separately governed protected artifact store. A failed cleanup must be observable and never silently reclassify leaked state as success.

## Liveness/readiness tests

Protected `develop` liveness tests cover `/health` only. PR #539 must prove:

- production auth config absent/invalid → fixed fail-closed readiness/parse behavior;
- required auth is checked before multipart body consumption;
- MinerU unavailable → `/ready` not traffic-ready;
- `/health` remains process liveness;
- readiness does not claim a full end-to-end document parse.

These become mainline tests only after #539 merges.

## Admission/concurrency tests

PR #548 must prove the application-local limiter using actual concurrent ASGI requests, not only semaphore unit calls:

- capacity N admits at most N downstream parses;
- excess requests return immediate bounded 429/Retry-After;
- rejected requests do not consume the upload body or create temp files;
- lease releases exactly once on success, validation failure, parser failure, unexpected exception, and cancellation;
- application instances do not share capacity accidentally;
- bounded burst behavior has no in-process waiting queue.

## Security/adversarial tests

Mirror `docs/THREAT_MODEL.md`:

- argument-injection-like option values;
- oversized/malformed PDFs and parser artifacts;
- internal-path/exception/source-content leakage;
- duplicate/malformed auth headers after #539;
- dependency/runtime substitution and known-vulnerable floor regression;
- prompt-injection strings inside extracted text treated as data;
- package/container action/source pin and provenance expectations.

## Accuracy/fidelity benchmark

Synthetic tests validate deterministic structure, not universal extraction validity. Commercial accuracy evidence uses a versioned, rights-cleared representative corpus with expected outputs and source manifests. Report at least document-class slices for:

- text block precision/recall or aligned character/token fidelity as appropriate;
- page/section ordering correctness;
- table/image/layout structural fidelity where the public schema claims it;
- malformed/low-quality scan failure/abstention behavior;
- parser/runtime/version-specific regressions.

Do not declare a single aggregate percentage as universal customer accuracy without slice coverage and confidence/uncertainty.

## Performance/resource benchmark

Any upload chunk/admission/parser-throughput claim requires a reproducible fixture hash, environment/runtime manifest, concurrency, case-local memory method, latency distribution, CPU time, temp bytes, event-loop delay, and rollback baseline. Process-lifetime high-water metrics must not be misreported as per-case deltas.

## Durable job target tests — not current behavior

Before durable async processing is promoted require:

- idempotency: same tenant/principal/key/source/options/version resolves to one logical accepted job;
- deliberate option/version changes produce distinct jobs;
- fenced stale worker cannot publish after a later attempt owns the job;
- worker crash/restart recovery;
- bounded retry only for classified transient failures;
- permanent validation/parser-contract failures quarantine without retry storm;
- cancellation before run, during safe interruptible stage, and after result publication;
- duplicate submission/race and queue saturation;
- explicit replay from quarantine with immutable attempt history;
- cross-tenant job/artifact denial;
- retention/deletion/backup/restore;
- exact source/parser/config/dependency/release/result provenance binding.

## Observability tests

Verify metrics/traces preserve status, latency, parser/admission/job state and bounded identifiers while excluding raw PDF/extracted text, authorization values, private temporary paths, and credentials.

## Documentation contract tests

CI should fail if canonical PRD/TRD/UML/ERD/Threat/Test/Operability/Traceability/ADR map disappears, if active PRs are promoted to implemented-main prematurely, if current persistence is falsely described as durable, or if `/health` is described as parser readiness before the implementing contract is on protected `develop`.

## Release acceptance

Re-run the full exact-head suite on the integrated release candidate, then package/container reinstall/smoke, security/fuzz, SBOM/provenance/attestation, representative parser-runtime acceptance, migration/rollback/backup evidence where persistence exists, and independent review. No predecessor-head success transfers after rebase/merge/release changes.