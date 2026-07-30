import pytest
from fastapi import HTTPException
from newsdom_api.main import require_authorization
import os
from unittest.mock import patch


@patch.dict(os.environ, {"NEWSDOM_API_TOKEN": "test-secret"})
def test_require_authorization_non_ascii():
    """Test that require_authorization handles non-ASCII characters securely and returns 401 instead of crashing."""
    # hmac.compare_digest raised TypeError with non-ASCII chars
    with pytest.raises(HTTPException) as excinfo:
        require_authorization(authorization="Bearer test🚀")

    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Unauthorized"
