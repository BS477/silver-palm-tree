import os
from fastapi.testclient import TestClient
import pytest

from service_a.app import app, startup, DB_PATH

SERVICE_A_URL = os.environ.get("SERVICE_A_URL", "localhost:8000")

client = TestClient(app)

def setup_module(module):
    # ensure a clean DB file
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    # trigger startup event
    startup()
    app.router.startup()

def teardown_module(module):
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

def test_post_and_get_result():
    payload = {"image_url": "http://example.org/image.jpg", "count": 3}
    r = client.post(SERVICE_A_URL+"/results", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["image_url"] == payload["image_url"]
    assert data["count"] == 3

    r2 = client.get("/results")
    assert r2.status_code == 200
    arr = r2.json()
    assert isinstance(arr, list)
    assert arr[0]["image_url"] == payload["image_url"]