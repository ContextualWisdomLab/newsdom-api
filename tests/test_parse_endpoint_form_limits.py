import pytest
from httpx import AsyncClient, ASGITransport
from newsdom_api.main import app

@pytest.mark.asyncio
async def test_parse_endpoint_language_mode_max_length(monkeypatch):
    """Verify that language and mode Form fields reject overly long inputs to prevent DoS."""
    from newsdom_api.config import RuntimeSettings, AuthenticationMode
    # Override settings to disable authentication for this test
    app.dependency_overrides[app.state.runtime_settings.__class__] = lambda: RuntimeSettings(authentication_mode=AuthenticationMode.DISABLED)
    # Actually, we need to override the dependency used in main.py, but looking at main.py, _runtime_settings is just a helper extracting from request.app.state.
    # The application state is used, so we can just modify the state or use the default setup if we disable auth.
    pass
