"""Regression contracts for bearer-token comparison length handling."""

from starlette.requests import Request

from newsdom_api.config import AuthenticationMode, RuntimeProfile, RuntimeSettings
from newsdom_api.main import _parse_access_failure, create_app


def _request(credentials: bytes) -> Request:
    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.PRODUCTION,
        api_token="secret",
    )
    application = create_app(settings, runtime_readiness_probe=lambda: True)
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/parse",
            "headers": [(b"authorization", b"Bearer " + credentials)],
            "app": application,
        }
    )


def test_length_mismatch_still_executes_expected_length_compare(monkeypatch) -> None:
    calls: list[tuple[bytes, bytes]] = []

    def capture(left: bytes, right: bytes) -> bool:
        calls.append((left, right))
        return False

    monkeypatch.setattr("newsdom_api.main.hmac.compare_digest", capture)

    response = _parse_access_failure(_request(b"x"))

    assert response is not None
    assert response.status_code == 401
    assert calls == [(b"secret", b"secret")]


def test_equal_length_mismatch_compares_supplied_and_expected_tokens(monkeypatch) -> None:
    calls: list[tuple[bytes, bytes]] = []

    def capture(left: bytes, right: bytes) -> bool:
        calls.append((left, right))
        return False

    monkeypatch.setattr("newsdom_api.main.hmac.compare_digest", capture)

    response = _parse_access_failure(_request(b"xxxxxx"))

    assert response is not None
    assert response.status_code == 401
    assert calls == [(b"xxxxxx", b"secret")]
