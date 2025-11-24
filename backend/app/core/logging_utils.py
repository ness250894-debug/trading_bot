import logging
from typing import List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # If sending fails, we might want to remove the connection, 
                # but usually disconnect handles it.
                pass

# Global Manager Instance
manager = ConnectionManager()

class WebSocketLogHandler(logging.Handler):
    """
    Custom logging handler that sends logs to the WebSocket manager.
    It needs an asyncio loop to run the async broadcast method, 
    or we can use 'run_until_complete' if we are in a thread, 
    BUT since we are in FastAPI (async), we should use 'asyncio.create_task' 
    if we are in the same loop, or run_coroutine_threadsafe.
    """
    def __init__(self, manager: ConnectionManager):
        super().__init__()
        self.manager = manager
        import asyncio
        self.loop = asyncio.get_event_loop()

    def emit(self, record):
        try:
            msg = self.format(record)
            # We need to schedule the broadcast in the event loop
            import asyncio
            
            # Check if there is a running loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                asyncio.create_task(self.manager.broadcast(msg))
            else:
                # If we are in a separate thread (like the bot thread), 
                # we might not have access to the main loop easily without passing it.
                # For simplicity in this MVP, we will just print if we can't send, 
                # OR we rely on the fact that the bot will be running in a thread 
                # and we need to send to the MAIN loop.
                pass
                
        except Exception:
            self.handleError(record)

# Improved Handler for Thread Safety
class AsyncWebSocketLogHandler(logging.Handler):
    def __init__(self, manager: ConnectionManager, loop):
        super().__init__()
        self.manager = manager
        self.loop = loop

    def emit(self, record):
        try:
            msg = self.format(record)
            import asyncio
            # Schedule the coroutine in the main event loop
            asyncio.run_coroutine_threadsafe(self.manager.broadcast(msg), self.loop)
        except Exception:
            self.handleError(record)
