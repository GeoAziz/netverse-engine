from fastapi import APIRouter, HTTPException

router = APIRouter()

# Mock device DB for demo
MOCK_DEVICES = {
    "example-device-id": {
        "id": "example-device-id",
        "ip": "192.168.1.10",
        "mac": "AA:BB:CC:DD:EE:FF",
        "os": "Ubuntu 22.04",
        "hostname": "SRV-03",
        "enrichment": {
            "geoip": {"country": "US", "city": "New York"},
            "virustotal": {"reputation": 0},
            "tor_exit_node": False
        },
        "alerts": ["Suspicious outbound connection blocked.", "Potential port scan detected."],
        "status": "online"
    }
}

@router.get("/devices/{device_id}")
async def get_device(device_id: str):
    device = MOCK_DEVICES.get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device
