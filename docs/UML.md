# NewsDOM API UML and Runtime Views

**Status:** Accepted documentation baseline; active-PR and accepted-target boundaries are labelled.  
**Last reviewed:** 2026-08-09

## Protected-develop component view

```mermaid
flowchart LR
    HOST[API client / host]
    API[FastAPI main]
    SERVICE[parse service]
    RUNNER[MinerU runner]
    MINERU[external MinerU CLI]
    BUILDER[DOM builder]
    SCHEMA[NewsDOM schemas]
    TMP[(ephemeral temp workspace)]

    HOST --> API
    API --> SERVICE
    SERVICE --> TMP
    SERVICE --> RUNNER
    RUNNER --> MINERU
    MINERU --> TMP
    SERVICE --> BUILDER
    BUILDER --> SCHEMA
    SCHEMA --> API
```

## Current synchronous parse sequence

```mermaid
sequenceDiagram
    actor Client
    participant API
    participant Service
    participant Temp as Temp workspace
    participant Runner as MinerU runner
    participant MinerU
    participant Builder as DOM builder

    Client->>API: POST /parse PDF
    API->>Service: bounded parse request
    Service->>Temp: create private workspace / write input
    Service->>Runner: execute configured parser
    Runner->>MinerU: bounded argv/subprocess
    MinerU-->>Runner: output artifacts / failure
    Runner-->>Service: validated collected artifacts
    Service->>Builder: normalize content_list + page metadata
    Builder-->>Service: typed NewsDOM
    Service->>Temp: cleanup
    Service-->>API: result
    API-->>Client: typed JSON / sanitized error
```

## Liveness/readiness view

```mermaid
flowchart TB
    PROCESS[FastAPI process]
    HEALTH[/health — protected-develop liveness]
    AUTH[required auth configuration — PR #539]
    EXEC[MinerU executable — PR #539 readiness input]
    READY[/ready — PR #539 active-PR]
    FULL[full customer-document parse]

    PROCESS --> HEALTH
    AUTH -. active-PR .-> READY
    EXEC -. active-PR .-> READY
    READY -. prerequisite, not proof .-> FULL
```

`/health` must not be documented as proof that parse traffic is usable.

## Authentication + admission sequence — active PRs

```mermaid
sequenceDiagram
    actor Client
    participant API
    participant Auth as Auth middleware (#539)
    participant Limit as App-local admission (#548)
    participant Body as Multipart/body
    participant Parser

    Client->>API: /parse
    API->>Auth: validate server config + authorization
    alt unauthorized / unsafe config
        Auth-->>Client: fixed 401/503 before body read
    else authenticated
        Auth->>Limit: non-waiting lease
        alt saturated
            Limit-->>Client: 429 + Retry-After before body read
        else lease acquired
            Limit->>Body: consume bounded input
            Body->>Parser: parse
            Parser-->>Limit: result/failure/cancel
            Limit->>Limit: release exactly once
        end
    end
```

This sequence becomes as-built only as its implementing PRs land in dependency order.

## Durable job state machine — accepted target, not implemented

```mermaid
stateDiagram-v2
    [*] --> accepted
    accepted --> queued
    queued --> running: fenced worker lease
    queued --> cancel_requested
    running --> cancel_requested
    running --> succeeded
    running --> failed_transient
    running --> failed_permanent
    failed_transient --> queued: bounded retry
    failed_transient --> quarantined: retry budget exhausted
    failed_permanent --> quarantined
    cancel_requested --> cancelled: safe interruption/cleanup
    succeeded --> [*]
    cancelled --> [*]
    quarantined --> replay_requested: explicit operator action
    replay_requested --> queued
```

No current synchronous request is a durable job merely because this target is documented.

## Durable job authority view — accepted target

```mermaid
flowchart LR
    CALLER[Authenticated principal/tenant]
    INTAKE[Job intake + idempotency]
    STORE[(NewsDOM-owned job/evidence store)]
    QUEUE[Durable bounded queue]
    WORKER[Fenced parser worker]
    ART[(Protected artifact store)]
    HOST[Consuming application]

    CALLER --> INTAKE
    INTAKE --> STORE
    INTAKE --> QUEUE
    QUEUE --> WORKER
    WORKER --> ART
    WORKER --> STORE
    STORE --> HOST
    ART --> HOST
```

NewsDOM-owned durable state, if introduced, remains behind a versioned API; the service never reaches into a consuming product's private database.

## Failure classes

```mermaid
stateDiagram-v2
    [*] --> request
    request --> rejected_4xx: invalid/unsupported input
    request --> parser_unavailable_503: runtime not available
    request --> parser_contract_502: required parser output absent/invalid
    request --> saturated_429: active-PR admission full
    request --> success: parse+normalization complete
    request --> internal_5xx: unexpected defect
```

## Deployment view

```mermaid
flowchart TB
    subgraph leaf[Standalone NewsDOM sidecar]
        API[NewsDOM API container]
        PARSER[MinerU runtime provisioned separately]
        API --> PARSER
    end

    subgraph host[Optional host]
        NARUON[naruon / another product]
        IDP[host identity/tenancy]
        STATE[(host product state)]
        NARUON --> IDP
        NARUON --> STATE
        NARUON --> API
    end
```

The host can add stronger policy and workflow but does not erase the leaf parser's own resource/input/runtime boundary.

## Maintenance rule

Update these views whenever authentication/readiness, parser execution, public schema, persistence, job state, tenant authority, retry/cancellation, or deployment ownership changes. `active-PR` and `accepted-target` views must not be relabelled as protected-branch behavior before integration and exact-head evidence.
