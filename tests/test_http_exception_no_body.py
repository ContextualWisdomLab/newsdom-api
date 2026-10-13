from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException

from newsdom_api.main import app

def test_http_exception_no_body():
    @app.get("/test_no_body")
    def no_body_endpoint():
        raise HTTPException(status_code=204)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/test_no_body")
    assert response.status_code == 204
    assert response.text == ""
    assert "x-frame-options" in response.headers
