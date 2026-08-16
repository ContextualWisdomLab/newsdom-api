"""Process-local parser admission before multipart body reads."""

from __future__ import annotations

import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

import pytest
from fastapi.testclient import TestClient

from newsdom_api.config import (
    MAX_CONCURRENT_PARSES_ENV_VAR,
    RuntimeConfigurationError,
    RuntimeSettings,
    load_runtime_settings,
)
from newsdom_api.main import (
    PARSE_UPLOAD_CHUNK_BYTES,
    TOO_MANY_REQUESTS_DETAIL,
    create_app,
)
from newsdom_api.parse_admission import ParseAdmissionLimiter

_PDF_FILES = {
    "file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")
}


def _settings(*, max_concurrent_parses: int = 1) -> RuntimeSettings:
    """Build required-mode settings with an explicit process admission cap."""

    return RuntimeSettings(
        api_token="s3cret-token",
        max_concurrent_parses=max_concurrent_parses,
    )


def _client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    max_concurrent_parses: int = 1,
    hold: threading.Event | None = None,
) -> tuple[TestClient, dict[str, int]]:
    """Return a client whose parser records entry and can hold the lease."""

    calls = {"count": 0}

    def fake_parse_pdf(*_args: object, **_kwargs: object) -> dict[str, object]:
        calls["count"] += 1
        if hold is not None:
            hold.wait(timeout=5)
        return {"document_id": "fixture", "pages": []}

    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf)
    application = create_app(
        _settings(max_concurrent_parses=max_concurrent_parses),
        runtime_readiness_probe=lambda: True,
    )
    return TestClient(application), calls


def test_custom_admission_capacity_is_frozen_on_the_settings_object() -> None:
    """A documented positive integer must become the process-local cap."""

    settings = load_runtime_settings(
        {
            "NEWSDOM_API_TOKEN": "token",
            MAX_CONCURRENT_PARSES_ENV_VAR: "8",
        }
    )
    assert settings.max_concurrent_parses == 8


def test_default_admission_capacity_is_one_parse_per_process() -> None:
    """A missing capacity setting must stay at the conservative default of one."""

    settings = load_runtime_settings({"NEWSDOM_API_TOKEN": "token"})
    assert settings.max_concurrent_parses == 1


@pytest.mark.parametrize("raw", ["0", "129", "-1", "1.5", "many", ""])
def test_invalid_admission_capacity_fails_closed(raw: str) -> None:
    """Operators must not launch with an unbounded or non-integer admission cap."""

    with pytest.raises(RuntimeConfigurationError, match=MAX_CONCURRENT_PARSES_ENV_VAR):
        load_runtime_settings(
            {
                "NEWSDOM_API_TOKEN": "token",
                MAX_CONCURRENT_PARSES_ENV_VAR: raw,
            }
        )


def test_direct_settings_reject_out_of_range_capacity() -> None:
    """Direct construction must use the same 1..128 fail-closed window."""

    with pytest.raises(RuntimeConfigurationError, match="1..128"):
        RuntimeSettings(api_token="token", max_concurrent_parses=0)
    with pytest.raises(RuntimeConfigurationError, match="1..128"):
        RuntimeSettings(api_token="token", max_concurrent_parses=129)


def test_limiter_rejects_invalid_capacity() -> None:
    """The limiter must not accept a cap outside the documented window."""

    with pytest.raises(ValueError, match="1..128"):
        ParseAdmissionLimiter(0)


def test_limiter_is_non_waiting_and_rejects_double_release() -> None:
    """A saturated limiter fails immediately; extra release must not expand capacity."""

    limiter = ParseAdmissionLimiter(capacity=1)
    assert limiter.try_acquire() is True
    assert limiter.try_acquire() is False
    limiter.release()
    assert limiter.try_acquire() is True
    limiter.release()
    with pytest.raises(ValueError):
        limiter.release()


def test_applications_do_not_share_admission_capacity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each FastAPI instance keeps its own last-resort process budget."""

    first, _ = _client(monkeypatch, max_concurrent_parses=1)
    second, _ = _client(monkeypatch, max_concurrent_parses=1)
    first_limiter = first.app.state.parse_admission_limiter
    second_limiter = second.app.state.parse_admission_limiter
    assert first_limiter is not second_limiter
    assert first_limiter.try_acquire() is True
    assert second_limiter.try_acquire() is True


def test_saturated_parse_returns_fixed_429_without_calling_parser(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Callers retry after Retry-After; they must not see a 503 or a parser start."""

    client, calls = _client(monkeypatch, max_concurrent_parses=1)
    limiter = client.app.state.parse_admission_limiter
    assert limiter.try_acquire() is True
    response = client.post(
        "/parse",
        files=_PDF_FILES,
        headers={"Authorization": "Bearer s3cret-token"},
    )
    assert response.status_code == 429
    assert response.json() == {"detail": TOO_MANY_REQUESTS_DETAIL}
    assert response.headers["Retry-After"] == "1"
    assert response.headers["Cache-Control"].startswith("no-store")
    assert calls["count"] == 0
    limiter.release()


def test_unauthenticated_requests_do_not_consume_admission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 401 must leave the single process slot available for a later valid caller."""

    client, calls = _client(monkeypatch, max_concurrent_parses=1)
    denied = client.post("/parse", files=_PDF_FILES)
    assert denied.status_code == 401
    accepted = client.post(
        "/parse",
        files=_PDF_FILES,
        headers={"Authorization": "Bearer s3cret-token"},
    )
    assert accepted.status_code == 200
    assert calls["count"] == 1


def test_admission_lease_is_released_after_invalid_media_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 415 after admission must not permanently saturate the replica."""

    client, _calls = _client(monkeypatch, max_concurrent_parses=1)
    rejected = client.post(
        "/parse",
        files={"file": ("note.txt", b"hello", "text/plain")},
        headers={"Authorization": "Bearer s3cret-token"},
    )
    assert rejected.status_code == 415
    accepted = client.post(
        "/parse",
        files=_PDF_FILES,
        headers={"Authorization": "Bearer s3cret-token"},
    )
    assert accepted.status_code == 200


def test_burst_of_thirty_two_at_capacity_four_returns_twenty_eight_429s(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A realistic overload burst must fail closed without a waiting queue."""

    hold = threading.Event()
    entered = threading.Semaphore(0)
    calls = {"count": 0}

    def fake_parse_pdf(*_args: object, **_kwargs: object) -> dict[str, object]:
        calls["count"] += 1
        entered.release()
        hold.wait(timeout=5)
        return {"document_id": "fixture", "pages": []}

    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf)
    application = create_app(
        _settings(max_concurrent_parses=4),
        runtime_readiness_probe=lambda: True,
    )
    client = TestClient(application)
    headers = {"Authorization": "Bearer s3cret-token"}

    def _post() -> int:
        return client.post("/parse", files=_PDF_FILES, headers=headers).status_code

    with ThreadPoolExecutor(max_workers=32) as pool:
        futures = [pool.submit(_post) for _ in range(32)]
        for _ in range(4):
            assert entered.acquire(timeout=5)
        pending = set(futures)
        rejected: list[int] = []
        while len(rejected) < 28:
            done, pending = wait(pending, timeout=5, return_when=FIRST_COMPLETED)
            assert done
            rejected.extend(future.result(timeout=1) for future in done)
        hold.set()
        admitted = [future.result(timeout=10) for future in pending]

    assert rejected.count(429) == 28
    assert admitted.count(200) == 4
    assert calls["count"] == 4


def test_upload_chunk_size_stays_at_rollback_8_kib() -> None:
    """#534 forbids swapping 8 KiB for an unbenchmarked 1 MiB constant."""

    assert PARSE_UPLOAD_CHUNK_BYTES == 8192


def test_missing_limiter_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    """A mis-wired application must not parse without a process-local limiter."""

    client, calls = _client(monkeypatch)
    client.app.state.parse_admission_limiter = object()
    with pytest.raises(RuntimeError, match="unavailable"):
        client.post(
            "/parse",
            files=_PDF_FILES,
            headers={"Authorization": "Bearer s3cret-token"},
        )
    assert calls["count"] == 0


def test_openapi_publishes_429_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clients must see the overload status in the published /parse contract."""

    client, _calls = _client(monkeypatch)
    spec = client.get("/openapi.json").json()
    responses = spec["paths"]["/parse"]["post"]["responses"]
    assert "429" in responses
