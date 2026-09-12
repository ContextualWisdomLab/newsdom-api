# ADR-0003: Isolate PDF structural validation

## Status

Accepted

## Context

`/parse` previously called `pypdf.PdfReader(..., strict=True)` on the
ASGI event loop after a 20 MiB upload cap. A bounded upload can still
expand into excessive CPU or memory while the parser walks objects,
cross-reference tables, or cyclic graphs. That stalls every concurrent
request on the same worker and gives a hostile PDF a process-wide
denial-of-service path.

Issue #624 requires a disposable child, a wall-clock kill, and
production-supported CPU plus address-space limits applied before the
untrusted file is opened. Admission limiting (#548) remains a separate
outer defense and is not reimplemented here.

This sidecar has no browser UI, so Storybook and design-token work
belong in clearfolio. NewsDOM stays independently deployable and
reusable as a naruon module.

## Decision

Run structural validation in `src/newsdom_api/pdf_structure_validator.py`:

- the parent never opens the PDF with pypdf on the event loop
- the child applies `RLIMIT_CPU` (5 seconds), `RLIMIT_AS` (512 MiB),
  `RLIMIT_CORE` (0), and `RLIMIT_NPROC` (64) before `PdfReader`
- the parent kills the process group after 5 wall-clock seconds and
  waits at most 1 second to reclaim it
- a child killed by signal (`returncode < 0`), including `RLIMIT_CPU`
  `SIGKILL`, is an invalid document — never a retried 503
- the child inherits only an allowlisted environment, `stdin=DEVNULL`,
  and a new session; this is resource isolation, not a full sandbox
- the child returns only `valid`, `invalid_document`, or
  `validator_failure`
- client-caused parser errors, timeouts, and signal kills map to the
  fixed 415 contract
- spawn or unsupported-platform failures fail closed with the fixed
  503 contract and an operator log
- non-Linux hosts fail closed even when `RLIMIT_*` names exist; there
  is no in-process `PdfReader` fallback

## Consequences

### Positive

- A hanging or memory-expanding PDF cannot pin the API event loop.
- Callers keep one non-sensitive 415 or 503 body.
- The leaf service stays useful without naruon, Redis, or a GPU.

### Negative

- Each upload pays one process spawn. Accuracy and isolation outrank
  speed.
- Non-Linux hosts, including Darwin where `RLIMIT_AS` may be a no-op,
  fail closed until an equivalent Linux sandbox is explicitly adopted.

## Rollback

Restore the previous image. The previous behavior is synchronous
in-process `PdfReader` on the event loop. Do not disable the child
by setting an environment flag.
