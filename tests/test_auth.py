"""Tests for fail-closed parser authentication and immutable runtime settings."""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import HTTPException, Request, Response
from fastapi.testclient import TestClient

from newsdom_api import config
from newsdom_api.config import (
    API_TOKEN_ENV_VAR,
    AUTH_MODE_ENV_VAR,
    RUNTIME_PROFILE_ENV_VAR,
    AuthenticationMode,
    RuntimeConfigurationError,
    RuntimeProfile,
    RuntimeSettings,
    get_api_token,
    load_runtime_settings,
)
from newsdom_api.main import (
    MAX_AUTHORIZATION_HEADER_BYTES,
    MAX_PARSE_REQUEST_BYTES,
    create_app,
    security_boundary_middleware,
)

_PDF_FILES = {
    "file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")
}


def _settings(
    *,
    token: str | None = "s3cret-token",
    mode: AuthenticationMode = AuthenticationMode.REQUIRED,
    profile: RuntimeProfile = RuntimeProfile.PRODUCTION,
) -> RuntimeSettings:
    """Build one explicit immutable settings object for an application test."""

    return RuntimeSettings(
        authentication_mode=mode,
        runtime_profile=profile,
        api_token=token,
    )


def _request_scope(
    application,
    *,
    method: str = "POST",
    path: str = "/parse",
    headers: list[tuple[bytes, bytes]] | None = None,
) -> dict:
    """Build the minimal ASGI request scope used by middleware tests."""

    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": headers or [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "app": application,
    }


@pytest.fixture
def parser_spy(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    """Replace PDF validation and parsing while recording real parser entry."""

    calls = {"count": 0}

    def fake_parse_pdf(*_args, **_kwargs):
        calls["count"] += 1
        return {"document_id": "fixture", "pages": []}

    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf)
    return calls


def test_required_mode_accepts_exact_bearer(parser_spy: dict[str, int]) -> None:
    """A configured required-mode service should accept one exact bearer header."""

    application = create_app(_settings(), runtime_readiness_probe=lambda: True)
    response = TestClient(application).post(
        "/parse",
        files=_PDF_FILES,
        headers={"Authorization": "Bearer s3cret-token"},
    )

    assert response.status_code == 200
    assert parser_spy["count"] == 1


@pytest.mark.parametrize(
    "headers",
    [
        None,
        {"Authorization": "Bearer wrong-token"},
        [(b"Authorization", b"Bearer \xe2\x98\x83")],
        {"Authorization": "Basic dXNlcjpwYXNz"},
        {"Authorization": "Bearer " + "x" * (MAX_AUTHORIZATION_HEADER_BYTES + 1)},
        [
            (b"Authorization", b"Bearer s3cret-token"),
            (b"Authorization", b"Bearer s3cret-token"),
        ],
    ],
)
def test_required_mode_rejects_hostile_credentials_before_parser(
    headers,
    parser_spy: dict[str, int],
) -> None:
    """Missing, malformed, Unicode, oversized, or duplicated credentials stay 401."""

    application = create_app(_settings(), runtime_readiness_probe=lambda: True)
    request_kwargs = {"files": _PDF_FILES}
    if headers is not None:
        request_kwargs["headers"] = headers
    response = TestClient(application, raise_server_exceptions=False).post(
        "/parse", **request_kwargs
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert parser_spy["count"] == 0


def test_missing_required_token_is_service_configuration_failure(
    parser_spy: dict[str, int],
) -> None:
    """A missing server token should return fixed 503 rather than caller 401."""

    application = create_app(
        _settings(token=None), runtime_readiness_probe=lambda: True
    )
    response = TestClient(application).post("/parse", files=_PDF_FILES)

    assert response.status_code == 503
    assert response.json() == {"detail": "Service Unavailable"}
    assert "WWW-Authenticate" not in response.headers
    assert parser_spy["count"] == 0


def test_development_disabled_mode_allows_parse_and_warns_once(
    parser_spy: dict[str, int], caplog: pytest.LogCaptureFixture
) -> None:
    """The explicit development bypass should be usable and logged once at startup."""

    caplog.set_level(logging.WARNING, logger="newsdom_api")
    application = create_app(
        _settings(
            token=None,
            mode=AuthenticationMode.DISABLED,
            profile=RuntimeProfile.DEVELOPMENT,
        ),
        runtime_readiness_probe=lambda: True,
    )
    client = TestClient(application)

    assert client.post("/parse", files=_PDF_FILES).status_code == 200
    assert client.post("/parse", files=_PDF_FILES).status_code == 200
    assert parser_spy["count"] == 2
    messages = [record.getMessage() for record in caplog.records]
    assert messages.count(
        "Parser authentication is disabled for the explicit development profile"
    ) == 1


def test_direct_runtime_settings_reject_invalid_security_invariants() -> None:
    """Direct application settings must enforce the same fail-closed boundary."""

    with pytest.raises(RuntimeConfigurationError, match="development"):
        RuntimeSettings(
            authentication_mode=AuthenticationMode.DISABLED,
            runtime_profile=RuntimeProfile.PRODUCTION,
            api_token=None,
        )

    with pytest.raises(RuntimeConfigurationError, match="blank"):
        RuntimeSettings(api_token="   ")

    with pytest.raises(RuntimeConfigurationError, match="too long"):
        RuntimeSettings(api_token="x" * 4090)


def test_direct_runtime_settings_normalize_token_once() -> None:
    """Direct construction should freeze the normalized bearer secret."""

    settings = RuntimeSettings(api_token="  stable-token\n")

    assert settings.api_token == "stable-token"
    assert settings.authentication_ready is True


def test_disabled_mode_is_rejected_outside_development() -> None:
    """Production cannot opt into the unauthenticated development bypass."""

    with pytest.raises(RuntimeConfigurationError, match="development"):
        load_runtime_settings(
            {
                AUTH_MODE_ENV_VAR: "disabled",
                RUNTIME_PROFILE_ENV_VAR: "production",
            }
        )


@pytest.mark.parametrize(
    ("variable", "value"),
    [
        (AUTH_MODE_ENV_VAR, "sometimes"),
        (RUNTIME_PROFILE_ENV_VAR, "staging"),
    ],
)
def test_unknown_runtime_modes_fail_deterministically(
    variable: str, value: str
) -> None:
    """Unknown mode strings must not silently select a permissive fallback."""

    with pytest.raises(RuntimeConfigurationError, match=variable):
        load_runtime_settings({variable: value})


def test_runtime_settings_are_immutable_after_application_creation(
    monkeypatch: pytest.MonkeyPatch, parser_spy: dict[str, int]
) -> None:
    """Environment changes after app creation must not rotate its security state."""

    application = create_app(
        _settings(token="token-a"), runtime_readiness_probe=lambda: True
    )
    monkeypatch.setenv(API_TOKEN_ENV_VAR, "token-b")
    client = TestClient(application)

    rejected = client.post(
        "/parse", files=_PDF_FILES, headers={"Authorization": "Bearer token-b"}
    )
    accepted = client.post(
        "/parse", files=_PDF_FILES, headers={"Authorization": "Bearer token-a"}
    )

    assert rejected.status_code == 401
    assert accepted.status_code == 200
    assert parser_spy["count"] == 1


def test_corrupted_application_settings_fail_closed_with_sanitized_response() -> None:
    """Missing runtime state must not expose internals or accept traffic."""

    application = create_app(_settings(), runtime_readiness_probe=lambda: True)
    application.state.runtime_settings = object()

    response = TestClient(application, raise_server_exceptions=False).get("/ready")

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_health_is_always_liveness_only() -> None:
    """Health should remain public even when authentication readiness is invalid."""

    application = create_app(
        _settings(token=None), runtime_readiness_probe=lambda: False
    )
    response = TestClient(application).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    ("settings", "runtime_ready", "expected_status"),
    [
        (_settings(), True, 200),
        (_settings(token=None), True, 503),
        (_settings(), False, 503),
        (
            _settings(
                token=None,
                mode=AuthenticationMode.DISABLED,
                profile=RuntimeProfile.DEVELOPMENT,
            ),
            True,
            200,
        ),
    ],
)
def test_ready_combines_authentication_and_parser_runtime(
    settings: RuntimeSettings,
    runtime_ready: bool,
    expected_status: int,
) -> None:
    """Readiness must represent both security configuration and parser runtime."""

    application = create_app(settings, runtime_readiness_probe=lambda: runtime_ready)
    response = TestClient(application).get("/ready")

    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json() == {"status": "ready"}
    else:
        assert response.json() == {"detail": "Service Unavailable"}
        assert settings.api_token not in response.text if settings.api_token else True


def test_default_runtime_probe_is_not_an_unconditional_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default app factory must consult MinerU availability rather than a stub."""

    monkeypatch.setattr(
        "newsdom_api.main.mineru_runtime_available", lambda: False, raising=False
    )
    response = TestClient(create_app(_settings())).get("/ready")

    assert response.status_code == 503


def test_authentication_middleware_rejects_before_reading_request_body() -> None:
    """Reject parser access before ASGI body receive or downstream parsing."""

    application = create_app(
        _settings(token=None), runtime_readiness_probe=lambda: True
    )
    body_read = False

    async def receive():
        nonlocal body_read
        body_read = True
        raise AssertionError("request body should not be read")

    async def call_next(_request):
        raise AssertionError("downstream application should not run")

    request = Request(_request_scope(application), receive)

    response = asyncio.run(security_boundary_middleware(request, call_next))

    assert response.status_code == 503
    assert body_read is False


def test_parse_request_content_length_is_rejected_before_body_read() -> None:
    """Reject a declared oversized multipart body before receiving any bytes."""

    application = create_app(_settings(), runtime_readiness_probe=lambda: True)
    body_read = False

    async def receive():
        nonlocal body_read
        body_read = True
        raise AssertionError("oversized request body should not be read")

    async def call_next(_request):
        raise AssertionError("oversized request should not reach the parser")

    request = Request(
        _request_scope(
            application,
            headers=[
                (b"authorization", b"Bearer s3cret-token"),
                (
                    b"content-length",
                    str(MAX_PARSE_REQUEST_BYTES + 1).encode("ascii"),
                ),
            ],
        ),
        receive,
    )

    response = asyncio.run(security_boundary_middleware(request, call_next))

    assert response.status_code == 413
    assert body_read is False


def test_parse_request_budget_runs_in_the_real_middleware_stack(
    monkeypatch: pytest.MonkeyPatch,
    parser_spy: dict[str, int],
) -> None:
    """Reject an oversized multipart request before endpoint execution."""

    monkeypatch.setattr("newsdom_api.main.MAX_PARSE_REQUEST_BYTES", 64)
    application = create_app(_settings(), runtime_readiness_probe=lambda: True)

    response = TestClient(application).post(
        "/parse",
        files=_PDF_FILES,
        headers={"Authorization": "Bearer s3cret-token"},
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "Payload Too Large"}
    assert parser_spy["count"] == 0


def test_parse_request_stream_budget_runs_in_the_real_middleware_stack(
    monkeypatch: pytest.MonkeyPatch,
    parser_spy: dict[str, int],
) -> None:
    """Reject an oversized chunked request without relying on Content-Length."""

    monkeypatch.setattr("newsdom_api.main.MAX_PARSE_REQUEST_BYTES", 64)
    application = create_app(_settings(), runtime_readiness_probe=lambda: True)

    def body_chunks():
        yield b"x" * 64
        yield b"x"

    response = TestClient(application).post(
        "/parse",
        content=body_chunks(),
        headers={
            "Authorization": "Bearer s3cret-token",
            "Content-Type": "multipart/form-data; boundary=test",
        },
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "Payload Too Large"}
    assert parser_spy["count"] == 0


def test_parse_request_stream_is_bounded_without_content_length() -> None:
    """Enforce the same total body budget for chunked or lengthless requests."""

    application = create_app(_settings(), runtime_readiness_probe=lambda: True)
    messages = iter(
        [
            {
                "type": "http.request",
                "body": b"x" * MAX_PARSE_REQUEST_BYTES,
                "more_body": True,
            },
            {"type": "http.request", "body": b"x", "more_body": False},
        ]
    )

    async def receive():
        return next(messages)

    async def call_next(request):
        async for _chunk in request.stream():
            pass
        return Response(status_code=204)

    request = Request(
        _request_scope(
            application,
            headers=[(b"authorization", b"Bearer s3cret-token")],
        ),
        receive,
    )

    response = asyncio.run(security_boundary_middleware(request, call_next))

    assert response.status_code == 413


def test_parse_request_limiter_preserves_disconnect_messages() -> None:
    """Forward non-body ASGI messages without treating them as request bytes."""

    application = create_app(_settings(), runtime_readiness_probe=lambda: True)

    async def receive():
        return {"type": "http.disconnect"}

    async def call_next(request):
        assert await request.receive() == {"type": "http.disconnect"}
        return Response(status_code=204)

    response = asyncio.run(
        security_boundary_middleware(
            Request(
                _request_scope(
                    application,
                    headers=[(b"authorization", b"Bearer s3cret-token")],
                ),
                receive,
            ),
            call_next,
        )
    )

    assert response.status_code == 204


def test_security_boundary_does_not_mask_unrelated_http_errors() -> None:
    """Propagate downstream HTTP errors that are not the body-limit signal."""

    application = create_app(_settings(), runtime_readiness_probe=lambda: True)

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def call_next(_request):
        raise HTTPException(status_code=409, detail="conflict")

    with pytest.raises(HTTPException, match="409: conflict"):
        asyncio.run(
            security_boundary_middleware(
                Request(
                    _request_scope(application, method="GET", path="/health"),
                    receive,
                ),
                call_next,
            )
        )


def test_concurrent_requests_cannot_switch_authentication_state(
    parser_spy: dict[str, int],
) -> None:
    """Concurrent callers should observe one frozen token and mode."""

    application = create_app(
        _settings(token="fixed"), runtime_readiness_probe=lambda: True
    )

    def request(token: str) -> int:
        return TestClient(application).post(
            "/parse",
            files=_PDF_FILES,
            headers={"Authorization": f"Bearer {token}"},
        ).status_code

    tokens = ["fixed" if index % 2 == 0 else "changed" for index in range(20)]
    with ThreadPoolExecutor(max_workers=8) as executor:
        statuses = list(executor.map(request, tokens))

    assert statuses.count(200) == 10
    assert statuses.count(401) == 10
    assert parser_spy["count"] == 10


def test_openapi_and_settings_repr_do_not_expose_bearer_secret() -> None:
    """Schema output and diagnostic repr must never contain the configured token."""

    secret = "do-not-disclose"
    settings = _settings(token=secret)
    application = create_app(settings, runtime_readiness_probe=lambda: True)
    openapi_response = TestClient(application).get("/openapi.json")
    openapi_text = openapi_response.text
    openapi_document = openapi_response.json()

    assert secret not in openapi_text
    assert secret not in repr(settings)
    assert openapi_document["components"]["securitySchemes"]["BearerAuth"] == {
        "type": "http",
        "scheme": "bearer",
    }


def test_get_api_token_normalizes_bootstrap_transport() -> None:
    """Whitespace-only secrets are absent and mounted newline suffixes are stripped."""

    assert get_api_token({}) is None
    assert get_api_token({API_TOKEN_ENV_VAR: "   "}) is None
    assert get_api_token({API_TOKEN_ENV_VAR: "  padded-token\n"}) == "padded-token"


def test_default_runtime_settings_are_required_production() -> None:
    """Missing mode variables must select the fail-closed production contract."""

    settings = load_runtime_settings({API_TOKEN_ENV_VAR: "token"})

    assert settings.authentication_mode is AuthenticationMode.REQUIRED
    assert settings.runtime_profile is RuntimeProfile.PRODUCTION
    assert settings.authentication_ready is True


def test_config_module_exposes_versioned_environment_contract() -> None:
    """Deployment tooling should use the exact documented environment names."""

    assert config.API_TOKEN_ENV_VAR == "NEWSDOM_API_TOKEN"
    assert config.AUTH_MODE_ENV_VAR == "NEWSDOM_AUTH_MODE"
    assert config.RUNTIME_PROFILE_ENV_VAR == "NEWSDOM_RUNTIME_PROFILE"
