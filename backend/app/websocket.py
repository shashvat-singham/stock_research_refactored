"""
WebSocket connection manager for streaming logs.
"""
import json
import asyncio
from typing import Dict, Set, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger()


class ConnectionManager:
    """
    Manages WebSocket connections for streaming logs.
    Supports multiple clients per request_id.
    """
    
    def __init__(self):
        # Map of request_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, request_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        
        async with self._lock:
            if request_id not in self.active_connections:
                self.active_connections[request_id] = set()
            self.active_connections[request_id].add(websocket)
        
        logger.info("WebSocket connected", 
                   request_id=request_id,
                   total_connections=len(self.active_connections[request_id]))
    
    async def disconnect(self, websocket: WebSocket, request_id: str):
        """Remove a WebSocket connection."""
        async with self._lock:
            if request_id in self.active_connections:
                self.active_connections[request_id].discard(websocket)
                
                # Clean up empty sets
                if not self.active_connections[request_id]:
                    del self.active_connections[request_id]
        
        logger.info("WebSocket disconnected", 
                   request_id=request_id,
                   remaining_connections=len(self.active_connections.get(request_id, [])))
    
    async def broadcast(self, request_id: str, message: Dict[str, Any]):
        """
        Broadcast a message to all connections for a specific request_id.
        
        Args:
            request_id: The request ID to broadcast to
            message: The message dictionary to send
        """
        if request_id not in self.active_connections:
            return
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        message_json = json.dumps(message)
        
        # Get a copy of connections to avoid modification during iteration
        connections = list(self.active_connections[request_id])
        
        disconnected = []
        for connection in connections:
            try:
                await connection.send_text(message_json)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error("Error broadcasting message", 
                           request_id=request_id,
                           error=str(e))
                disconnected.append(connection)
        
        # Clean up disconnected connections
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    self.active_connections[request_id].discard(conn)
                
                if not self.active_connections[request_id]:
                    del self.active_connections[request_id]
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a specific WebSocket connection."""
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error("Error sending personal message", error=str(e))
    
    def get_connection_count(self, request_id: str) -> int:
        """Get the number of active connections for a request_id."""
        return len(self.active_connections.get(request_id, set()))
    
    async def close_all(self, request_id: str):
        """Close all connections for a specific request_id."""
        if request_id not in self.active_connections:
            return
        
        connections = list(self.active_connections[request_id])
        
        for connection in connections:
            try:
                await connection.close()
            except Exception as e:
                logger.error("Error closing connection", 
                           request_id=request_id,
                           error=str(e))
        
        async with self._lock:
            if request_id in self.active_connections:
                del self.active_connections[request_id]


# Global connection manager instance
connection_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return connection_manager
