import requests

API = "http://localhost:8000/api/v1"

def test_analyze_packet():
    r = requests.post(f"{API}/ai/analyze-packet", json={"packet_data": {"source_ip": "8.8.8.8"}})
    assert r.status_code == 200
    assert "analysis" in r.json()

def test_analyze_incident():
    r = requests.post(f"{API}/ai/analyze-incident", json={"incident_data": {"incident_id": "test-incident"}})
    assert r.status_code == 200
    assert "analysis" in r.json()
