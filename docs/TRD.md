# NewsDOM API Technical Requirements Document

**Status:** Accepted documentation baseline for protected `develop` at `2f29e69c99a1201ce6b4e43370a463701efdc81c`  
**Last reviewed:** 2026-08-09

## 1. Technical objective

NewsDOM is a narrow FastAPI sidecar that turns bounded PDF input into a typed NewsDOM document by invoking a separately provisioned MinerU CLI and normalizing its artifacts. Runtime liveness, parser readiness, expensive-work admission, durable orchestration, host authorization, and release evidence are separate authorities.

## 2. Protected-develop runtime modules

| Module | Owns | Does not own |
|---|---|---|
| `main.py` | FastAPI surface, request/error mapping | MinerU internals, durable jobs |
| `service.py` | parse orchestration, temp workspace lifecycle | external queue/persistence |
| `mineru_runner.py` | executable resolution, subprocess invocation, artifact collection | model distribution/licensing |
| `dom_builder.py` | parser-output → canonical NewsDOM normalization | business semantic interpretation |
| `schemas.py` | public typed response contract | database schema |
| `synthetic.py` / `equivalence.py` | deterministic fixtures/structural comparison | customer-corpus validity by themselves |

The default image is the API service and does not silently claim to bundle MinerU.

## 3. Synchronous parse flow

```text
HTTP upload
→ bounded request/input validation
→ temporary workspace
→ configured MinerU execution
→ bounded artifact discovery/read
→ typed NewsDOM normalization
→ sanitized response
→ deterministic cleanup
```

The service must never treat “process started” as a successful parse. Expected output artifacts and normalization must complete.

## 4. Liveness/readiness contract

Protected `develop` currently exposes liveness `/health`. PR #539 is the active implementation of the stronger contract in which `/ready` also evaluates required authentication configuration and MinerU executable availability. Until integrated, docs and deploy probes must not represent `/health` as parser traffic readiness.

After #539 integration, readiness is still not equivalent to a full customer-document end-to-end parse: it is a bounded traffic-admission prerequisite.

## 5. Authentication boundary

PR #539 is active-PR. Its accepted target is authentication before multipart body consumption and parser/resource allocation, with production fail-closed configuration and a narrowly explicit development bypass. No current protected-branch documentation may promote it early.

Host/gateway authentication can be stronger but does not remove the leaf service's own production safety requirement if the leaf can be reached directly.

## 6. Resource and concurrency boundary

All source-controlled limits are finite and validated. PR #548 introduces the first process-local non-waiting parser admission limiter and remains active-PR/stacked. The intended invariant is:

```text
authentication
→ non-waiting process admission
→ multipart/body/temp allocation
→ parser
→ release lease on every terminal path
```

No in-process unbounded wait queue is accepted. Multi-replica global fairness is a future durable orchestration concern; process-local admission remains a last-resort resource boundary.

## 7. Durable asynchronous target

Durable high-cost processing is **accepted target, not current implementation**. The design requires:

- opaque `parse_job` identity;
- tenant/principal-scoped idempotency key;
- durable states such as `accepted`, `queued`, `running`, `succeeded`, `failed`, `cancel_requested`, `cancelled`, `quarantined`;
- lease/fencing or equivalent single-active-worker ownership;
- bounded queue/admission and backpressure;
- cancellation checked before expensive stages and between safely interruptible stages;
- retry classification separating transient infrastructure from permanent validation/parser-contract failures;
- dead-letter/quarantine with explicit operator replay;
- immutable input/artifact digests and parser/version provenance;
- host-visible status without leaking source content;
- cleanup/recovery after worker crash.

A synchronous request must not be relabelled as a durable job to satisfy this requirement.

## 8. Idempotency and provenance target

A future durable request binds principal/tenant, source content digest, parse options, API/schema version, parser runtime/version, and idempotency key. Equivalent accepted retries resolve to the same logical job or an explicit prior result; they must not create duplicate expensive work silently.

Output provenance should bind source digest, parser identity/version, normalized schema version, relevant configuration digest, result digest, and exact producing release/commit where operationally available.

## 9. Data and persistence ownership

Current protected runtime owns no application database and no durable parse-job table. Temporary files are ephemeral. Host systems may persist returned NewsDOM data under their own authority.

If NewsDOM introduces durable job/control persistence, it must own a documented schema rather than writing directly to a consuming product's private database. See `docs/ERD.md`.

## 10. Error semantics

- malformed/unsupported input → bounded 4xx;
- configured parser runtime unavailable → bounded `503`;
- parser completed without required output/contract → bounded `502`;
- saturation after #548 → bounded `429` with explicit retry advice;
- unexpected internal error → generic bounded 5xx with internal detail retained only in approved operator evidence.

Errors must not echo temporary paths, command internals, credentials, raw source content, or unbounded provider output.

## 11. Security requirements

- validate uploaded media/size before expensive execution where feasible;
- do not interpret customer document content as instructions to the service/operator/agent;
- treat MinerU output as untrusted until schema/size/shape validation;
- use explicit subprocess argv, time/resource bounds, private temporary storage, and deterministic cleanup;
- preserve immutable action pins and dependency lock/provenance;
- separate deterministic CI/security gates from optional model/agent credentials.

## 12. Accuracy/validity requirements

Deterministic synthetic fixtures protect structural contracts. Commercial accuracy claims additionally require representative licensed/customer-approved document classes with expected text/layout/table/image/ordering outcomes and measurable error/fidelity. Benchmark manifests must preserve fixture provenance and avoid committing private customer source data without authorization.

## 13. Observability requirements

Emit bounded, content-minimized telemetry for request/job counts, status, parser duration, queue/admission rejection, failure class, artifact-size class and resource pressure. Never put raw PDFs, extracted text, credentials, internal file paths, or tenant-crossing identifiers into general metrics.

## 14. Packaging and deployment

- API package/container build is reproducible from reviewed lock/source;
- parser runtime path/config is explicit;
- default image/documentation agree on whether MinerU is bundled;
- `/health` and future `/ready` probes are not conflated;
- Compose/Kubernetes examples remain examples, not evidence of managed deployment readiness;
- release manifests, checksums, SBOM/provenance/attestation are verified before release claim.

## 15. Verification gates

- exact 100% owned production statement/branch coverage;
- complete public shipped-symbol docstrings;
- compile/lint/full pytest;
- subprocess/runtime-unavailable/incomplete-output/malformed-input/cleanup tests;
- active auth/admission changes add body-not-read and concurrency/cancellation regressions;
- package/container/release smoke;
- exact-current-head required GitHub CI/security/review.

## 16. Change control

A change that introduces persistence, durable queues, tenant authority, new outbound capability, parser distribution, new public schema version, authentication semantics, retry/replay semantics, or resource-admission ownership requires an ADR and synchronized PRD/TRD/Architecture/UML/ERD/Threat/Test/Operability/Traceability updates.
