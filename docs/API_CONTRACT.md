# NewsDOM API Contract and Versioning

**Status:** Accepted current API contract plus explicitly labelled active-PR/accepted-target extensions.  
**Last reviewed:** 2026-08-09

## 1. Authority

FastAPI/Pydantic source remains the executable schema authority. This document defines compatibility, failure, maturity, and future durable-job semantics that cannot be reconstructed safely from generated OpenAPI alone. If prose and protected source disagree, repair the documentation/source drift; do not silently treat an active PR or target schema as shipped.

## 2. Current protected-`develop` HTTP surface

### `GET /health`

Purpose: **process liveness only**.

Current success shape is the typed health model (for example `{"status":"ok"}` under the current schema). A successful `/health` response does not prove MinerU is installed, authentication is configured, or an arbitrary PDF will parse.

### `POST /parse`

Purpose: synchronous bounded PDF → NewsDOM conversion.

Input:

- multipart PDF upload under the current endpoint contract;
- finite source-controlled upload/body limits;
- no client-provided executable path, shell command, or arbitrary parser program.

Success:

- one typed `ParseResponse` / NewsDOM document following the current Pydantic schema;
- response semantics derive from the requested source document only after MinerU output completes required normalization.

Representative current failure classes:

| HTTP | Meaning | Contract |
|---:|---|---|
| 4xx | invalid/unsupported client input | bounded message; no parser/internal/source leakage |
| 502 | parser ran/returned but required NewsDOM input artifact/contract is incomplete or invalid | bounded parser-contract failure |
| 503 | configured parser runtime is unavailable/unusable | bounded runtime-availability failure |
| 5xx | unexpected internal defect | generic external error; detailed evidence restricted to approved operator channel |

Exact response strings remain source/test authority and can evolve under compatibility rules below.

## 3. Active-PR API extensions

### PR #539 — authentication + readiness

**Maturity:** active-PR, not protected-branch behavior.

If integrated:

- production `/parse` requires fail-closed authorization before multipart body consumption/resource allocation;
- missing/unsafe server auth configuration fails closed;
- `GET /ready` reports bounded traffic-prerequisite state using authentication/runtime checks;
- `/health` remains liveness and does not become an alias for `/ready`;
- development bypass is explicit profile behavior, never a production fallback.

### PR #548 — saturation/backpressure

**Maturity:** active-PR-stacked on #539.

If integrated on an accepted predecessor/current `develop`:

- authenticated requests attempt a non-waiting per-process parser lease before body allocation;
- saturation returns `429 Too Many Requests` with documented retry advice;
- rejected requests do not enter an in-process waiting queue;
- lease release is guaranteed on every terminal/cancellation path.

No predecessor-head status/check/review transfers after stack refresh.

## 4. Schema/version compatibility

The current public NewsDOM Pydantic model is the serialization contract. Any breaking field removal/rename/type/cardinality/meaning change requires an explicit compatibility decision and release/version treatment.

Compatibility rules:

- adding optional fields with safe defaults can be backward-compatible when older consumers ignore unknown fields under their contract;
- changing requiredness, field type, ordering semantics that consumers rely on, identifier meaning, or failure-state meaning is potentially breaking;
- examples/descriptions improve developer experience but do not change runtime semantics unless source validation/serialization changes;
- generated OpenAPI must be tested against representative public models so documentation metadata cannot silently disappear;
- schema/version claims in docs must match package/runtime source on the exact release head.

If a future major NewsDOM JSON schema identifier is introduced, responses/results/provenance manifests bind the exact schema version used rather than inferring compatibility from package display version alone.

## 5. Identifier and authorization rules

Current synchronous `/parse` does not expose a durable job/object identifier. Temporary file names/paths are internal and are never public resource identities.

Future opaque IDs such as `parse_job_id`, `parse_attempt_id`, or result/artifact IDs:

- are not authorization by themselves;
- are tenant/principal scoped server-side;
- must be non-sequential opaque identifiers;
- cannot be accepted from a caller as proof of ownership;
- remain stable for the logical object they identify and are not silently reused for a different source/options/version contract.

## 6. Accepted-target durable job API — not implemented

The following is a target contract, not an existing endpoint set. Exact URLs may adapt through review, but semantics are normative for the design.

### Submit

Conceptual operation: `POST /parse-jobs`

Inputs:

- authenticated principal/tenant;
- PDF/source handle or bounded upload according to deployment profile;
- caller idempotency key;
- versioned parse options;
- requested public schema/API version.

Returns one opaque `parse_job_id` and a status representing the existing logical idempotent request if an equivalent accepted submission already exists.

The idempotency identity binds principal/tenant, caller key, source digest, parse options, and relevant API/schema/parser contract version. Same source bytes with intentionally different options/version are not forced into one job.

### Read status

Conceptual operation: `GET /parse-jobs/{parse_job_id}`

Returns only caller-authorized, bounded state such as:

- `accepted`
- `queued`
- `running`
- `succeeded`
- `failed`
- `cancel_requested`
- `cancelled`
- `quarantined`

It may include attempt count, bounded failure class, timestamps, retry eligibility/advice, and result availability but never raw parser logs/source content/secret values.

### Cancel

Conceptual operation: `POST /parse-jobs/{parse_job_id}/cancel`

Cancellation records durable intent. A successful cancel request does not falsely assert the parser is already stopped; terminal `cancelled` requires fenced worker acknowledgement/safe interruption/cleanup or a recovery path that invalidates stale publication authority.

### Replay quarantined job

Conceptual operation: `POST /parse-jobs/{parse_job_id}/replay`

Requires explicit authorized action and creates a new immutable attempt under bounded policy. Historical failed attempts remain evidence and are not rewritten as success.

### Read result

Conceptual operation: `GET /parse-jobs/{parse_job_id}/result`

Available only for an authorized succeeded job. The result binds exact source, parser/runtime, options/config, dependency/release and NewsDOM schema/provenance digests as defined by the accepted data model.

## 7. Idempotency/retry semantics

Current synchronous `/parse` does not claim durable idempotency or automatic retry.

Future durable jobs:

- deduplicate equivalent submissions using the server-owned scoped identity;
- preserve immutable attempt numbers;
- allow automatic retry only for closed transient failure classes and a bounded count/backoff/deadline;
- quarantine permanent or exhausted failures;
- use worker fencing so stale attempts cannot publish over newer attempts;
- never use HTTP 5xx alone as sufficient proof that a retry is safe without persisted/re-observed state.

## 8. Error privacy and diagnostic boundary

External API errors are bounded and safe for untrusted callers. They do not include:

- raw PDF/extracted text;
- temp paths;
- full subprocess argv/internal stack trace;
- bearer/API credentials;
- provider/parser raw output;
- other-tenant object identities.

Approved operator diagnostics may retain additional evidence under purpose-bound authorization and retention, but the presence of an operator channel never expands the public error schema.

## 9. OpenAPI contract tests

Tests should verify:

- documented endpoints and public models appear as intended;
- examples/descriptions required for developer-facing fields remain present;
- active/future endpoint prose is not emitted into generated OpenAPI until implemented;
- public error/security metadata stays synchronized with source;
- `/health` is never described as parser readiness before the implementing source contract exists.

## 10. Change control

Any new public endpoint/event, persistent job identity, breaking schema change, authentication/readiness meaning, retry/idempotency/cancellation/replay semantic, or new tenant authority requires synchronized PRD/TRD/Architecture/UML/ERD/Threat/Test/Operability/Traceability/ADR updates and exact-head tests/security/review before promotion.