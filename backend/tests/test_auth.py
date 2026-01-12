"""
Tests for authentication endpoints.
"""


class TestRegister:
    """Tests for POST /api/auth/register"""

    def test_register_with_valid_data_returns_201(self, client):
        """Test successful registration with valid data."""
        response = client.post('/api/auth/register', json={
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'full_name': 'New User',
        })

        assert response.status_code == 201
        data = response.get_json()
        assert 'user' in data
        assert data['user']['email'] == 'newuser@example.com'

    def test_register_with_existing_email_returns_400(self, client, test_user):
        """Test registration fails with existing email."""
        response = client.post('/api/auth/register', json={
            'email': test_user['email'],  # Already exists from fixture
            'password': 'anotherpassword',
            'full_name': 'Duplicate User',
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestLogin:
    """Tests for POST /api/auth/login"""

    def test_login_with_correct_credentials_returns_200_and_token(self, client, test_user):
        """Test successful login returns 200 and access token."""
        response = client.post('/api/auth/login', json={
            'email': test_user['email'],
            'password': test_user['password'],
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'user' in data

    def test_login_with_wrong_password_returns_401(self, client, test_user):
        """Test login with wrong password returns 401."""
        response = client.post('/api/auth/login', json={
            'email': test_user['email'],
            'password': 'wrongpassword',
        })

        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data

    def test_login_with_nonexistent_email_returns_401(self, client):
        """Test login with non-existent email returns 401."""
        response = client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'anypassword',
        })

        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
