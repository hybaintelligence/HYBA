"""
WebSocket telemetry endpoint for real-time updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import asyncio
import json
import logging

router = APIRouter()

# Active WebSocket connections
active_connections: Set[WebSocket] = set()

logger = logging.getLogger(__name__)


@router.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """
    WebSocket endpoint for real-time telemetry updates.
    Sends telemetry data every 5 seconds to connected clients.
    """
    await websocket.accept()
    active_connections.add(websocket)
    
    try:
        logger.info(f"WebSocket client connected. Active connections: {len(active_connections)}")
        
        while True:
            # Import here to avoid circular dependencies
            from hyba_genesis_api.api.routes import get_telemetry_data
            
            try:
                # Get current telemetry
                telemetry_data = await get_telemetry_data()
                
                # Send to client
                await websocket.send_json(telemetry_data)
                
                # Wait 5 seconds before next update
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error sending telemetry: {e}")
                # Try to send error message to client
                try:
                    await websocket.send_json({
                        "error": "Telemetry fetch failed",
                        "status": "degraded"
                    })
                except:
                    # Client likely disconnected
                    break
                
                await asyncio.sleep(5)
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.discard(websocket)
        logger.info(f"WebSocket client removed. Active connections: {len(active_connections)}")


async def broadcast_telemetry(data: dict):
    """
    Broadcast telemetry data to all connected WebSocket clients.
    Can be called from other parts of the application to push updates.
    """
    if not active_connections:
        return
    
    disconnected = set()
    
    for connection in active_connections:
        try:
            await connection.send_json(data)
        except Exception as e:
            logger.warning(f"Failed to send to WebSocket client: {e}")
            disconnected.add(connection)
    
    # Clean up disconnected clients
    for conn in disconnected:
        active_connections.discard(conn)
