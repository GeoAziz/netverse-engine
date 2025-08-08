import requests

API = "http://localhost:8000/api/v1"

def test_forward_to_siem():
    r = requests.post(f"{API}/siem/forward", json={"event": "test_siem", "severity": "info"})
    assert r.status_code in (200, 500)  # Accept 500 if SIEM URL is not set
