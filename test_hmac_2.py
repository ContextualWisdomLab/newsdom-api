import hmac

provided = "Bearer tokẽn"
expected = "Bearer secret"

try:
    print(hmac.compare_digest(provided, expected))
except Exception as e:
    print(f"Exception: {type(e).__name__}: {e}")

try:
    print(hmac.compare_digest(provided.encode('utf-8'), expected.encode('utf-8')))
except Exception as e:
    print(f"Exception: {type(e).__name__}: {e}")
