"""
WebSocket Manager for real-time updates
"""

from fastapi import WebSocket
from typing import List, Dict, Set
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manage WebSocket connections and real-time data broadcasting"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def handle_message(self, websocket: WebSocket, message: str):
        """Handle incoming messages from clients"""
        try:
            data = json.loads(message)
            action = data.get("action")
            
            if action == "subscribe":
                symbols = data.get("symbols", [])
                self.subscriptions[websocket].update(symbols)
                await websocket.send_json({
                    "type": "subscription_success",
                    "symbols": list(self.subscriptions[websocket])
                })
            
            elif action == "unsubscribe":
                symbols = data.get("symbols", [])
                self.subscriptions[websocket].difference_update(symbols)
                await websocket.send_json({
                    "type": "unsubscription_success",
                    "symbols": list(self.subscriptions[websocket])
                })
        
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {str(e)}")
    
    async def send_to_subscribers(self, symbol: str, data: dict):
        """Send data only to clients subscribed to a symbol"""
        for connection in self.active_connections:
            if symbol in self.subscriptions.get(connection, set()):
                try:
                    await connection.send_json({
                        "type": "tick",
                        "symbol": symbol,
                        "data": data
                    })
                except Exception as e:
                    logger.error(f"Error sending to subscriber: {str(e)}")
