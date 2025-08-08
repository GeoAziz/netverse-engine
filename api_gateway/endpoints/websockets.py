# src/backend/api_gateway/endpoints/websockets.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import List, Dict, Any
import json
import asyncio
import logging
from services.message_queue import message_queue
from api_gateway.endpoints.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections for real-time log streaming."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.authenticated_connections: Dict[WebSocket, dict] = {}
    
    async def connect(self, websocket: WebSocket, user_data: dict):
        """Accept a new WebSocket connection and authenticate."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.authenticated_connections[websocket] = user_data
        logger.info(f"WebSocket connected for user: {user_data.get('email', 'unknown')}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.authenticated_connections:
            del self.authenticated_connections[websocket]
        logger.info("WebSocket disconnected")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected WebSockets."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


# Global connection manager
manager = ConnectionManager()


async def authenticate_websocket(websocket: WebSocket, token: str = None) -> dict:
    """
    Authenticate WebSocket connection using Firebase token.
    
    Args:
        websocket: WebSocket connection
        token: Firebase ID token
        
    Returns:
        User data if authenticated
        
    Raises:
        WebSocketException if authentication fails
    """
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        raise HTTPException(status_code=4001, detail="Missing authentication token")
    
    try:
        # Use the same authentication logic as the REST endpoints
        from firebase_admin import auth
        decoded_token = auth.verify_id_token(token, check_revoked=True)
        return decoded_token
    except Exception as e:
        await websocket.close(code=4003, reason="Invalid authentication token")
        raise HTTPException(status_code=4003, detail="Invalid authentication token")


@router.websocket("/ws/logs/network")
async def websocket_network_logs(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time network log streaming.
    
    Client should connect with: ws://localhost:8000/api/v1/ws/logs/network?token=<firebase_token>
    """
    try:
        # Authenticate the WebSocket connection
        user_data = await authenticate_websocket(websocket, token)
        await manager.connect(websocket, user_data)
        
        # Send initial connection confirmation
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "status": "connected",
                "message": f"Welcome to Zizo_NetVerse live stream, {user_data.get('email', 'Agent')}"
            }),
            websocket
        )
        
        # Set up Redis subscription for real-time packet data
        async def packet_handler(packet_data: Dict[str, Any]):
            """Handle incoming packet data from Redis and forward to WebSocket."""
            message = json.dumps({
                "type": "network_log",
                "data": packet_data,
                "timestamp": packet_data.get("timestamp")
            })
            await manager.send_personal_message(message, websocket)
        
        # Subscribe to the network packets channel
        subscription_task = asyncio.create_task(
            message_queue.subscribe_to_channel("network_packets", packet_handler)
        )
        
        # Keep the connection alive and handle client messages
        try:
            while True:
                # Wait for messages from client (like filter requests)
                data = await websocket.receive_text()
                client_message = json.loads(data)
                
                if client_message.get("type") == "ping":
                    await manager.send_personal_message(
                        json.dumps({"type": "pong", "timestamp": client_message.get("timestamp")}),
                        websocket
                    )
                elif client_message.get("type") == "filter":
                    # Handle filter requests (future enhancement)
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "filter_ack",
                            "message": "Filter settings received (not yet implemented)"
                        }),
                        websocket
                    )
                
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        finally:
            # Cancel the subscription task
            subscription_task.cancel()
            manager.disconnect(websocket)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in manager.active_connections:
            manager.disconnect(websocket)


@router.websocket("/ws/system/status")
async def websocket_system_status(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time system status updates.
    
    Provides capture statistics, system health, and other operational data.
    """
    try:
        user_data = await authenticate_websocket(websocket, token)
        await manager.connect(websocket, user_data)
        
        from services.network_capture import network_capture
        
        while True:
            # Send system status every 5 seconds
            status_data = {
                "type": "system_status",
                "data": {
                    "capture_stats": network_capture.get_capture_stats(),
                    "timestamp": asyncio.get_event_loop().time(),
                    "active_connections": len(manager.active_connections)
                }
            }
            
            await manager.send_personal_message(json.dumps(status_data), websocket)
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        logger.info("System status WebSocket disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"System status WebSocket error: {e}")
        if websocket in manager.active_connections:
            manager.disconnect(websocket)
