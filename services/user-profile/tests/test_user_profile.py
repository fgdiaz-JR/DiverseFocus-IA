"""
Unit tests for the User Profile service.
Tests CRUD operations on users and tasks using an in-memory SQLite database.
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.main import Base, app, engine, AsyncSessionLocal


# Override DB with in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
def override_db(monkeypatch):
    """Replace the module-level engine and session factory with test versions."""
    import src.main as svc
    monkeypatch.setattr(svc, "engine", test_engine)
    monkeypatch.setattr(svc, "AsyncSessionLocal", TestSessionLocal)


@pytest.fixture(autouse=True)
def setup_tables(override_db):
    """Create all tables before each test, drop after."""
    import asyncio

    async def _create():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _drop():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.get_event_loop().run_until_complete(_create())
    yield
    asyncio.get_event_loop().run_until_complete(_drop())


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_profile_creates_user_on_first_access():
    response = client.get("/profile/user-test-001")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user-test-001"
    assert data["username"] == "user-test-001"
    assert data["preferences"] == {}


def test_get_profile_returns_existing_user():
    # First access creates the user
    client.get("/profile/user-abc")
    # Second access should return the same user
    response = client.get("/profile/user-abc")
    assert response.status_code == 200
    assert response.json()["user_id"] == "user-abc"


def test_update_profile_username():
    client.get("/profile/user-update")
    response = client.put(
        "/profile/user-update",
        json={"username": "Alice", "email": "alice@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "Alice"
    assert data["email"] == "alice@example.com"


def test_update_profile_preferences():
    client.get("/profile/user-prefs")
    client.put(
        "/profile/user-prefs",
        json={"preferences": {"high_contrast": True, "font_size": "large"}},
    )
    response = client.put(
        "/profile/user-prefs",
        json={"preferences": {"simplified_language": True}},
    )
    assert response.status_code == 200
    prefs = response.json()["preferences"]
    # Preferences should be merged, not replaced
    assert prefs["high_contrast"] is True
    assert prefs["simplified_language"] is True
    assert prefs["font_size"] == "large"


def test_create_task():
    response = client.post(
        "/tasks",
        json={
            "user_id": "user-tasks",
            "task_type": "simplify",
            "content": "Original complex text",
            "result": "Simplified text",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "user-tasks"
    assert data["task_type"] == "simplify"
    assert data["result"] == "Simplified text"
    assert "id" in data


def test_get_tasks_empty():
    response = client.get("/tasks/user-no-tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_get_tasks_returns_history():
    for i in range(3):
        client.post(
            "/tasks",
            json={
                "user_id": "user-history",
                "task_type": "transcribe",
                "content": f"Audio clip {i}",
                "result": f"Transcript {i}",
            },
        )

    response = client.get("/tasks/user-history")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 3
