import logging
from typing import Dict, List, Any
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio

logger = logging.getLogger("Core.SocketManager")

class ConnectionManager:
    def __init__(self):
        # Store active connections: {user_id: [WebSocket, ...]}
        # Allows multiple tabs for same user
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WS Connected: User {user_id} (Total: {len(self.active_connections[user_id])})")

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WS Disconnected: User {user_id}")

    async def broadcast(self, message: Dict[str, Any], user_id: int = None):
        """
        Broadcast message to connected clients.
        If user_id is provided, send only to that user.
        """
        json_msg = json.dumps(message)
        
        if user_id:
            if user_id in self.active_connections:
                # Send to all connections of this user
                for connection in self.active_connections[user_id]:
                    try:
                        await connection.send_text(json_msg)
                    except Exception as e:
                        logger.error(f"Error sending WS message to user {user_id}: {e}")
                        # Cleanup dead connection? Handled by disconnect mostly
        else:
            # Broadcast to ALL users (e.g. maintenance mode, global alerts)
            for uid, connections in self.active_connections.items():
                for connection in connections:
                    try:
                        await connection.send_text(json_msg)
                    except:
                        pass

socket_manager = ConnectionManager()
