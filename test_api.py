#!/usr/bin/env python3
"""Backend API test script"""
import requests
import json

BASE_URL = "http://localhost:5002/api"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✓ Health check passed")

def test_login():
    """Test login and return token"""
    print("\n=== Testing Login ===")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "test@example.com", "password": "test123"}
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response keys: {data.keys()}")
    assert response.status_code == 200
    assert "access_token" in data
    print(f"✓ Login successful, token received")
    return data["access_token"]

def test_stats(token):
    """Test stats endpoint with JWT"""
    print("\n=== Testing Stats ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/stats", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✓ Stats endpoint passed")

def test_api_key_generation(token):
    """Test API key generation"""
    print("\n=== Testing API Key Generation ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/keys",
        headers=headers,
        json={"name": "Test Extension Key"}
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Generated key prefix: {data.get('api_key', '')[:12]}...")
    assert response.status_code == 201
    assert "api_key" in data
    print("✓ API key generation passed")
    return data["api_key"]

def test_api_key_list(token):
    """Test listing API keys"""
    print("\n=== Testing API Key List ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/keys", headers=headers)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Number of keys: {len(data)}")
    assert response.status_code == 200
    print("✓ API key list passed")

def test_documents_list(token):
    """Test documents endpoint"""
    print("\n=== Testing Documents List ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/documents", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✓ Documents list passed")

def test_templates_list(token):
    """Test templates endpoint"""
    print("\n=== Testing Templates List ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/templates", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✓ Templates list passed")

def test_applications_list(token):
    """Test applications endpoint"""
    print("\n=== Testing Applications List ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/applications", headers=headers)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total applications: {data.get('total', 0)}")
    assert response.status_code == 200
    print("✓ Applications list passed")

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("Backend API Test Suite")
        print("=" * 60)

        # Test unauthenticated endpoints
        test_health()

        # Login and get token
        token = test_login()

        # Test authenticated endpoints
        test_stats(token)
        test_documents_list(token)
        test_templates_list(token)
        test_applications_list(token)

        # Test API key endpoints
        test_api_key_list(token)
        api_key = test_api_key_generation(token)
        test_api_key_list(token)

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        print(f"\nGenerated API Key for extension testing:")
        print(f"{api_key}")
        print("\nYou can use this key to configure the Chrome Extension.")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        exit(1)
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to backend. Is it running on port 5002?")
        exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        exit(1)
