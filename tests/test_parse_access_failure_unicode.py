from unittest.mock import MagicMock
from newsdom_api.main import _parse_access_failure
from newsdom_api.config import RuntimeSettings, AuthenticationMode
from fastapi import Request
import json


def test_parse_access_failure_unicode_encode_error(monkeypatch):
    request = MagicMock(spec=Request)

    settings = RuntimeSettings(authentication_mode=AuthenticationMode.REQUIRED)
    # bypass config validation for token
    object.__setattr__(settings, "api_token", "\ud800")

    monkeypatch.setattr("newsdom_api.main._runtime_settings", lambda req: settings)
    monkeypatch.setattr(
        "newsdom_api.main._authorization_values", lambda req: [b"Bearer something"]
    )

    res = _parse_access_failure(request)
    assert res.status_code == 401
    assert json.loads(res.body) == {"detail": "Unauthorized"}
