# ADR-0003: Authenticate before request-body cost and separate readiness from liveness

**Status:** Proposed — implemented on active PR #539, not protected `develop`  
**Date:** 2026-08-09

## Context

The expensive PDF parser must not consume multipart data, allocate temporary storage, or invoke MinerU for an unauthorized caller. Production configuration must also fail closed when required authentication material is absent. Separately, orchestration needs a traffic-readiness signal stronger than process liveness.

## Decision

If PR #539 is accepted and integrated:

- production authentication is required by default;
- a development bypass exists only under an explicit development profile;
- authorization and server-configuration safety are evaluated before multipart body consumption or parser admission;
- malformed/duplicate/oversized/non-ASCII authorization values fail as one bounded external unauthorized contract;
- missing required server configuration fails closed rather than opening the parser;
- `/health` remains liveness;
- `/ready` reports the bounded authentication/runtime prerequisites for traffic admission;
- readiness is not advertised as proof that an arbitrary customer document will parse successfully.

## Consequences

- API/OpenAPI/deployment examples and tests must preserve authentication-before-body ordering.
- Capacity admission (PR #548) must run after successful authentication and before body allocation.
- Production rollback repairs credential/configuration injection or rolls back the release; it does not silently enable the development bypass.
- This ADR remains Proposed until #539 lands on protected `develop` with exact-head required checks/review and the canonical documentation maturity is updated.
