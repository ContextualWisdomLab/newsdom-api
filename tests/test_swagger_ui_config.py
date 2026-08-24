import pytest
from fastapi.testclient import TestClient

from newsdom_api.main import create_app

def test_swagger_ui_persist_authorization():
    app = create_app()
    assert app.swagger_ui_parameters is not None
    assert app.swagger_ui_parameters.get("persistAuthorization") is True
