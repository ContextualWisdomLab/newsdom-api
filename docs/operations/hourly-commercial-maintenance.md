# Hourly commercial maintenance

## Purpose

NewsDOM invokes the organization-owned pull-request maintenance control plane once per hour. The leaf repository supplies only its repository identity, `develop` integration branch, cadence, and bounded queue limits. Review parsing, exact-head selection, repair dispatch, credential separation, and OpenCode model configuration remain owned by `ContextualWisdomLab/.github`.

## Schedule and single-flight behavior

- Schedule: minute 41 of every hour.
- Maximum inspected pull requests: 50.
- Maximum repair dispatches per run: 1.
- Same-head repair retry floor: 1 hour.
- Concurrency: one active run per repository; a newer scheduler invocation cancels an older scheduler invocation before another repair can be dispatched.
- Manual mode: `workflow_dispatch` exposes `dry_run`, which reads the queue and records decisions without dispatching a worker.

The central worker uses OpenCode with the organization secret `NVIDIA_NIM_API_KEY`. The leaf workflow never receives that secret and never uses `COPILOT_GITHUB_TOKEN`. GitHub transport authorization is obtained centrally through the existing OpenCode App OIDC exchange or an explicitly declared maintenance token fallback. The read-only OpenCode and Noema review workflows are unchanged.

## Merge and safety boundaries

The hourly workflow does not merge a pull request. It only dispatches a conservative repair when the current head has actionable, file-scoped review evidence or meets the central conflict-resolution contract. A repair:

1. revalidates the live base and head SHAs;
2. accepts only same-repository heads;
3. gives OpenCode access only to the approved paths;
4. denies model shell, task, network, LSP, and external-directory access;
5. refuses a push if the head moves;
6. produces a new head that must pass all repository checks and independent review; and
7. cannot approve, publish, release, or weaken branch protection.

## MSA boundary

This workflow is a leaf adapter, not a second implementation. It pins the reusable central workflow by full commit SHA. Other CWL components can adopt the same central component while supplying their own target repository, default branch, and schedule. NewsDOM continues to operate independently as a FastAPI PDF-to-DOM service and as a naruon-compatible sidecar.

## Operational prerequisites

- The organization OpenCode GitHub App must be able to read and write the target pull-request head.
- The central `.github` repository must expose the pinned reusable workflow and worker commit.
- `NVIDIA_NIM_API_KEY` must be available to the central worker repository.
- Required checks and independent-review rules remain active.

If the central app-token exchange is unavailable and no optional maintenance token is configured, cross-repository dispatch fails closed. It does not fall back to Copilot or another inference provider.

## Verification

Before enabling the schedule on `develop`, verify:

- the caller pins exactly one 40-character central commit SHA;
- no model or Copilot credential appears in the leaf workflow;
- the workflow grants no `contents: write` or `pull-requests: write` permission;
- static contracts pass under the repository's 100% coverage gate;
- the central workflow passes its own unit, security, and independent-review gates; and
- one manual dry run records a bounded no-write queue decision.

## Rollback

Delete or disable `.github/workflows/hourly-commercial-maintenance.yml`. This does not affect application runtime, existing review workflows, branch protection, or manually initiated maintenance. Revert only the leaf adapter; the central component can remain available to other repositories.
