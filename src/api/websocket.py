from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio

from src.config.logging import logger
from src.utils.progress_tracker import progress_tracker
from src.utils.error_handler import VoiceCloneError

class WebSocketManager:
    """Manager for WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client connected: {client_id}")
    
    def disconnect(self, client_id: str) -> None:
        """Disconnect a WebSocket client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def send_message(self, client_id: str, message: Dict[str, Any]) -> None:
        """Send message to a specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {str(e)}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all connected clients"""
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {str(e)}")
                disconnected_clients.append(client_id)
        
        for client_id in disconnected_clients:
            self.disconnect(client_id)

# Create global instance
websocket_manager = WebSocketManager()

async def handle_websocket(websocket: WebSocket, client_id: str) -> None:
    """Handle WebSocket connection"""
    try:
        await websocket_manager.connect(websocket, client_id)
        
        # Register for task progress updates
        await progress_tracker.register_websocket(client_id, websocket)
        
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message["type"] == "subscribe_task":
                    task_id = message["task_id"]
                    await progress_tracker.register_websocket(task_id, websocket)
                
                elif message["type"] == "unsubscribe_task":
                    task_id = message["task_id"]
                    await progress_tracker.unregister_websocket(task_id)
                
                elif message["type"] == "ping":
                    await websocket.send_json({"type": "pong"})
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    
    finally:
        websocket_manager.disconnect(client_id)
        await progress_tracker.unregister_websocket(client_id)
