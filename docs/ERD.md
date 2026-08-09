# NewsDOM API Logical and Persistence ERD

**Status:** Accepted logical baseline. Protected `develop` owns no durable application database.  
**Last reviewed:** 2026-08-09

## Current persistence truth

The protected synchronous service writes a PDF and parser outputs into a private temporary workspace for one request, returns typed NewsDOM JSON, and cleans the workspace. It does **not** own durable parse-job, tenant, audit, or artifact database tables. Host products may persist returned data under their own authority.

```mermaid
erDiagram
    PARSE_REQUEST ||--|| SOURCE_DOCUMENT : carries
    PARSE_REQUEST ||--o| TEMP_WORKSPACE : allocates
    TEMP_WORKSPACE ||--o{ PARSER_ARTIFACT : holds
    PARSER_ARTIFACT }o--|| NEWSDOM_DOCUMENT : normalizes_to

    PARSE_REQUEST {
      string request_scope
      string parse_options
    }
    SOURCE_DOCUMENT {
      string content_sha256
      bigint size_bytes
      string media_type
    }
    TEMP_WORKSPACE {
      string request_local_path
      string lifecycle_state
    }
    PARSER_ARTIFACT {
      string artifact_kind
      bigint artifact_size_bytes
    }
    NEWSDOM_DOCUMENT {
      string schema_version
      string result_digest
    }
```

These are conceptual current-runtime entities, not tables.

## Accepted-target durable job model — not implemented

```mermaid
erDiagram
    TENANT_RECORD ||--o{ PARSE_JOB : owns
    SOURCE_ARTIFACT ||--o{ PARSE_JOB : input_to
    PARSE_JOB ||--o{ PARSE_ATTEMPT : has
    PARSE_JOB ||--o{ PARSE_RESULT : yields
    PARSE_JOB ||--o{ JOB_AUDIT_EVENT : records
    PARSE_ATTEMPT ||--o{ PARSER_ARTIFACT : produces
    PARSE_RESULT ||--o{ RESULT_ARTIFACT : references
    REPRODUCIBILITY_MANIFEST ||--o{ PARSE_ATTEMPT : binds
    REPRODUCIBILITY_MANIFEST ||--o{ PARSE_RESULT : governs

    TENANT_RECORD {
      uuid tenant_record_id PK
      text tenant_status_code
      timestamptz created_at
    }

    SOURCE_ARTIFACT {
      uuid source_artifact_id PK
      uuid tenant_record_id FK
      text content_sha256
      bigint source_size_bytes
      text protected_object_ref
      timestamptz created_at
    }

    PARSE_JOB {
      uuid parse_job_id PK
      uuid tenant_record_id FK
      uuid source_artifact_id FK
      text idempotency_scope_hash
      text parse_option_hash
      text job_state_code
      integer attempt_count
      timestamptz accepted_at
      timestamptz updated_at
    }

    PARSE_ATTEMPT {
      uuid parse_attempt_id PK
      uuid parse_job_id FK
      uuid reproducibility_manifest_id FK
      text worker_lease_token
      integer attempt_number
      text attempt_state_code
      text failure_class_code
      timestamptz lease_expires_at
      timestamptz started_at
      timestamptz finished_at
    }

    PARSER_ARTIFACT {
      uuid parser_artifact_id PK
      uuid parse_attempt_id FK
      text artifact_kind_code
      text artifact_sha256
      bigint artifact_size_bytes
      text protected_object_ref
    }

    PARSE_RESULT {
      uuid parse_result_id PK
      uuid parse_job_id FK
      uuid reproducibility_manifest_id FK
      text newsdom_schema_version
      text result_sha256
      text result_status_code
      timestamptz completed_at
    }

    RESULT_ARTIFACT {
      uuid result_artifact_id PK
      uuid parse_result_id FK
      text artifact_kind_code
      text artifact_sha256
      text protected_object_ref
    }

    REPRODUCIBILITY_MANIFEST {
      uuid reproducibility_manifest_id PK
      text manifest_sha256 UK
      text parser_runtime_identity
      text parser_runtime_version
      text api_release_identity
      text dependency_lock_sha256
      text configuration_sha256
      text newsdom_schema_version
      text source_commit_sha
      timestamptz created_at
    }

    JOB_AUDIT_EVENT {
      uuid job_audit_event_id PK
      uuid parse_job_id FK
      uuid actor_identity_id
      text action_code
      text outcome_code
      text bounded_evidence_digest
      timestamptz occurred_at
    }
```

## Naming and identity invariants

Owned persistent objects use descriptive two-or-more-word `snake_case`. Public/job IDs are opaque UUIDs, never sequential authorization tokens.

Logical uniqueness for the target includes:

- `(tenant_record_id, idempotency_scope_hash)` for one accepted logical submission scope;
- `(parse_job_id, attempt_number)` for attempt ordering;
- immutable digest identity for source/parser/result artifacts;
- a partial unique constraint on `(parse_job_id, reproducibility_manifest_id)`
  where `result_status_code = 'succeeded'`, allowing at most one immutable
  successful result per exact accepted job contract; a versioned reparse uses
  a new manifest/contract identity and explicit successor relationship.

`idempotency_scope_hash` binds principal/tenant, caller idempotency key, source
digest, parse options, public API/schema version, and parser runtime/model
contract identity and version. It is not derived from source digest alone
because the same source may be intentionally parsed under different options or
contract versions.

## Job-state invariant

Target job-state transitions are closed and forward-governed. `succeeded`, `cancelled`, and `quarantined` are terminal for one attempt lifecycle; replay creates a new attempt under explicit policy rather than mutating historical attempt evidence into success.

## Lease/fencing invariant

A durable worker attempt may publish state/result only while holding the current fencing/lease authority for the job. Expired/stale workers cannot overwrite a later attempt's result. Process-local semaphores from PR #548 are not a substitute for this durable target.

## Artifact and provenance invariant

A parse result binds:

- exact source digest;
- exact parser runtime identity/version;
- NewsDOM schema version;
- parse-option/configuration digest;
- dependency lock and producing release/commit identity;
- result digest and protected artifact reference.

Audit events are bounded operational evidence and do not replace the reproducibility manifest.

## Tenant/privacy invariant

All durable source/result/artifact records are tenant-scoped and require purpose-bound authorization. General logs/metrics store bounded digests/classifications rather than raw PDF/extracted text. Deletion/retention must cover source and derived protected artifacts without rewriting immutable audit facts falsely.

## Migration acceptance

This target becomes physical only with reviewed migrations/rollback, indexes/constraints, tenant/RLS or equivalent authorization, idempotency/concurrency/lease tests, cancellation/replay, backup/restore, retention/deletion, artifact-store recovery, and exact-head security/coverage evidence. Until then this is conceptual/accepted-target, not a protected-branch database claim.
