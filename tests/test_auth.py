"""
Authentication & Authorization Integration Tests
Verifies registration, login, logout, token verification, and security rejections.
"""

def test_register_success(client):
    res = client.post("/api/auth/register", json={
        "email": "newuser@example.com",
        "password": "SecurePassword123"
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "newuser@example.com"
    assert "id" in data["user"]
    # Verify password hash is NEVER exposed
    assert "password" not in data["user"]
    assert "hashed_password" not in data["user"]


def test_register_duplicate_email_fails(client):
    res = client.post("/api/auth/register", json={
        "email": "duplicate@example.com",
        "password": "SecurePassword123"
    })
    assert res.status_code == 201

    # Second attempt with same email
    res2 = client.post("/api/auth/register", json={
        "email": "duplicate@example.com",
        "password": "AnotherPassword456"
    })
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_register_validation_errors(client):
    # Password too short (< 8 chars)
    res_short = client.post("/api/auth/register", json={
        "email": "valid@example.com",
        "password": "short"
    })
    assert res_short.status_code == 422

    # Invalid email format
    res_bad_email = client.post("/api/auth/register", json={
        "email": "not-an-email",
        "password": "ValidPassword123"
    })
    assert res_bad_email.status_code == 422


def test_login_success(client):
    # Register first
    client.post("/api/auth/register", json={
        "email": "loginuser@example.com",
        "password": "MySecretPassword123"
    })

    # Login
    res = client.post("/api/auth/login", json={
        "email": "loginuser@example.com",
        "password": "MySecretPassword123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "loginuser@example.com"


def test_login_invalid_credentials(client):
    # Wrong password
    res_wrong_pw = client.post("/api/auth/login", json={
        "email": "loginuser@example.com",
        "password": "WrongPassword!"
    })
    assert res_wrong_pw.status_code == 401
    assert "Invalid email or password" in res_wrong_pw.json()["detail"]

    # Nonexistent user
    res_nonexistent = client.post("/api/auth/login", json={
        "email": "ghost@example.com",
        "password": "SomePassword123"
    })
    assert res_nonexistent.status_code == 401
    assert "Invalid email or password" in res_nonexistent.json()["detail"]


def test_get_me_endpoint(user_a_client, client):
    # Authenticated user
    res = user_a_client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json()["email"] == "user_a@example.com"

    # Unauthenticated request
    res_unauth = client.get("/api/auth/me")
    assert res_unauth.status_code == 401


def test_logout_endpoint(user_a_client):
    res = user_a_client.post("/api/auth/logout")
    assert res.status_code == 200
    assert "Logged out" in res.json()["message"]
