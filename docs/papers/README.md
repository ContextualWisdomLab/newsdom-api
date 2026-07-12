# Reference papers

Background reading for the fuzzing harnesses under `fuzzers/`.

## The Art, Science, and Engineering of Fuzzing: A Survey

- File: `fuzzing-survey-arxiv-1812.00140.pdf`
- Authors: Valentin J. M. Manès, HyungSeok Han, Choongwoo Han, Sang Kil Cha,
  Manuel Egele, Edward J. Schwartz, Maverick Woo
- Source: arXiv:1812.00140 (open access, <https://arxiv.org/abs/1812.00140>)

A survey of coverage-guided and mutation-based fuzzing that frames the model
our targets follow: feed a program arbitrary input, drive it with coverage
feedback, and treat any unhandled crash as a finding. It motivates why the
untrusted-input boundaries in this service (the MinerU DOM normalizer, the
`ParseResponse` validator, and the equivalence metrics normalizer) are worth
continuous fuzzing rather than example-based tests alone.
