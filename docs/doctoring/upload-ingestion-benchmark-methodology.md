# Upload-ingestion benchmark methodology

## Purpose

This record defines the reproducible evidence required before NewsDOM changes
the current 8 KiB upload read size. It deliberately does **not** select a new
default or claim a performance improvement. The benchmark compares every
candidate required by issue #534 while the production parser admission boundary
remains fixed and independently testable.

FastAPI documents that the asynchronous `UploadFile` methods run the underlying
file operations in a thread pool. Starlette documents that `UploadFile` shares
AnyIO's thread-pool capacity with synchronous endpoints, file responses,
background tasks, and other framework work. Chunk size therefore affects more
than sequential file-copy throughput: it changes the number of thread-pool
crossings, event-loop responsiveness, and the amount of data retained by each
concurrent request.

## Candidate matrix

The default command measures the following exact candidates:

| Candidate | Exact or resolved read size |
| --- | ---: |
| `8kib` | 8,192 bytes |
| `64kib` | 65,536 bytes |
| `256kib` | 262,144 bytes |
| `1mib` | 1,048,576 bytes |
| `adaptive` | 64 KiB at 1 MiB, 256 KiB through 5 MiB, otherwise 1 MiB |

Every candidate is measured at concurrency `1`, `8`, `32`, and `128`. The
fixture set must contain representative PDFs near 1 MiB, 5 MiB, and the existing
20 MiB request limit. Fixtures remain outside public git when licensing,
privacy, or contractual restrictions apply. The raw report stores each fixture
name, byte size, and SHA-256 identifier so an internal evidence bundle can be
audited without publishing document content.

The adaptive rule is only a benchmark candidate. It is not production behavior
and must not be described as selected until a reviewed result satisfies the
acceptance rules below.

## Reproducible command

```bash
uv run python tools/benchmark_upload_ingestion.py \
  --fixtures-dir /absolute/path/to/approved-pdf-fixtures \
  --output artifacts/upload-ingestion-result.json \
  --repetitions 3
```

The default command runs the complete candidate and concurrency matrix. Filters
are available for diagnosis, but a filtered run is not sufficient for a default
selection. Execute the benchmark on an otherwise idle, dedicated Linux
environment and record the container or host image, CPU model, memory, storage
class, filesystem, Python and dependency lock, commit SHA, worker count, and
whether the files were cold or warm in the operating-system cache.

## Measurement implementation

`tools/benchmark_upload_ingestion.py` uses a real file-backed Starlette
`UploadFile` and copies each request to an independent temporary file. It does
not use an in-memory bytes object as the source of accepted evidence.

The harness retains both request-level and cohort-level raw observations and
derives:

- p50 and p95 request latency by deterministic nearest-rank percentile;
- aggregate copied bytes divided by cohort wall time;
- total `UploadFile.read(size)` calls;
- process CPU time;
- each cohort's current-RSS baseline, sampled peak RSS, and peak-minus-baseline
  delta;
- temporary bytes written;
- raw event-loop scheduling-delay samples, their nearest-rank p95, and maximum.

Python defines `time.perf_counter()` as a high-resolution monotonic clock suited
to duration measurement and `time.process_time()` as process CPU time excluding
sleep. Event-loop responsiveness is reported as a real nearest-rank p95 over the
retained probe samples, not as a maximum mislabeled as a percentile.

On Linux, the harness samples `VmRSS` from `/proc/self/status` during each
cohort. The Linux kernel distinguishes `VmRSS`, the current resident set, from
`VmHWM`, the process-lifetime resident-set high-water mark. A lifetime high-water
metric would contaminate later matrix cases with memory used by earlier cases;
therefore `resource.getrusage(...).ru_maxrss` is not accepted as case-local
memory evidence. Every report preserves the cohort baseline and sampled peak so
the absolute process budget and incremental case pressure can both be audited.

If `/proc/self/status` is unavailable or malformed, the provider returns zero
and the environment record still identifies `linux_proc_status_vmrss`. Such a
run does not satisfy the final memory-evidence gate. Other operating systems
require a separately reviewed current-RSS provider before their memory numbers
can support a production default.

RSS sampling is observational rather than an allocation profiler. Candidate
selection therefore requires repeated clean-process runs and should be
corroborated with operating-system or container memory telemetry. Do not treat
`peak_rss_delta_bytes` as exact ownership of memory that may be shared,
allocator-retained, or concurrently used by another thread.

## Raw evidence schema

The checked-in JSON Schema is:

```text
docs/benchmarks/upload-ingestion-result.schema.json
```

Accepted evidence must validate against schema version `1.1.0`. The report keeps
request samples and raw cohort observations alongside aggregates, rejects
unknown top-level and case fields, and records the exact resolved byte size even
for the adaptive candidate. Generated reports are evidence artifacts, not source
files; do not commit private fixture paths or customer document names.

## Interpretation and selection gates

A candidate can replace 8 KiB only when the exact current-head report shows all
of the following across the complete matrix:

1. no upload-size, magic-byte, temporary-file cleanup, authentication, or parser
   admission regression;
2. no materially worse request p95 latency or event-loop p95 at high
   concurrency, with the maximum retained for tail diagnosis;
3. absolute sampled peak RSS and peak-minus-baseline pressure remain inside an
   explicit per-process budget;
4. thread-pool read-call reduction does not merely shift cost to larger retained
   buffers or storage stalls;
5. results are reproduced on at least two runs from clean processes;
6. the selected rule is simple enough to explain, test, operate, and roll back;
7. the production regression test, README, architecture, runbook, CHANGELOG, and
   release evidence all identify the same value or rule.

Compare distributions and operational thresholds rather than publishing a
single mean. A percentage improvement may be stated only when the attached raw
report, environment manifest, analysis code, and variability treatment support
it.

## Accuracy and security invariants

Chunk experiments must preserve:

- authentication and process admission before multipart body consumption;
- first-five-byte PDF magic rejection;
- the exact 20 MiB streamed limit even when size metadata is missing;
- no write of the chunk that crosses the limit;
- request-scoped temporary files and cleanup after every outcome;
- structural PDF validation before MinerU;
- parser-not-called evidence for rejected requests;
- fixed sanitized errors and no-store response headers.

The benchmark is not permission to bypass `NEWSDOM_MAX_CONCURRENT_PARSES`.
Concurrency cases measure ingestion behavior under controlled experiments; a
production deployment must continue to reject active parser work above its
accepted process budget.

## Rollback

Keep 8 KiB as the rollback value until a new policy has exact-head benchmark and
release acceptance. If a deployed policy increases RSS, event-loop delay,
temporary-storage pressure, timeout rate, or parser failures, restore the prior
value or release, restart processes so immutable configuration and code are
loaded, and rerun the overload and upload-limit smoke tests.

## References

FastAPI. (2026). *Request files*. FastAPI documentation.
https://fastapi.tiangolo.com/tutorial/request-files/

Linux Kernel Organization. (2026). *The /proc filesystem*. Linux kernel
documentation. https://www.kernel.org/doc/html/latest/filesystems/proc.html

Python Software Foundation. (2026). *time—Time access and conversions (Python
3.14.6 documentation)*. https://docs.python.org/3/library/time.html

Starlette. (2026). *Thread pool*. Starlette documentation.
https://www.starlette.io/threadpool/
