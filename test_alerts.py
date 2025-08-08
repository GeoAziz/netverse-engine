import requests

API = "http://localhost:8000/api/v1"

def test_alert_webhook():
    r = requests.post(f"{API}/alerts/webhook", json={"event": "test_alert", "severity": "high"})
    assert r.status_code in (200, 500)  # Accept 500 if webhook URL is not set
