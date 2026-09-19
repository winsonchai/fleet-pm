"""Pytest configuration and shared fixtures for multi-tenant isolation testing."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import SessionLocal, Base, engine
from backend.seed import seed


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Ensure database schema is created and seeded before running tests."""
    Base.metadata.create_all(bind=engine)
    seed()


@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    return TestClient(app)


def _get_token(client: TestClient, email: str, password: str = "password123") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


@pytest.fixture
def super_admin_headers(client):
    token = _get_token(client, "admin@fleetpm.com", "admin123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def apex_admin_headers(client):
    token = _get_token(client, "alex@apex.com", "password123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def apex_driver_headers(client):
    token = _get_token(client, "dave@apex.com", "password123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def summit_admin_headers(client):
    token = _get_token(client, "elena@summit.com", "password123")
    return {"Authorization": f"Bearer {token}"}
