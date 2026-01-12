"""
Tests for health endpoint.
"""


def test_health_endpoint_returns_200(client):
    """Test that GET /api/health returns 200 status."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert "message" in data
