from fastapi import APIRouter, UploadFile, File, HTTPException
import os

router = APIRouter()

THREAT_FEED_DIR = "threat_feeds/"
os.makedirs(THREAT_FEED_DIR, exist_ok=True)

@router.post("/threat-feeds/upload", tags=["Threat Feeds"])
async def upload_threat_feed(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(THREAT_FEED_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threat-feeds/list", tags=["Threat Feeds"])
async def list_threat_feeds():
    try:
        files = os.listdir(THREAT_FEED_DIR)
        return {"feeds": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
