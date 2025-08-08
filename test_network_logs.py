import requests

API = "http://localhost:8000/api/v1"

def test_get_network_logs():
    r = requests.get(f"{API}/logs/network")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_get_logs_summary():
    r = requests.get(f"{API}/logs/summary")
    assert r.status_code == 200
    assert "total_packets" in r.json() or "summary" in r.json()
