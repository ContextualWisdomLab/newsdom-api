# ADR-0002: Keep MinerU external and keep liveness weaker than parser readiness

**Status:** Accepted  
**Date:** 2026-08-09

## Context

NewsDOM's default API image does not bundle the MinerU runtime. A FastAPI process can therefore be alive while `/parse` cannot execute successfully. Folding parser availability into ordinary process liveness would make orchestrators restart a healthy API process for an external runtime/configuration problem, while treating liveness as readiness would route traffic to an unusable parser.

## Decision

- MinerU remains an explicitly configured external runtime boundary rather than an invisible assumption of the default API image.
- `/health` means process liveness only.
- Parser/runtime availability is a stronger readiness/acceptance condition and must never be inferred from `/health` alone.
- Parser execution success remains stronger than readiness and requires an actual bounded parse contract to complete.
- Public failures distinguish runtime unavailable from incomplete parser output without leaking internal paths or raw parser diagnostics.

## Consequences

- Deployment documentation must state how MinerU is provisioned/configured.
- The default API image may be healthy without being parser-ready; that is truthful, not a defect in `/health`.
- PR #539 can add `/ready` without changing the liveness meaning.
- Operators require a controlled representative parse smoke before declaring full product acceptance.
- Any future decision to bundle/parser-manage MinerU inside the image requires a superseding ADR and supply-chain/runtime-size/licensing/upgrade analysis.
