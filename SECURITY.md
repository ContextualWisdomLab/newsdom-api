# Security Policy

## Reporting a vulnerability

Please report a vulnerability privately by opening a GitHub Security
Advisory draft for this repository:

- [GitHub Security Advisory draft](https://github.com/Seongho-Bae/newsdom-api/security/advisories/new)
- [Maintainer profile](https://github.com/seonghobae)

Do not open a public issue for an unpatched vulnerability.

When reporting, include:

- affected branch or commit
- reproduction steps
- impact assessment
- any proof-of-concept input or sanitized logs needed to reproduce safely

Avoid sending secrets, production credentials, or copyrighted third-party
source documents in reports.

## Supported branches

- `develop`: actively maintained integration branch
- `main`: stable release branch

Security fixes should target the appropriate Git Flow branch and be
back-merged when required by `docs/workflow/git-flow.md`.

## Disclosure expectations

- acknowledgement target: within 7 days
- triage/update target: within 30 days when a fix is feasible
- coordinated disclosure preferred after a fix or mitigation is available

## Safe handling notes

- use synthetic fixtures whenever possible
- keep private reference inputs out of the repository
- provide sanitized evidence that preserves reproducibility without exposing
  sensitive data
