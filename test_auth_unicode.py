import pytest
from fastapi.testclient import TestClient

from newsdom_api import config
from newsdom_api.config import API_TOKEN_ENV_VAR
from newsdom_api.main import app

_PDF_FILES = {"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")}

def fake_parse_pdf(file_path, filename, **kwargs):
    return {"document_id": "fixture", "pages": []}

import newsdom_api.main
newsdom_api.main._validate_pdf_structure = lambda _: None
newsdom_api.main.parse_pdf = fake_parse_pdf

client = TestClient(app)

import os
os.environ[API_TOKEN_ENV_VAR] = "s3cret-token"

response = client.post(
    "/parse",
    files=_PDF_FILES,
    headers={"Authorization": "Bearer tøken".encode("utf-8")},
)
print(f"Status Code: {response.status_code}")
if response.status_code != 200:
    print(f"Response: {response.json()}")
