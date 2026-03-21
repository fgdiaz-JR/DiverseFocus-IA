"""
Unit tests for the API Gateway.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app, DEMO_USERS, pwd_context

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "api-gateway"


def test_login_success():
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "demo", "password": "demo1234"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "demo", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_unknown_user():
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "nobody", "password": "anything"},
    )
    assert response.status_code == 401


def test_protected_route_without_token():
    response = client.get("/api/v1/user/profile")
    assert response.status_code == 403


def test_protected_route_invalid_token():
    response = client.get(
        "/api/v1/user/profile",
        headers={"Authorization": "Bearer not.a.valid.token"},
    )
    assert response.status_code == 401


def _get_valid_token() -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "demo", "password": "demo1234"},
    )
    return resp.json()["access_token"]


def test_simplify_proxies_with_valid_token(httpx_mock):
    """Verify the simplify route proxies to ai-inference when authenticated."""
    httpx_mock.add_response(
        method="POST",
        url="http://ai-inference:8001/simplify",
        json={"simplified_text": "Easy version"},
        status_code=200,
    )
    token = _get_valid_token()
    response = client.post(
        "/api/v1/ai/simplify",
        json={"text": "Complex text", "level": "easy"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["simplified_text"] == "Easy version"
