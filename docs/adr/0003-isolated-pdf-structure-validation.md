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
- the child applies `RLIMIT_CPU` (5 seconds) and `RLIMIT_AS` (512 MiB)
  before `PdfReader`
- the parent kills the child after 5 wall-clock seconds
- the child returns only `valid`, `invalid_document`, or
  `validator_failure`
- client-caused parser errors and timeouts map to the fixed 415
  contract
- spawn or unsupported-platform failures fail closed with the fixed
  503 contract and an operator log
- hosts without `setrlimit` do not fall back to in-process parsing

## Consequences

### Positive

- A hanging or memory-expanding PDF cannot pin the API event loop.
- Callers keep one non-sensitive 415 or 503 body.
- The leaf service stays useful without naruon, Redis, or a GPU.

### Negative

- Each upload pays one process spawn. Accuracy and isolation outrank
  speed.
- Windows and other hosts without POSIX resource limits fail closed
  until an equivalent sandbox is explicitly adopted.

## Rollback

Restore the previous image. The previous behavior is synchronous
in-process `PdfReader` on the event loop. Do not disable the child
by setting an environment flag.
