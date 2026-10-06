import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from src.newsdom_api.main import app

client = TestClient(app, raise_server_exceptions=False)

def test_http_exception_headers():
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert response.headers.get("X-Content-Type-Options") == "nosniff"

def test_validation_error_headers():
    response = client.post("/parse", data={})
    assert response.status_code == 422
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
