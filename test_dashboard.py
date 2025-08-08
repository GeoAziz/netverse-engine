import requests
import os

# Assume the backend is running on localhost:8000
API_URL = os.getenv("API_URL", "http://localhost:8000")

def test_health_check():
    """Tests if the /health endpoint is operational and returns a healthy status."""
    response = requests.get(f"{API_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data
    assert "firebase" in data["services"]

def test_root_endpoint():
    """Tests the root endpoint for a welcome message."""
    response = requests.get(f"{API_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "🚀 Welcome to the Zizo_NetVerse Backend Engine!"
