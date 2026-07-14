import asyncio
from fastapi import Header
from fastapi.testclient import TestClient
from src.newsdom_api.main import app

def fake_get_api_token():
    return "secret"

import src.newsdom_api.main
src.newsdom_api.main.get_api_token = fake_get_api_token

client = TestClient(app)

response = client.post(
    "/parse",
    headers={"Authorization": "Bearer tøken"},
    files={"file": ("test.pdf", b"%PDF-test", "application/pdf")}
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
