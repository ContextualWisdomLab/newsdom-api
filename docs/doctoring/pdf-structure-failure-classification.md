# PDF structure failure classification

## Decision

The `/parse` boundary distinguishes malformed representation failures from unexpected server defects. During structural inspection, `PdfReadError`, `RecursionError`, `ValueError`, `OverflowError`, `TypeError`, and the existing bounded-upload `MemoryError` compatibility case are converted to the existing sanitized `415 Unsupported Media Type` response. Other exceptions, including `RuntimeError`, are not caught by `_validate_pdf_structure`; they remain server failures so monitoring is not blinded by a false client-error classification.

This is an exception-classification control, not a complete denial-of-service control. The 20 MiB streamed upload limit, parser admission control, subprocess timeout, deployment resource limits, and stronger process isolation remain the resource-exhaustion controls. A `MemoryError` mapped at this legacy compatibility boundary must therefore not be interpreted as evidence that host memory pressure has been contained.

## HTTP semantics

RFC 9110 defines 415 for content whose format is unsupported by the target method, including a format problem discovered by inspecting the representation data. That supports a 415 response for malformed PDF structure detected during direct representation inspection. Unexpected implementation or integration failures are not representation-format evidence and therefore must not be relabeled as 415.

## Security and observability

CWE-400 describes uncontrolled resource consumption as an availability risk and recommends architectural limits and safe failure behavior. MITRE also cautions that CWE-400 is a high-level class and should not be used as a precise vulnerability mapping when a more specific weakness exists. This document therefore uses CWE-400 only as resource-exhaustion context, not as the vulnerability identifier for every parser failure.

Operator-visible parser-class failures retain the fixed `Failed to parse PDF structure` error event without exposing parser exception text or filesystem paths to the HTTP client. Unexpected server exceptions continue through the service's existing sanitized 500-class boundary and observability path.

## Verification contract

The exact-head regression suite must prove that a malformed `PdfReadError` remains 415, the compatibility resource-error case stays sanitized according to the current product contract, and an injected `RuntimeError` escapes `_validate_pdf_structure` instead of being converted to 415. Any future expansion of the caught exception tuple requires a focused RED→GREEN regression and an explicit classification rationale here.

## Rollback

If the narrow exception tuple causes a supported malformed PDF to escape as a server error, add only the evidence-backed parser exception class after reproducing it with a bounded fixture. Do not restore `except Exception`, and do not weaken upload/admission/process resource controls.

## References

Fielding, R., Nottingham, M., & Reschke, J. (2022). *HTTP semantics* (RFC 9110). Internet Engineering Task Force. https://doi.org/10.17487/RFC9110

The MITRE Corporation. (2026). *CWE-400: Uncontrolled resource consumption* (CWE Version 4.20). Common Weakness Enumeration. https://cwe.mitre.org/data/definitions/400.html
