from fastapi import APIRouter, HTTPException, Request
import requests

router = APIRouter()

SIEM_WEBHOOK_URL = "https://your-siem.example.com/webhook"  # Set in config/env in production

@router.post("/siem/forward", tags=["SIEM Integration"])
async def forward_to_siem(request: Request):
    try:
        data = await request.json()
        resp = requests.post(SIEM_WEBHOOK_URL, json=data)
        if resp.status_code == 200:
            return {"status": "forwarded"}
        else:
            raise HTTPException(status_code=500, detail=f"SIEM error: {resp.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
