from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, IPvAnyAddress
import subprocess
import time
from .auth import require_role

# Create the dependency instance for analyst or admin
require_analyst = require_role(["analyst", "admin"])

router = APIRouter()

RATE_LIMIT = {}
async def rate_limiter(req: Request):
    ip = req.client.host
    now = time.time()
    window = 10  # seconds
    max_requests = 5
    if ip not in RATE_LIMIT:
        RATE_LIMIT[ip] = []
    RATE_LIMIT[ip] = [t for t in RATE_LIMIT[ip] if now - t < window]
    if len(RATE_LIMIT[ip]) >= max_requests:
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
    RATE_LIMIT[ip].append(now)

class BlockIPRequest(BaseModel):
    ip: IPvAnyAddress

@router.post("/control/block-ip", tags=["Control"])
async def block_ip(
    request: BlockIPRequest,
    req: Request,
    user=Depends(require_analyst),
    _: None = Depends(rate_limiter)
):
    """
    Block an IP address using system firewall (iptables).
    """
    try:
        # Example for Linux with iptables
        result = subprocess.run([
            "sudo", "iptables", "-A", "INPUT", "-s", str(request.ip), "-j", "DROP"
        ], capture_output=True, text=True)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"iptables error: {result.stderr}")
        return {"status": "success", "message": f"Blocked IP {request.ip}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
