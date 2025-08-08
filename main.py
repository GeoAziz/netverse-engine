# src/backend/main.py

from fastapi import FastAPI
from api_gateway.endpoints import (
    auth,
    logs,
    websockets,
    control,
    proxy,
    ai_analysis,
    threat_feeds,
    siem,
    alerts,
    devices,
    control_device,
    users, # Added users endpoint
)
from core.config import settings
from services import firebase_admin
from services.message_queue import message_queue
from services.network_capture import network_capture
from starlette.middleware.cors import CORSMiddleware
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
# This needs to be called before the app starts to ensure it's available
firebase_admin.initialize_firebase_admin()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Zizo_NetVerse Backend Engine - Advanced Cybersecurity Command Deck",
    version="1.0.0"
)

# Set all CORS enabled origins
if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": "🚀 Welcome to the Zizo_NetVerse Backend Engine!",
        "status": "operational",
        "version": "1.0.0",
        "documentation": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "services": {
            "firebase": "connected" if firebase_admin._apps else "disconnected",
            "capture": "ready" if network_capture else "unavailable",
            "message_queue": "ready" if message_queue else "unavailable"
        }
    }


# Include routers from the api_gateway

app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["Authentication"])
app.include_router(logs.router, prefix=settings.API_V1_STR, tags=["Network Logs"])
app.include_router(websockets.router, prefix=settings.API_V1_STR, tags=["WebSocket Streaming"])
app.include_router(control.router, prefix=settings.API_V1_STR, tags=["Control"])
app.include_router(proxy.router, prefix=settings.API_V1_STR, tags=["Proxy"])
app.include_router(ai_analysis.router, prefix=settings.API_V1_STR, tags=["AI Analysis"])
app.include_router(threat_feeds.router, prefix=settings.API_V1_STR, tags=["Threat Feeds"])
app.include_router(siem.router, prefix=settings.API_V1_STR, tags=["SIEM Integration"])
app.include_router(alerts.router, prefix=settings.API_V1_STR, tags=["Alerts"])
app.include_router(devices.router, prefix=settings.API_V1_STR, tags=["Devices"])
app.include_router(control_device.router, prefix=settings.API_V1_STR, tags=["Device Control"])
app.include_router(users.router, prefix=settings.API_V1_STR, tags=["User Management"]) # Added users router


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    logger.info("🔥 Starting Zizo_NetVerse Backend Engine...")
    
    try:
        # Initialize message queue
        await message_queue.initialize()
        logger.info("✅ Message queue initialized")
        
        # Start packet capture if enabled in config
        if settings.CAPTURE_ENABLED:
            logger.info("🎯 Starting packet capture service...")
            # Start capture in background task
            asyncio.create_task(network_capture.start_capture())
        else:
            logger.info("📊 Packet capture disabled in configuration")
            
        logger.info("🚀 All services initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown."""
    logger.info("🛑 Shutting down Zizo_NetVerse Backend Engine...")
    
    try:
        # Stop packet capture
        if network_capture.is_capturing:
            network_capture.stop_capture()
            
        # Close message queue connection
        await message_queue.close()
        
        logger.info("✅ Clean shutdown completed")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
