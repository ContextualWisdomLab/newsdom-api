# GitHub Actions ownership consolidation

## Scope

This audit compares `newsdom-api` `develop` at
`e06b1f3fb10903569124af011da213951e6e2473` with the central required-workflow
source at `ContextualWisdomLab/.github` main
`769691526f8c73cf714de8fe8ba51ae6cfa2901a`. Product code is outside scope.

## Ownership decision

The organization ruleset injects these seven required workflows from the
central repository:

- `codeql-pr.yml`
- `noema-review.yml`
- `opencode-review.yml`
- `pr-review-merge-scheduler.yml`
- `security-scan.yml`
- `strix.yml`
- `sast-semgrep.yml`

`security-scan.yml` already owns PR dependency review and Scorecard work.
Accordingly, the local CodeQL and Scorecard PR triggers are removed while their
default-branch and scheduled backstops remain. The local dependency-review and
duplicate quality-gate workflows are removed. The remaining `tests` workflow
preserves the stricter all-extras install and the same 100% branch-coverage
command, so no product test is dropped.

Repository-local workflow files fall from 10 to 8. An ordinary source-code PR
falls from seven local workflow runs to three: tests, ClusterFuzzLite, and the
container build. Documentation-only PRs run only tests locally. ClusterFuzzLite
and container builds ignore documentation-only changes.

PR validation workflows use a fixed workflow-name, repository, and PR-number
group and cancel only an older run for the same PR. Image, Pages, and release
workflows serialize by repository and PR or ref with cancellation disabled.
There were no local sleep or queue-sweep steps to retain or remove.

The repository ruleset keeps strict required checks and the `pytest` GitHub
Actions context. The four deleted local contexts are replaced by the central
required-workflow ruleset rather than being bypassed by local copies.
