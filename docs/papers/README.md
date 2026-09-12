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
untrusted-input boundaries in this service (isolated PDF structural
validation, the MinerU DOM normalizer, the `ParseResponse` validator, and
the equivalence metrics normalizer) are worth continuous fuzzing rather
than example-based tests alone.

## Extract Me If You Can: Abusing PDF Parsers in Malware Detectors

- Authors: Curtis Carmony, Xunchao Hu, Heng Yin, Abhishek Vasisht
  Bhaskar, Mu Zhang
- Source: NDSS 2016, https://doi.org/10.14722/ndss.2016.23483
- Open access PDF:
  <https://www.ndss-symposium.org/wp-content/uploads/2017/09/extract-me-if-you-can-abusing-pdf-parsers-malware-detectors.pdf>

Carmony et al. (2016) show that PDF parsers disagree on malformed
objects and that those disagreements are exploitable. NewsDOM therefore
opens untrusted PDFs only inside a disposable, resource-limited child
and never on the API event loop. The NDSS license allows noncommercial
reproduction only, so the PDF is cited and linked rather than vendored
here. Full APA 7th citations live in
`docs/doctoring/isolated-pdf-structure-validation.md`.
