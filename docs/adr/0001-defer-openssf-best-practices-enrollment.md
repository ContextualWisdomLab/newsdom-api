# ADR-0001: Defer OpenSSF Best Practices Enrollment

## Status

Accepted

## Context

The repository `newsdom-api` has completed its initial governance-phase OpenSSF Scorecard remediation up through release `v0.2.0`. The current Scorecard API reports a score of **7.7**. 

The remaining gaps are:
1. `Branch-Protection = 4`: The single-maintainer exception requires `develop` and `main` to have 0 required approvers to avoid a merge deadlock.
2. `Code-Review = 6`: This score represents the historical reviewed-changeset ratio and will naturally improve as human-reviewed PRs accumulate over time.
3. `CII-Best-Practices = 0`: The repository is not enrolled in the OpenSSF Best Practices program (bestpractices.dev).
4. `Maintained = 0`: The repository is currently younger than 90 days; this will only improve with time and history.

Issue #31 tracks these remaining gaps. Addressing `CII-Best-Practices` requires an active enrollment process that involves an external OAuth login and a sustained commitment to fulfilling the Best Practices criteria, which may be disproportionate for the current repository age, size, and single-maintainer status.

## Decision Drivers

- **Maintainer Capacity**: As a single-maintainer repository, operational overhead must be strictly prioritized.
- **Scorecard ROI**: The current score of 7.7 represents a strong baseline security posture (including Signed-Releases, Fuzzing, Dependency-Review, and CodeQL).
- **Time/History Constraints**: Several remaining gaps (`Maintained`, `Code-Review`) are purely time-bound or history-bound and cannot be forced immediately.

## Decision

We will **defer** enrollment in the OpenSSF Best Practices program (bestpractices.dev) and formally accept the current OpenSSF Scorecard gaps (`CII-Best-Practices=0`, `Branch-Protection=4`, `Maintained=0`, `Code-Review=6`).

## Rationale

The remaining Scorecard gaps are either structural limitations of a single-maintainer project (Branch-Protection approvals), require the passage of time (Maintained, Code-Review history), or impose external operational burdens (CII-Best-Practices) that do not currently provide sufficient ROI given the repository's age. Documenting this as a durable decision allows us to close the immediate governance-phase tracking without artificially forcing enrollment.

## Consequences

### Positive

- Avoids the immediate operational burden of navigating bestpractices.dev and maintaining a separate external checklist.
- Allows the maintainer to focus on functional development and OCR accuracy.
- Closes the active governance tracking (Issue #31) with a clear, documented endpoint.

### Negative

- The OpenSSF Scorecard `CII-Best-Practices` metric will remain at `0`.
- The overall Scorecard score will be capped until either time passes or the repository scales to multiple maintainers.

## Implementation Notes

- Issue #31 will be closed, citing this ADR as the durable decision.
- Re-evaluation of this decision should occur if the repository onboards additional non-author reviewers, or when it ages past the 90-day threshold.
