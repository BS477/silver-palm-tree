# tests/test_api.py
import os
import tempfile
import pytest
from typing import Dict
from datetime import datetime, timedelta

# Important: set DATABASE_URL before importing app so app uses test DB
test_db_file = os.path.join(tempfile.gettempdir(), "test_baza.db")
os.environ["DATABASE_URL"] = f"sqlite:///{test_db_file}"
# set a known secret for tests
os.environ["JWT_SECRET"] = "testsecret123"

# Now import app and db setup
from setup_db import create_tables, SessionLocal
from app import app, create_access_token, get_password_hash, JWT_SECRET, JWT_ALGORITHM
from models import User

from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def prepare_db():
    # remove db file if exists
    try:
        os.remove(test_db_file)
    except FileNotFoundError:
        pass
    # create tables
    create_tables()
    # create an admin and a normal user
    db = SessionLocal()
    try:
        admin = User(username="admin", full_name="Admin User", hashed_password=get_password_hash("adminpass"), roles="ROLE_ADMIN,ROLE_USER")
        normal = User(username="bob", full_name="Bob User", hashed_password=get_password_hash("bobpass"), roles="ROLE_USER")
        db.add(admin)
        db.add(normal)
        db.commit()
    finally:
        db.close()
    yield
    # teardown
    try:
        os.remove(test_db_file)
    except FileNotFoundError:
        pass

client = TestClient(app)

def login_and_get_token(username: str, password: str) -> str:
    data = {"username": username, "password": password}
    resp = client.post("/login", data=data)
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["access_token"]

def test_login_success_and_failure():
    # correct login
    resp = client.post("/login", data={"username": "admin", "password": "adminpass"})
    assert resp.status_code == 200
    token = resp.json().get("access_token")
    assert token and isinstance(token, str)
    # wrong credentials
    resp2 = client.post("/login", data={"username": "admin", "password": "wrong"})
    assert resp2.status_code == 401

def test_create_user_with_admin_and_without():
    admin_token = login_and_get_token("admin", "adminpass")
    # admin can create user
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"username": "newuser", "password": "newpass", "full_name": "New User", "roles": ["ROLE_USER"]}
    resp = client.post("/users", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["username"] == "newuser"
    assert "id" in data
    # non-admin cannot create
    bob_token = login_and_get_token("bob", "bobpass")
    headers_bob = {"Authorization": f"Bearer {bob_token}"}
    resp2 = client.post("/users", json={"username": "x","password":"x"}, headers=headers_bob)
    assert resp2.status_code == 403

def test_user_details_with_and_without_token():
    token = login_and_get_token("admin", "adminpass")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/user_details", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["sub"] == "admin"
    assert "ROLE_ADMIN" in data["roles"]
    # missing token
    resp2 = client.get("/user_details")
    assert resp2.status_code == 401
