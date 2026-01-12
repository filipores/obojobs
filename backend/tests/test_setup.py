"""
Basic test to verify pytest setup works correctly.
This test will be replaced/expanded in INFRA-002.
"""


def test_pytest_setup():
    """Verify pytest is working."""
    assert True


def test_app_fixture(app):
    """Verify Flask test app fixture works."""
    assert app is not None
    assert app.config["TESTING"] is True


def test_client_fixture(client):
    """Verify test client fixture works."""
    assert client is not None
