# Doctoring record: bounded PDF upload transport

**Observed gap:** The live NewsDOM sidecar accepted only 20 MiB while the
Naruon direct PDF DOM contract allowed 64 MiB, so equivalent customer workflows
were inconsistent.

**Correction:** `MAX_PARSE_UPLOAD_BYTES` and its boundary tests now use 64 MiB.
Authentication remains checked before multipart parsing, and streaming input
still fails closed at the first byte over the bound.

**Evidence:** `tests/test_parse_endpoint.py` covers the 64 MiB contract and the
unknown-size streaming over-limit path. Full coverage and exact-head hosted
checks remain required before merge.

**References (APA 7th):**

- Internet Engineering Task Force. (2022). *HTTP semantics (RFC 9110).* RFC
  Editor. https://www.rfc-editor.org/rfc/rfc9110
- National Institute of Standards and Technology. (2025). *Secure software
  development framework (SSDF) version 1.2* (NIST Special Publication 800-218
  Rev. 1, Initial Public Draft). https://doi.org/10.6028/NIST.SP.800-218r1.ipd
