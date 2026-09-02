# Product and technical gap baseline

This document records gaps that are observable from the current NewsDOM code, delivery policy, releases, and open integration work. It is not a roadmap commitment; a gap leaves this list only after the corresponding code and evidence are current on the protected integration path.

## Product boundary

NewsDOM API owns the PDF-to-canonical-NewsDOM parsing boundary around MinerU. It accepts an authenticated PDF, validates and bounds the upload, invokes the local MinerU runtime, and returns the repository's NewsDOM response schema. Authentication, parsing and readiness truth stay in this service; consumers such as Naruon use the released API contract rather than source-copying NewsDOM internals.

The latest immutable GitHub release observed while updating this baseline is `v0.2.0` (published 2026-04-24). `CHANGELOG.md` currently describes an unreleased `0.3.0` migration in which parser authentication becomes default-required.

## Current gaps

| Gap | Current evidence | Acceptance |
| --- | --- | --- |
| Interactive API documentation security and behavior | PR #775 repairs unconditional Swagger authorization persistence and the CSP that blocked Swagger execution. The current repair makes persistence development-only, disables the external Swagger validator, and keeps the non-doc CSP locked down. Repository policy still requires a live localhost `/docs` and `/redoc` smoke for documentation changes. | Current-head unit/coverage/docs gates pass; a real browser/local smoke proves `/docs` and `/redoc` render without CSP errors; a refresh in development preserves Swagger authorization while production does not persist it; screenshots or equivalent browser evidence correspond to the exact tested head. |
| `0.3.0` release readiness | The changelog still uses an unreleased image placeholder for the authentication migration. The last immutable release is `v0.2.0`. | Protected `develop` evidence is GREEN; package, OpenAPI, container image, SBOM/provenance, rollback instructions and release manifest identify the same version and source; the release tag is immutable and reproducible. |
| Runtime configuration boundary | `AGENTS.md` records `NEWSDOM_MINERU_BIN` as the remaining raw-environment deployment knob and requires future secrets/credentials/external endpoints to use the canonical KV/credential-registry pattern. | The executable-path override has an explicit deployment/configuration ADR or is moved behind the adopted configuration boundary; no new runtime secret is read directly from process environment. |
| Real-data parser acceptance | Synthetic fixtures remain suitable for unit tests, but commercial parsing acceptance requires right-cleared representative PDFs and must not publish private/copyrighted inputs. | A private/right-cleared acceptance corpus exercises representative layouts, languages, page counts and failure cases; results are reproducible and published only as non-sensitive metrics/evidence, not source documents. |

## Current PR #775 traceability

The repair sequence on branch `jules-11760207665579123715-6bc329bb` is test-first:

- RED regression: `31bf14cd6d71e03b0b31320c940c3b79f3d984ca`
- causal implementation: `6c4a5846761e4c1eee2d968c690589811de875a7`
- corrected CSP test oracle: `623b14fc62262fddb8e0d810e72317908cf76ae5`
- documentation alignment: `bbaed060f1243dc30653c40b2e66c9d93df46474`

At that exact head, GitHub-hosted Ubuntu verification is not yet terminal: the repository `tests` job remains queued without an assigned runner and the central CodeQL PR workflow ended in `startup_failure`. Those states are incomplete evidence, not passing gates and not a reason for source churn.
