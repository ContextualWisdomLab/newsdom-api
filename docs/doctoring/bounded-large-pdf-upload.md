# Doctoring record: bounded large PDF upload alignment

**Observed gap:** Naruon's signed email-import transport accepted PDFs up to
64 MiB while NewsDOM `/parse` rejected requests above 20 MiB before deferred DOM
recognition.

**Correction:** NewsDOM now uses a 64 MiB bounded upload budget. Authentication,
PDF signature validation, chunk-by-chunk accounting, temporary-file cleanup,
parser timeout, and the `413 Payload Too Large` response remain unchanged.

**Evidence:** `tests/test_parse_endpoint.py` proves the exact configured budget
and the first over-limit byte with a monkeypatched 64-byte fixture; the complete
suite passes with statement and branch coverage at 100%.

**References (APA 7th):**

- Internet Engineering Task Force. (2022). *HTTP semantics (RFC 9110).* RFC
  Editor. https://www.rfc-editor.org/rfc/rfc9110
  The standard supports the retained `413` contract for an explicitly bounded
  request body.
- National Institute of Standards and Technology. (2025). *Secure software
  development framework (SSDF) version 1.2* (NIST SP 800-218 Rev. 1, Initial
  Public Draft). https://doi.org/10.6028/NIST.SP.800-218r1.ipd
  The framework supports regression evidence and operational controls around
  untrusted-input boundary changes.

No private PDF or customer document was used; no source PDF is redistributed.
