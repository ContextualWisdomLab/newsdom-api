# Isolated PDF structural validation

## Buyer next action

If `/parse` returns `415 Unsupported Media Type`, re-export the file as
a standard PDF 1.x or PDF 2.0 document and retry. If it returns `503
Service Unavailable` after authentication succeeded, ask the operator
to confirm Linux `RLIMIT_CPU` / `RLIMIT_AS` support and to inspect the
`newsdom_api` validator log; do not retry a hanging upload in a tight
loop.

## Decision

NewsDOM treats structural PDF validation as an untrusted-parser
boundary. The parent FastAPI worker copies at most 20 MiB to a
temporary file, then starts a disposable child that applies CPU and
address-space limits before `pypdf.PdfReader(..., strict=True)`. The
parent enforces a 5-second wall-clock timeout and kills the child.
The child prints one JSON object `{"outcome":"..."}` and never echoes
paths, exception text, or uploaded bytes.

This is a leaf-service control. A naruon gateway may add tenant
fairness or a job queue, but bypassing the gateway must not restore
unbounded in-process parsing.

## Failure mapping

| Outcome | Caller response | Operator action |
| --- | --- | --- |
| `valid` | Continue to MinerU | None |
| `invalid_document` | `415 Unsupported Media Type` | Ask the client to re-export the PDF |
| timeout / killed child | `415 Unsupported Media Type` | Treat as a pathological PDF; do not raise worker concurrency |
| spawn or missing `setrlimit` | `503 Service Unavailable` | Restore the previous image or move the replica to a Linux host with POSIX resource limits |

## Limits

- wall clock: 5 seconds
- CPU: 5 seconds (`RLIMIT_CPU`)
- address space: 512 MiB (`RLIMIT_AS`)
- upload size: 20 MiB (unchanged outer defense)

Rollback is an image revert. There is no environment flag that
re-enables in-process `PdfReader` on the event loop.

## Standards and research

Parser confusion and resource expansion are first-class PDF risks, not
edge cases. Carmony et al. (2016) show that PDF parsers disagree on
malformed objects and that those disagreements are exploitable.
Manès et al. (2021) frame untrusted parsers as continuous fuzzing
targets; this repository already keeps that survey under
`docs/papers/`. ISO 32000-2 (2020) is the current PDF file-format
standard. OWASP API4:2023 requires an explicit resource budget for
expensive operations. POSIX `setrlimit` is the production-supported
Linux enforcement point used here.

The NDSS 2016 paper grants noncommercial reproduction only. This
repository therefore cites and links it rather than vendoring the PDF
into a commercial product tree.

## References

Carmony, C., Hu, X., Yin, H., Bhaskar, A. V., & Zhang, M. (2016).
Extract me if you can: Abusing PDF parsers in malware detectors. In
*Proceedings of the 23rd Annual Network and Distributed System
Security Symposium (NDSS 2016)*. Internet Society.
https://doi.org/10.14722/ndss.2016.23483

International Organization for Standardization. (2020). *Document
management — Portable document format — Part 2: PDF 2.0* (ISO
Standard No. 32000-2:2020). https://www.iso.org/standard/75839.html

Manès, V. J. M., Han, H., Han, C., Cha, S. K., Egele, M., Schwartz,
E. J., & Woo, M. (2021). The art, science, and engineering of
fuzzing: A survey. *IEEE Transactions on Software Engineering,
47*(11), 2312–2331. https://doi.org/10.1109/TSE.2019.2946563

Open Worldwide Application Security Project. (2023). *API4:2023
unrestricted resource consumption*. In *OWASP API security top 10
2023*.
https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/

The Open Group. (2018). *setrlimit — set resource limits* (IEEE Std
1003.1-2017).
https://pubs.opengroup.org/onlinepubs/9699919799/functions/setrlimit.html

Tiangolo, S. (n.d.). *Concurrency and async / await*. FastAPI.
https://fastapi.tiangolo.com/async/
