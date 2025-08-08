import requests

API = "http://localhost:8000/api/v1"

def test_start_proxy():
    r = requests.post(f"{API}/proxy/start")
    assert r.status_code == 200
    assert r.json()["status"] == "started"

def test_stop_proxy():
    r = requests.post(f"{API}/proxy/stop")
    assert r.status_code == 200
    assert r.json()["status"] == "stopped"
