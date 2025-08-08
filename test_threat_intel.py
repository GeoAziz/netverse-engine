import requests

API = "http://localhost:8000/api/v1"

def test_get_threat_feeds():
    r = requests.get(f"{API}/threat-feeds/list")
    assert r.status_code == 200
    data = r.json()
    assert "feeds" in data

def test_upload_threat_feed():
    # This is a placeholder; in real tests, use a test file
    files = {'file': ('test-feed.txt', b'1.2.3.4\n5.6.7.8', 'text/plain')}
    r = requests.post(f"{API}/threat-feeds/upload", files=files)
    assert r.status_code == 200
    assert r.json()["status"] == "success"
