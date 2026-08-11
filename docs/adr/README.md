# Architecture Decision Records

This directory contains durable Architecture Decision Records for `newsdom-api`. `Accepted` means the decision governs current architecture; `Proposed` may describe an active PR or accepted target and must not be advertised as protected-branch implementation until its promotion conditions are satisfied.

## Index

| ADR | Title | Status | Date |
|---|---|---|---|
| [0001](0001-defer-openssf-best-practices-enrollment.md) | Defer OpenSSF Best Practices Enrollment | Accepted | 2026-04-24 |
| [0002](0002-external-parser-and-liveness.md) | Keep MinerU external and liveness weaker than parser readiness | Accepted | 2026-08-09 |
| [0003](0003-authentication-before-body-and-readiness.md) | Authenticate before request-body cost and separate readiness from liveness | Proposed — PR #539 | 2026-08-09 |
| [0004](0004-process-local-parser-admission.md) | Non-waiting process-local parser admission as leaf safety | Proposed — PR #548 | 2026-08-09 |
| [0005](0005-durable-async-jobs-and-idempotency.md) | Durable idempotent jobs with worker fencing, cancellation, and replay | Proposed target | 2026-08-09 |

## ADR status

- **Proposed**: decision is under review, implemented only on an active PR, or accepted as target architecture without protected implementation.
- **Accepted**: decision governs protected architecture and representative source/evidence exists where implementation is required.
- **Deprecated**: no longer recommended but retained for historical compatibility.
- **Superseded**: replaced by a later ADR, which must be linked from the old record.
- **Rejected**: considered and deliberately not adopted.

## ADR triggers

Create or update an ADR when a change moves the external-parser boundary, changes liveness/readiness/authentication authority, changes resource/admission ownership, introduces persistence/durable job/idempotency/retry/cancellation semantics, changes public schema/versioning, moves tenant/security authority, or changes release/provenance requirements.

An ADR status alone is not a release or implementation claim. Keep `docs/PRD.md`, `docs/TRD.md`, `ARCHITECTURE.md`, `docs/UML.md`, `docs/ERD.md`, `docs/THREAT_MODEL.md`, `docs/TEST_STRATEGY.md`, `docs/OPERABILITY.md`, and `docs/TRACEABILITY.md` synchronized with source and exact evidence.
