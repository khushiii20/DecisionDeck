"""
Pytest Fixtures for DecisionDeck Backend Integration Tests
Configures an isolated SQLite database and test API clients.
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app

# Isolated SQLite test database
TEST_DB_FILE = "./test_decisiondeck.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Creates tables before tests run and cleans up afterwards."""
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass


@pytest.fixture
def client():
    """Provides a TestClient for testing unauthenticated or general requests."""
    with TestClient(app) as test_client:
        yield test_client


def get_authenticated_client(email: str, password: str = "Password123!"):
    test_client = TestClient(app)
    # Attempt register first
    reg_res = test_client.post("/api/auth/register", json={"email": email, "password": password})
    if reg_res.status_code == 201:
        token = reg_res.json()["access_token"]
    else:
        # Otherwise log in
        login_res = test_client.post("/api/auth/login", json={"email": email, "password": password})
        token = login_res.json()["access_token"]
    test_client.headers["Authorization"] = f"Bearer {token}"
    return test_client


@pytest.fixture
def user_a_client():
    """Registers User A and returns a TestClient with User A's Authorization header."""
    client = get_authenticated_client("user_a@example.com")
    yield client
    client.close()


@pytest.fixture
def user_b_client():
    """Registers User B and returns a TestClient with User B's Authorization header."""
    client = get_authenticated_client("user_b@example.com")
    yield client
    client.close()
