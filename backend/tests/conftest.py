"""
Pytest fixtures for obojobs backend tests.
"""

import os

import pytest

# Set test environment before importing app
os.environ["FLASK_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key"
os.environ["ANTHROPIC_API_KEY"] = "test-api-key"

from app import create_app
from models import User, db


@pytest.fixture(scope="function")
def app():
    """Create test Flask application with in-memory SQLite database."""
    test_app = create_app()
    test_app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "JWT_SECRET_KEY": "test-jwt-secret-key",
        }
    )

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Create test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture(scope="function")
def test_user(app):
    """Create a test user in the database."""
    with app.app_context():
        user = User(
            email="test@example.com",
            full_name="Test User",
        )
        user.set_password("TestPass123")  # Meets new password requirements
        db.session.add(user)
        db.session.commit()

        # Return user data (not the ORM object, to avoid detached session issues)
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "password": "TestPass123",
        }


@pytest.fixture(scope="function")
def auth_token(client, test_user):
    """Get JWT token for authenticated requests."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"],
        },
    )
    data = response.get_json()
    return data["access_token"]


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """Return headers with JWT authorization."""
    return {"Authorization": f"Bearer {auth_token}"}
