# Hourly product-development loop

NewsDOM API uses a pull-request-first autonomous development loop. The workflow
`.github/workflows/hourly-product-development.yml` runs at minute 41 of every
hour and can also be evaluated manually with `workflow_dispatch`.

## Control flow

1. Query the repository for any open pull request.
2. Stop without creating work when a PR exists; organization-level PR
   maintenance remains responsible for review, repair, exact-head validation,
   branch updates, and policy-compliant merge.
3. Require a configured Agent Tasks credential.
4. Read the complete current Agent Tasks inventory.
5. Stop when any task is active or has an unknown state.
6. Create one bounded Copilot cloud-agent task only when the repository has no
   open PR and no active or unknown task.

This single-flight contract prevents autonomous work from accumulating behind
an unresolved review or from creating multiple competing implementations of the
same product gap.

## Authentication and API contract

The built-in `GITHUB_TOKEN` is used only for read-only pull-request inventory.
GitHub's Agent Tasks API requires a fine-grained user token or GitHub App user
access token and does not accept an installation access token such as the
workflow `GITHUB_TOKEN`. Configure `COPILOT_GITHUB_TOKEN` as a repository or
organization secret with Agent tasks read/write permission for
`ContextualWisdomLab/newsdom-api`.

The workflow sends the GitHub-recommended media type and supported REST API
version `2022-11-28`. Agent Tasks endpoints are in public preview, so their
request and response contract must remain covered by the repository workflow
tests and reviewed when GitHub changes the preview.

When the secret is absent, task inventory is unavailable, or the API returns an
unexpected state, the workflow fails closed and records the reason in the step
summary. It never assumes that missing evidence means the queue is empty.

## Agent task contract

Each task must:

- inspect the repository, issues, recent merged PRs, documentation, and tests
  before selecting work;
- choose the single highest-value buyer-visible product or reliability gap that
  fits one reviewable increment;
- work test-first and retain 100% production statement and branch coverage plus
  complete production docstrings;
- preserve NewsDOM API as both a standalone service and a modular sidecar for
  CWL MSA deployments and naruon;
- update `CHANGELOG.md` and all affected user, operator, API, architecture, and
  research documentation;
- create exactly one bounded PR against `develop` with verification evidence,
  authoritative citations when relevant, and explicit residual risk;
- never merge, publish, release, or bypass protected review and security gates.

## Manual dry run

Run **Hourly Product Development** from the Actions UI with `dry_run=true` to
exercise the queue and authentication gates and print the bounded task prompt
without creating an Agent Task.

Scheduled workflows execute from the repository's default branch, so the hourly
loop becomes active only after the workflow is merged into `develop`.
