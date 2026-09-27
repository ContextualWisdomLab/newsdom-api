# Parser cancellation and actual work lifetime

## Scope and continuity

This follow-up is based on owner admission PR #548 at
`dd5ebcfac3f0163fb083741ae834d4f304cb4797`. It reuses that PR's authentication
before multipart handling, immutable process capacity, non-waiting semaphore,
fixed 429/Retry-After/cache contract and readiness policy. It adds no queue or
new capacity setting. The native MinerU adapter is a separate change.

## Root cause

Starlette BaseHTTPMiddleware runs the downstream endpoint in another task.
Cancelling the outer request can interrupt `call_next` and release the middleware
lease while the synchronous parser thread still runs. Cancelling an
`asyncio.to_thread` task likewise does not terminate its running thread.

An actual authenticated ASGI regression cancelled the first request while a
real synchronous worker remained active. The old implementation accepted the
second request with 200 where the required result was 429. Its prior fake
cancellation test only checked lease return after a downstream coroutine raised;
it did not prove work had ended.

## Repair

The endpoint submits parsing to the existing standard default executor,
preserving copied context variables, and stores its completion future in
shared request state before yielding. It shields that future and waits for
actual completion before removing the temporary upload on cancellation.
AnyIO shielding prevents repeated ASGI scope cancellation from spinning the
wait; direct task cancellation is also handled.

The middleware retains its existing lease. If no worker was submitted, it
releases immediately. Otherwise exactly one completion callback releases that
lease, even if the outer request has already been cancelled. No extra pool,
semaphore, per-request configuration or waiting queue is introduced.

An already-completed future schedules the callback on the event loop; the
lease can remain held for one additional loop turn. This is conservative.
Capacity remains per application/process. Forced process termination and
cross-replica/shared-server admission are outside this guarantee.

## Verification

The ASGI test checks fixed 429, exact Retry-After, no-store, no second worker,
and successful recovery after actual worker completion. It covers successful
and failing cancelled workers. Additional real endpoint/thread checks cover
repeated direct cancellation, actual AnyIO cancellation scopes and orderly
cancellation of all remaining event-loop tasks. The old separate-task version
failed the shutdown test by deleting the input while the thread remained live.

Required production coverage is 100% with warnings as errors. A broader optional
API-plus-tools measurement reported 96.15%: its uncovered lines belong solely
to the unchanged `tools/benchmark_upload_ingestion.py`. This report is not a
claim that that broader scope passes. Independent source review found no
blocking issue in lease ownership or orderly shutdown; hosted security/review
and protected merge remain separate acceptance requirements.

Final required-gate run: 536 tests pass, warnings as errors, production API
branch coverage 100% (893 statements, 264 branches). Both repository
`tests.yml` and `quality-gate.yml` require this API-only coverage scope. The new
lifetime test module passes Ruff; `git diff --check` passes. No coverage target,
workflow, dependency lock or admission setting was changed.
