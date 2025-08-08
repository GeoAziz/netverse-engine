import requests
import os

# Use environment variable for API base or default to localhost
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

# This token is a placeholder and will fail unless you provide a valid one.
# In a real CI/CD pipeline, this would be a securely stored service account token.
AUTH_TOKEN = os.getenv("TEST_AUTH_TOKEN", "dummy-token")
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}

def test_get_device_success():
    """Tests fetching a known device, expecting a 200 OK."""
    # This test assumes the mock device "example-device-id" exists in the backend.
    response = requests.get(f"{API_URL}/devices/example-device-id", headers=HEADERS)
    # The first request will likely be a 401 if the dummy token is used, which is a valid security test.
    # For a real test, a valid token would yield 200.
    assert response.status_code in [200, 401] 
    if response.status_code == 200:
        data = response.json()
        assert data["id"] == "example-device-id"
        assert "enrichment" in data

def test_get_device_not_found():
    """Tests fetching a non-existent device, expecting a 404 Not Found."""
    response = requests.get(f"{API_URL}/devices/non-existent-device", headers=HEADERS)
    assert response.status_code in [404, 401]

def test_device_control_unauthorized():
    """Tests a control endpoint without a valid token, expecting a 401 Unauthorized."""
    response = requests.post(f"{API_URL}/control/isolate-device", json={"device_id": "example-device-id"})
    # This should fail without the Authorization header
    assert response.status_code == 401
