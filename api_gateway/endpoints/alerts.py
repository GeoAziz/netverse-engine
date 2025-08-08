from fastapi import APIRouter, HTTPException, Request
import requests

router = APIRouter()

WEBHOOK_URL = "https://your-alert-webhook.example.com"  # Set in config/env in production

@router.post("/alerts/webhook", tags=["Alerts"])
async def trigger_webhook_alert(request: Request):
    try:
        data = await request.json()
        resp = requests.post(WEBHOOK_URL, json=data)
        if resp.status_code == 200:
            return {"status": "alert_sent"}
        else:
            raise HTTPException(status_code=500, detail=f"Webhook error: {resp.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
