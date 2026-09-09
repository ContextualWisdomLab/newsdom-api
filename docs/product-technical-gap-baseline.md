# Product–Technical Gap Baseline

This document records verified product/technical gaps against the live `newsdom-api` code. Completion requires evidence from the exact PR head; historical GREEN results are not transferred across source changes.

## Parser authentication boundary

### Current contract

`/parse` authentication must fail closed before multipart/body parsing. A configured production service accepts one exact Bearer credential and returns the existing fixed unauthorized response for missing, malformed, duplicated, oversized, non-ASCII, or incorrect credentials. Runtime authentication settings remain immutable after application creation.

### Timing-hardening gap

Python documents `hmac.compare_digest()` as preferable for secret comparisons, while noting that differing lengths or types can theoretically reveal length/type information through timing. PR #836 narrows the unequal-length Bearer path so it performs an equal-length comparison over the expected-token buffer before returning the same unauthorized response.

This is treated as defense-in-depth timing hardening, not as a proven remotely exploitable vulnerability. No buyer-visible severity or risk-reduction percentage is claimed without representative timing distributions and an attack model.

### Dependency isolation

Authentication timing changes must not opportunistically regenerate unrelated dependency locks. Dependency/security upgrades belong to their own causal lane with resolver-generated lock state, compatibility tests, vulnerability evidence, rollback, and immutable release provenance. PR #836 restores `uv.lock` to the protected `develop` blob so its semantic delta remains limited to the parser authentication boundary.

### Acceptance

- unchanged exact head passes the repository's required pytest and applicable security/static checks;
- fail-closed parser tests remain GREEN;
- independent current-head review is obtained;
- no dependency lock delta remains in the authentication PR;
- any stronger constant-time or vulnerability claim requires measured evidence rather than implementation inference.
