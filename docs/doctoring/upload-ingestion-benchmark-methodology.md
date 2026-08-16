# Upload-ingestion benchmark methodology

## Buyer next action

Run `uv run python tools/benchmark_upload_ingestion.py --smoke` on a
Linux replica before changing `PARSE_UPLOAD_CHUNK_BYTES`. Keep 8 KiB in
production until a complete matrix on representative PDFs is reviewed.
Do not merge an unvalidated 64 KiB or 1 MiB substitution.

## Purpose

Issue #534 requires evidence before the upload chunk changes. This
harness records read-call count, elapsed time, and sampled Linux
`VmRSS` for candidate chunk sizes. It does not select a new production
default.

## Command

```bash
uv run python tools/benchmark_upload_ingestion.py --smoke
uv run python tools/benchmark_upload_ingestion.py \
  --output docs/benchmarks/upload-ingestion-result.json
```

`--smoke` uses the checked-in synthetic PDF, chunk `8kib`, and
concurrency `1`. A full matrix may add `--chunks 8kib,64kib,256kib,1mib`
and `--concurrency 1,8,32,128`.

## Evidence rules

- Fixture size and SHA-256 are recorded.
- Peak RSS is sampled from `/proc/self/status` `VmRSS` on Linux. A run
  without that file reports zero and is not sufficient for a memory
  decision.
- `resource.ru_maxrss` is a process-lifetime high-water mark and must
  not be used as a per-case peak.
- No speedup percentage may be claimed without the complete reviewed
  matrix.

## References

Bradner, S. (1997). *Key words for use in RFCs to indicate requirement
levels* (RFC 2119). Internet Engineering Task Force.
https://doi.org/10.17487/RFC2119

Gregg, B. (2020). *Systems performance: Enterprise and the cloud*
(2nd ed.). Addison-Wesley.

Tiangolo, S. (n.d.). *Request files*. FastAPI.
https://fastapi.tiangolo.com/tutorial/request-files/
