from fastapi import APIRouter, HTTPException, Depends, Request
from services.proxy_engine import proxy_engine
import asyncio
import time
from .auth import require_admin # Import the admin role dependency

router = APIRouter()

RATE_LIMIT = {}
def rate_limiter(request: Request):
    ip = request.client.host
    now = time.time()
    window = 10  # seconds
    max_requests = 5
    if ip not in RATE_LIMIT:
        RATE_LIMIT[ip] = []
    RATE_LIMIT[ip] = [t for t in RATE_LIMIT[ip] if now - t < window]
    if len(RATE_LIMIT[ip]) >= max_requests:
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
    RATE_LIMIT[ip].append(now)

@router.post("/proxy/start", tags=["Proxy"], dependencies=[Depends(require_admin), Depends(rate_limiter)])
async def start_proxy():
    try:
        asyncio.create_task(proxy_engine.start())
        return {"status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/proxy/stop", tags=["Proxy"], dependencies=[Depends(require_admin), Depends(rate_limiter)])
async def stop_proxy():
    try:
        await proxy_engine.shutdown()
        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
