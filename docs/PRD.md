# NewsDOM API Product Requirements Document

**Status:** Accepted documentation baseline for protected `develop` at `2f29e69c99a1201ce6b4e43370a463701efdc81c`  
**Last reviewed:** 2026-08-09

## 1. Product purpose

NewsDOM API is an independently deployable PDF-to-structured-document sidecar. It accepts bounded PDF input, delegates document parsing to a separately provisioned MinerU runtime, normalizes parser output into a stable typed NewsDOM JSON contract, and returns sanitized failure states suitable for use by naruon or another host.

The service is not a document-management system, browser, OCR model host, mailbox, or general ETL platform. It keeps the expensive/untrusted parser execution boundary small and explicit.

## 2. Protected-develop product claims

The following are current protected-`develop` claims:

- FastAPI service exposing liveness `/health` and bounded `/parse` behavior;
- external MinerU executable resolution and subprocess orchestration rather than pretending the default API image contains the parser runtime;
- typed/sanitized `503` runtime-unavailable and `502` incomplete-output behavior;
- canonical NewsDOM response models and deterministic DOM normalization;
- synthetic and provenance-noted fixtures for repeatable validation;
- package/container/release evidence including required security and supply-chain workflows;
- developer/maintainer architecture, security, release, runtime-data, review, and workflow documentation;
- `develop` as integration branch and `main` as stable release branch.

## 3. Active-PR boundaries

Open PRs are not protected-branch product claims.

- **PR #539 — active-PR:** fail-closed parser authentication and separate `/ready` traffic-readiness semantics. Until merged, protected `develop` does not claim this production authentication/readiness contract.
- **PR #548 — active-PR and stacked:** process-local non-waiting parser admission/backpressure. It must be refreshed after its authentication predecessor integrates.
- **PR #575 — active-PR:** raises the pypdf security floor to 6.15.0 with explicit CVE/lock regression evidence.
- Other narrow UX/performance/filter PRs remain ordinary active work and do not change protected-branch capability until integrated.

## 4. Primary users

### API/product integrator

Needs a stable parse contract, explicit parser-unavailable state, bounded errors, and a sidecar that can be deployed independently from the consuming application.

### Platform/SRE engineer

Needs honest liveness/readiness, bounded expensive-work admission, reproducible containers/releases, observable failure classes, safe rollback, and no false-green parser readiness.

### Security/data-governance engineer

Needs strict PDF/input boundaries, no raw secret/internal-path leakage, least privilege, supply-chain evidence, and a clear distinction between request metadata and customer document content.

## 5. Functional requirements

### PRD-FR-001 Parse PDF into canonical NewsDOM

The service SHALL accept a bounded PDF upload, validate enough input structure to reject unsupported/malformed input safely, execute the configured MinerU parser, and map produced artifacts into the versioned typed NewsDOM response contract.

### PRD-FR-002 Parser runtime truthfulness

The API SHALL distinguish “the FastAPI process is alive” from “the configured parser runtime can serve parse traffic.” It MUST NOT claim parser readiness solely because `/health` is green. The stronger readiness behavior is active-PR until #539 lands.

### PRD-FR-003 Sanitized failures

Parser-runtime, incomplete-output, validation, and unexpected failure classes SHALL map to bounded external errors without raw temporary paths, parser internals, credentials, or customer document content.

### PRD-FR-004 Resource boundedness

Upload size, parser execution, temporary storage, output collection, and future concurrency must have explicit finite bounds. Expensive work MUST fail closed rather than create an unbounded in-process queue. The first process-local admission implementation is active-PR #548.

### PRD-FR-005 Independent deployment

NewsDOM SHALL remain usable as a standalone sidecar. Naruon or another host may add tenant identity, durable orchestration, quotas, audit, and product workflows, but the leaf parser must preserve its own input/runtime safety boundary.

### PRD-FR-006 Durable asynchronous processing — accepted target

For long/high-cost documents, a commercial deployment target SHOULD provide a durable asynchronous job lifecycle with opaque job identity, idempotent submission, bounded queue/backpressure, status, cancellation, retry classification, quarantine/dead-letter behavior, and replay-safe audit. This is **accepted target / not implemented on protected develop**; no current synchronous endpoint may be described as durable-job processing.

### PRD-FR-007 Tenant and usage control — accepted target

A managed multi-tenant deployment SHOULD support authenticated tenant/resource authority, quotas/rate policy, privacy-safe audit, regional/retention policy, and controlled export. These controls are not inferred from request-supplied organization strings or sequential identifiers.

### PRD-FR-008 Accuracy and fidelity evidence — accepted target

Product claims about extraction quality SHALL be tied to versioned representative document sets and measurable structural/content fidelity. Synthetic fixtures are necessary for deterministic regression but are not sufficient evidence for every customer-document class.

## 6. Non-functional requirements

### Reliability

- no false-green parse readiness;
- deterministic failure classification;
- idempotent/replay-safe semantics where durable jobs are introduced;
- cleanup of temporary resources after success/failure/cancellation;
- controlled retry only for evidence-classified transient boundaries.

### Security

- fail closed on malformed/oversized input and parser/runtime ambiguity;
- do not leak raw source content, temporary paths, internal exception chains, tokens, or credentials in public errors/logs;
- immutable/pinned supply-chain inputs and current-head security evidence;
- no blanket PII masking that destroys the parse workflow; protect content through purpose-bound access, minimization, encryption, retention, and audit.

### Quality

- exact 100% owned production statement and branch coverage;
- complete public shipped-symbol docstrings;
- realistic subprocess/error/cleanup/concurrency/security/package/container/release tests;
- required GitHub checks on the unchanged exact head before integration/release.

### Observability

The product SHOULD expose bounded metrics/traces for request/job latency, parser execution, failure class, admission rejection, queue depth when a durable queue exists, and resource pressure without copying customer document contents or credentials into telemetry.

## 7. Non-goals

- bundling MinerU invisibly into the current default API image while documentation claims otherwise;
- pretending `/health` proves parser usability;
- fabricating durable job, tenant, quota, or audit semantics before those are implemented;
- implementing customer document business interpretation in the parser sidecar;
- bypassing provider/site/license/security controls to obtain parser/model assets.

## 8. Integration requirements

Naruon and other CWL services consume NewsDOM through an explicit versioned API/sidecar boundary. Hosts own their application authorization and persistent workflow state. NewsDOM does not directly query another product's private database. A host outage or absent central CWL service must not remove standalone parsing capability when the configured parser runtime itself is available.

## 9. Release acceptance

A release requires one exact integrated protected release head with required CI/security/review, 100% coverage/docstrings, package/container build and reinstall/smoke, SBOM/provenance/attestation, parser-runtime compatibility evidence, rollback/recovery/runbook coherence, and representative parse acceptance. Active PRs, queued checks, predecessor-head success, or architecture prose are not release evidence.

## 10. Buyer-visible roadmap order

1. fail-closed production authentication + honest readiness (#539);
2. bounded process-level parser admission/backpressure (#548 after stack repair);
3. representative upload/memory evidence without premature chunk-size claims;
4. durable asynchronous jobs, idempotency, cancellation, retry/quarantine;
5. tenant quotas/audit/observability and operational SLO evidence;
6. versioned customer-document accuracy/fidelity benchmark;
7. reproducible release/provenance and managed deployment acceptance.
