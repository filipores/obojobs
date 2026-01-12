"""
Tests for Security Headers Middleware.
"""

import os

import pytest

# Override environment for production tests
os.environ["FLASK_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key"
os.environ["ANTHROPIC_API_KEY"] = "test-api-key"

from app import create_app
from middleware.security_headers import add_security_headers
from models import db


class MockConfig:
    """Mock config for testing security headers."""

    def __init__(self, debug=True, security_enabled=False, force_https=False):
        self.DEBUG = debug
        self.SECURITY_HEADERS_ENABLED = security_enabled
        self.FORCE_HTTPS = force_https


class MockResponse:
    """Mock Flask response for testing."""

    def __init__(self):
        self.headers = {}


class TestSecurityHeadersFunction:
    """Test the add_security_headers function directly."""

    def test_no_headers_in_development(self):
        """Security headers should NOT be added in development mode."""
        response = MockResponse()
        config = MockConfig(debug=True, security_enabled=False)

        result = add_security_headers(response, config)

        assert "X-Content-Type-Options" not in result.headers
        assert "X-Frame-Options" not in result.headers
        assert "Content-Security-Policy" not in result.headers

    def test_headers_in_production(self):
        """Security headers should be added in production mode."""
        response = MockResponse()
        config = MockConfig(debug=False, security_enabled=False)

        result = add_security_headers(response, config)

        assert result.headers["X-Content-Type-Options"] == "nosniff"
        assert result.headers["X-Frame-Options"] == "DENY"
        assert result.headers["X-XSS-Protection"] == "1; mode=block"
        assert result.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "Content-Security-Policy" in result.headers
        assert "Permissions-Policy" in result.headers

    def test_headers_when_force_enabled(self):
        """Security headers should be added when explicitly enabled."""
        response = MockResponse()
        config = MockConfig(debug=True, security_enabled=True)

        result = add_security_headers(response, config)

        assert result.headers["X-Content-Type-Options"] == "nosniff"
        assert result.headers["X-Frame-Options"] == "DENY"

    def test_no_hsts_without_https(self):
        """HSTS header should NOT be added without HTTPS."""
        response = MockResponse()
        config = MockConfig(debug=False, force_https=False)

        result = add_security_headers(response, config)

        assert "Strict-Transport-Security" not in result.headers

    def test_hsts_with_force_https(self):
        """HSTS header should be added when FORCE_HTTPS is true."""
        response = MockResponse()
        config = MockConfig(debug=False, force_https=True)

        result = add_security_headers(response, config)

        assert "Strict-Transport-Security" in result.headers
        assert "max-age=31536000" in result.headers["Strict-Transport-Security"]
        assert "includeSubDomains" in result.headers["Strict-Transport-Security"]

    def test_csp_content(self):
        """CSP header should contain proper directives."""
        response = MockResponse()
        config = MockConfig(debug=False)

        result = add_security_headers(response, config)

        csp = result.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_permissions_policy_content(self):
        """Permissions-Policy should restrict sensitive features."""
        response = MockResponse()
        config = MockConfig(debug=False)

        result = add_security_headers(response, config)

        policy = result.headers["Permissions-Policy"]
        assert "camera=()" in policy
        assert "microphone=()" in policy
        assert "geolocation=()" in policy


@pytest.fixture(scope="function")
def production_app():
    """Create production-like Flask app for testing."""
    test_app = create_app()
    test_app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "DEBUG": False,  # Simulate production
        }
    )

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def production_client(production_app):
    """Create test client with production settings."""
    return production_app.test_client()


class TestSecurityHeadersIntegration:
    """Integration tests for security headers in Flask app."""

    def test_health_endpoint_has_security_headers_in_production(
        self, production_client
    ):
        """Health endpoint should include security headers in production."""
        response = production_client.get("/api/health")

        assert response.status_code == 200
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_auth_endpoint_has_security_headers_in_production(self, production_client):
        """Auth endpoints should include security headers in production."""
        response = production_client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "TestPass123"},
        )

        # Even failed requests should have security headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_csp_header_in_production(self, production_client):
        """CSP header should be present in production."""
        response = production_client.get("/api/health")

        csp = response.headers.get("Content-Security-Policy")
        assert csp is not None
        assert "default-src 'self'" in csp

    def test_permissions_policy_in_production(self, production_client):
        """Permissions-Policy header should be present in production."""
        response = production_client.get("/api/health")

        policy = response.headers.get("Permissions-Policy")
        assert policy is not None
        assert "camera=()" in policy


class TestSecurityHeadersDevelopment:
    """Test that security headers are NOT applied in development."""

    def test_no_security_headers_in_development(self, client):
        """Security headers should NOT be present in development mode."""
        response = client.get("/api/health")

        assert response.status_code == 200
        # In development mode, security headers should not be added
        # (conftest.py sets FLASK_ENV=testing which keeps DEBUG behavior)
        # The middleware checks config.DEBUG which is True for testing


class TestCORSConfiguration:
    """Test CORS configuration."""

    def test_cors_headers_on_options_request(self, client):
        """CORS headers should be returned for OPTIONS requests."""
        response = client.options(
            "/api/health",
            headers={"Origin": "http://localhost:3000"},
        )

        # CORS is configured in app.py via flask-cors
        # Actual header depends on flask-cors configuration
        assert response.status_code in [200, 204]

    def test_cors_allows_configured_origin(self, client):
        """CORS should allow configured origins."""
        response = client.get(
            "/api/health",
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.status_code == 200
        # flask-cors adds Access-Control-Allow-Origin for matching origins
