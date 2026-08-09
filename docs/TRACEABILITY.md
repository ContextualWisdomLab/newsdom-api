# NewsDOM API Requirements and Evidence Traceability

**Status:** Accepted documentation baseline  
**Last reviewed:** 2026-08-09

| Requirement / decision | Canonical basis | Source/evidence boundary | Maturity |
|---|---|---|---|
| PDF → typed NewsDOM sidecar | PRD/TRD/Architecture | `main.py`, `service.py`, `mineru_runner.py`, `dom_builder.py`, schemas/tests | implemented-develop |
| default API image does not silently bundle MinerU | Architecture; deploy runbook | container/runtime docs and smoke | implemented-develop |
| `/health` is process liveness, not parser readiness | PRD/TRD/ADR-0002 | current API + deploy docs | implemented-develop |
| fail-closed production auth before body allocation | PR #539; ADR-0003 | auth/readiness tests + exact-head evidence | active-PR |
| `/ready` combines auth/runtime prerequisites | PR #539; ADR-0003 | readiness/OpenAPI/deploy tests | active-PR |
| non-waiting process-local parser admission | PR #548; ADR-0004 | concurrent ASGI/body-not-read/lease tests | active-PR-stacked |
| pypdf known-vulnerability floor at 6.15.0 | PR #575 | dependency metadata/lock/CVE regression/security docs | active-PR |
| durable async parse lifecycle | PRD/TRD/ADR-0005 | no protected source yet | accepted-target |
| principal/tenant-scoped idempotency and fenced workers | ERD/ADR-0005 | no protected source yet | accepted-target |
| tenant quota/audit/retention | PRD/ERD/Threat/Operability | no NewsDOM-owned persistent control plane yet | accepted-target |
| exact 100% owned production statement/branch coverage and docstrings | engineering acceptance/PRD/Test Strategy | repository CI and local full-suite evidence | implemented-develop |
| representative extraction-fidelity benchmark | PRD/Test Strategy | synthetic fixtures exist; full representative corpus gate remains | partial |
| supply-chain SBOM/provenance/release manifest | deploy/release docs/workflows | release workflows/artifacts | implemented-develop |
| Naruon integration through API/sidecar, not private DB | PRD/TRD/UML | README/host boundary | implemented-architecture |

## Maturity vocabulary

- `implemented-develop`: source and representative contract tests exist on protected integration branch; release readiness still requires exact release-head gates.
- `implemented-architecture`: an existing integration/ownership boundary is established without implying every downstream product path is deployed.
- `active-PR`: implementation exists only on an open PR.
- `active-PR-stacked`: implementation is active and depends on an earlier PR/base contract; predecessor evidence does not transfer after refresh.
- `accepted-target`: approved product/technical target without protected implementation.
- `partial`: some evidence exists, but the complete commercial claim is not yet justified.

## Promotion rules

A row moves to `implemented-develop` only when the implementing exact head is integrated into protected `develop` and current required checks/security/review evidence supports the claim. A feature PR, architecture diagram, local predecessor run, queued check, or PR-body assertion cannot promote maturity.

A row moves from `implemented-develop` to a release claim only after the integrated release head passes package/container/security/provenance/compatibility/operational acceptance and release artifacts are verified.

## Standards and primary technical evidence

Material protocol/security/HTTP/deployment decisions should continue to record authoritative RFCs, OWASP/NIST/official framework/runtime documentation, and primary benchmark methodology in the existing `docs/doctoring/`, `docs/operations/`, and plan records. This matrix points to product decisions and source evidence rather than duplicating full bibliographic entries.

## Conversation-derived backlog captured here

The current durable product conversation requires the repository to preserve the distinction between liveness and dependency readiness, then advance bounded parser admission, durable asynchronous jobs, idempotency/replay/dead-letter behavior, tenant-scoped authorization/audit, OpenTelemetry-style observability, representative accuracy/fidelity benchmarks, schema/version compatibility, reproducible SBOM/provenance, and truthful release evidence. These items remain `active-PR`, `accepted-target`, or `partial` until their source/evidence exists; this document must not promote them by prose alone.

## Change rule

Every material runtime/security/data/operability PR should update the affected row(s), ADR if the authority/contract changes, and representative tests. Superseded decisions remain historically discoverable rather than silently disappearing.