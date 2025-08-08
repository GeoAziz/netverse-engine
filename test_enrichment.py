import requests

API = "http://localhost:8000/api/v1"

def test_enrich_ip():
    # This assumes an endpoint exists to directly enrich an IP (if not, test via device or packet API)
    r = requests.post(f"{API}/ai/analyze-packet", json={"packet_data": {"source_ip": "8.8.8.8"}})
    assert r.status_code == 200
    data = r.json()
    assert "analysis" in data
