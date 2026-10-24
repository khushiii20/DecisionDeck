"""
Tests for Phase 1: Foundation and Visual Prototype
Verifies routes, static file serving, and basic HTML structure.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["app"] == "DecisionDeck"

def test_landing_page_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "DecisionDeck" in response.text
    assert "Make choices with clarity" in response.text
    assert "Career Growth" in response.text

def test_static_css_serves_design_tokens():
    response = client.get("/static/css/style.css")
    assert response.status_code == 200
    assert "#0B1020" in response.text  # Deep navy background token
    assert "#3B82F6" in response.text  # Electric blue accent token

def test_auth_and_app_pages_serve():
    for path in ["/login.html", "/register.html", "/dashboard.html", "/decision.html"]:
        response = client.get(path)
        assert response.status_code == 200
        assert "DecisionDeck" in response.text
