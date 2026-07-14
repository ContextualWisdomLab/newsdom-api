import hmac

try:
    hmac.compare_digest("Bearer token", "Bearer tøken")
    print("Success")
except Exception as e:
    print(f"Error: {e}")
