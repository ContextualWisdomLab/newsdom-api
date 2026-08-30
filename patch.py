import re

with open("src/newsdom_api/main.py", "r") as f:
    content = f.read()

search = """    scheme, separator, credentials = provided.partition(b" ")
    if separator != b" " or scheme.lower() != b"bearer" or not credentials:
        return _unauthorized_response()

    token_bytes = token.encode("utf-8")
    is_valid = len(credentials) == len(token_bytes)
    if not is_valid:
        hmac.compare_digest(credentials, credentials)
    elif not hmac.compare_digest(credentials, token_bytes):
        is_valid = False

    if not is_valid:
        return _unauthorized_response()
    return None"""

replace = """    scheme, separator, credentials = provided.partition(b" ")
    if separator != b" " or scheme.lower() != b"bearer" or not credentials:
        return _unauthorized_response()

    verifier = request.app.state.api_token_verifier
    if verifier is None:
        return JSONResponse(
            status_code=503,
            content={"detail": SERVICE_UNAVAILABLE_DETAIL},
        )

    is_valid = len(credentials) == len(verifier)
    if not is_valid:
        hmac.compare_digest(credentials, credentials)
    elif not hmac.compare_digest(credentials, verifier):
        is_valid = False

    if not is_valid:
        return _unauthorized_response()
    return None"""

if search in content:
    with open("src/newsdom_api/main.py", "w") as f:
        f.write(content.replace(search, replace))
    print("Patched main.py successfully")
else:
    print("Search block not found in main.py")

with open("src/newsdom_api/main.py", "r") as f:
    content = f.read()

search2 = """    application.state.runtime_settings = application_settings
    application.state.runtime_readiness_probe = (
        runtime_readiness_probe or mineru_runtime_available
    )
    application.middleware("http")(security_boundary_middleware)"""

replace2 = """    application.state.runtime_settings = application_settings

    verifier = None
    if application_settings.api_token is not None:
        verifier = application_settings.api_token.encode("utf-8")
    application.state.api_token_verifier = verifier

    application.state.runtime_readiness_probe = (
        runtime_readiness_probe or mineru_runtime_available
    )
    application.middleware("http")(security_boundary_middleware)"""

if search2 in content:
    with open("src/newsdom_api/main.py", "w") as f:
        f.write(content.replace(search2, replace2))
    print("Patched main.py create_app successfully")
else:
    print("Search block 2 not found in main.py")
