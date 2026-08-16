# Bounded parser admission

## Buyer next action

If `/parse` returns `429 Too Many Requests`, wait for the `Retry-After`
seconds and retry once. If 429s continue, add replicas or raise
`NEWSDOM_MAX_CONCURRENT_PARSES` only after measuring process RSS under
your PDF mix. Do not treat 429 as `503 Service Unavailable` and do not
open a waiting queue in front of MinerU.

## Decision

NewsDOM admits expensive `/parse` work with a process-local,
non-waiting limiter. Authentication runs first. A lease is acquired
before the multipart body is read. The default cap is one in-flight
parse per process (`NEWSDOM_MAX_CONCURRENT_PARSES=1`). Valid values are
integers from 1 through 128. Each FastAPI application owns its own
`ParseAdmissionLimiter`; two replicas do not share a counter.

The production upload chunk stays 8 KiB. Issue #534 still requires a
reviewed benchmark before any other chunk size is selected. The
reproducible command is `uv run python tools/benchmark_upload_ingestion.py`.

This is a leaf-service control. A naruon gateway may add tenant fairness
or a job queue, but bypassing the gateway must not restore unbounded
admission.

## Failure mapping

| Outcome | Caller response | Operator action |
| --- | --- | --- |
| lease acquired | Continue to upload copy and MinerU | None |
| replica saturated | `429 Too Many Requests` plus `Retry-After: 1` | Retry after one second; scale replicas if sustained |
| invalid capacity at start | Process refuses to start | Set an integer in 1..128 |

## Limits

- default concurrent parses: 1
- maximum concurrent parses: 128
- retry hint: 1 second
- upload chunk: 8192 bytes (rollback baseline)
- upload size: 20 MiB (unchanged outer defense)

Rollback is an image revert or a return to the previous integer cap.
There is no environment flag that disables admission.

## Standards and research

RFC 6585 defines `429 Too Many Requests` and the `Retry-After` signal
used here. RFC 9110 keeps that status in the current HTTP semantics.
OWASP API4:2023 requires an explicit resource budget for expensive
operations. Python's `BoundedSemaphore` is the fail-loud primitive that
prevents a double release from raising the cap.

## References

Fielding, R., Nottingham, M., & Reschke, J. (Eds.). (2022). *HTTP
semantics* (RFC 9110). Internet Engineering Task Force.
https://doi.org/10.17487/RFC9110

Nottingham, M., & Fielding, R. (2012). *Additional HTTP status codes*
(RFC 6585). Internet Engineering Task Force.
https://doi.org/10.17487/RFC6585

Open Worldwide Application Security Project. (2023). *API4:2023
unrestricted resource consumption*. In *OWASP API security top 10
2023*.
https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/

Python Software Foundation. (n.d.). *threading — Thread-based
parallelism*.
https://docs.python.org/3/library/threading.html#threading.BoundedSemaphore

Tiangolo, S. (n.d.). *Request files*. FastAPI.
https://fastapi.tiangolo.com/tutorial/request-files/
