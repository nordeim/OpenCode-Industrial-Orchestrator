"""
INDUSTRIAL WEBSOCKET CONNECTION MANAGER
Thread-safe WebSocket connection management with room-based broadcasting.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Metadata for a WebSocket connection."""
    
    client_id: str
    websocket: WebSocket
    rooms: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0


class ConnectionManager:
    """
    Industrial-grade WebSocket connection manager.
    
    Features:
    - Thread-safe connection tracking
    - Room-based message routing
    - Heartbeat monitoring
    - Broadcast and personal messaging
    - Graceful disconnection handling
    """
    
    def __init__(self, heartbeat_interval: int = 30):
        self._connections: Dict[str, ConnectionInfo] = {}
        self._rooms: Dict[str, Set[str]] = {}  # room_name -> client_ids
        self._lock = asyncio.Lock()
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_task: Optional[asyncio.Task] = None
    
    @property
    def connection_count(self) -> int:
        """Get current number of active connections."""
        return len(self._connections)
    
    @property
    def room_count(self) -> int:
        """Get current number of active rooms."""
        return len(self._rooms)
    
    async def connect(
        self,
        websocket: WebSocket,
        client_id: Optional[str] = None,
        rooms: Optional[List[str]] = None
    ) -> str:
        """
        Accept and register a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            client_id: Optional client identifier (generated if not provided)
            rooms: Optional list of rooms to join
            
        Returns:
            The client_id for this connection
        """
        await websocket.accept()
        
        client_id = client_id or str(uuid4())
        rooms = rooms or []
        
        async with self._lock:
            connection = ConnectionInfo(
                client_id=client_id,
                websocket=websocket,
                rooms=set(rooms)
            )
            self._connections[client_id] = connection
            
            # Add to rooms
            for room in rooms:
                if room not in self._rooms:
                    self._rooms[room] = set()
                self._rooms[room].add(client_id)
        
        logger.info(
            f"WebSocket connected: {client_id} | "
            f"Rooms: {rooms} | "
            f"Total connections: {self.connection_count}"
        )
        
        # Send welcome message
        await self._send_to_websocket(websocket, {
            "type": "connection.established",
            "payload": {
                "client_id": client_id,
                "rooms": rooms,
                "server_time": datetime.utcnow().isoformat()
            }
        })
        
        return client_id
    
    async def disconnect(self, client_id: str) -> None:
        """
        Remove a connection and clean up room memberships.
        
        Args:
            client_id: The client to disconnect
        """
        async with self._lock:
            if client_id not in self._connections:
                return
            
            connection = self._connections.pop(client_id)
            
            # Remove from all rooms
            for room in connection.rooms:
                if room in self._rooms:
                    self._rooms[room].discard(client_id)
                    if not self._rooms[room]:
                        del self._rooms[room]
        
        logger.info(
            f"WebSocket disconnected: {client_id} | "
            f"Duration: {(datetime.utcnow() - connection.connected_at).seconds}s | "
            f"Messages: {connection.message_count}"
        )
    
    async def join_room(self, client_id: str, room: str) -> bool:
        """
        Add a client to a room.
        
        Args:
            client_id: The client to add
            room: The room to join
            
        Returns:
            True if joined successfully
        """
        async with self._lock:
            if client_id not in self._connections:
                return False
            
            self._connections[client_id].rooms.add(room)
            
            if room not in self._rooms:
                self._rooms[room] = set()
            self._rooms[room].add(client_id)
        
        logger.debug(f"Client {client_id} joined room: {room}")
        return True
    
    async def leave_room(self, client_id: str, room: str) -> bool:
        """
        Remove a client from a room.
        
        Args:
            client_id: The client to remove
            room: The room to leave
            
        Returns:
            True if left successfully
        """
        async with self._lock:
            if client_id not in self._connections:
                return False
            
            self._connections[client_id].rooms.discard(room)
            
            if room in self._rooms:
                self._rooms[room].discard(client_id)
                if not self._rooms[room]:
                    del self._rooms[room]
        
        logger.debug(f"Client {client_id} left room: {room}")
        return True
    
    async def broadcast(
        self,
        message: dict,
        room: Optional[str] = None,
        exclude: Optional[List[str]] = None
    ) -> int:
        """
        Broadcast a message to all clients or a specific room.
        
        Args:
            message: The message to send
            room: Optional room to target (all clients if None)
            exclude: Optional list of client_ids to exclude
            
        Returns:
            Number of clients that received the message
        """
        exclude = exclude or []
        sent_count = 0
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        async with self._lock:
            if room:
                client_ids = self._rooms.get(room, set())
            else:
                client_ids = set(self._connections.keys())
            
            targets = [
                cid for cid in client_ids
                if cid not in exclude
            ]
        
        # Send to all targets (outside lock to avoid blocking)
        for client_id in targets:
            if await self.send_personal(client_id, message):
                sent_count += 1
        
        logger.debug(
            f"Broadcast to {sent_count} clients | "
            f"Room: {room or 'all'} | "
            f"Type: {message.get('type', 'unknown')}"
        )
        
        return sent_count
    
    async def send_personal(self, client_id: str, message: dict) -> bool:
        """
        Send a message to a specific client.
        
        Args:
            client_id: The target client
            message: The message to send
            
        Returns:
            True if sent successfully
        """
        async with self._lock:
            if client_id not in self._connections:
                return False
            connection = self._connections[client_id]
        
        try:
            await self._send_to_websocket(connection.websocket, message)
            
            async with self._lock:
                if client_id in self._connections:
                    self._connections[client_id].message_count += 1
            
            return True
        except Exception as e:
            logger.warning(f"Failed to send to {client_id}: {e}")
            await self.disconnect(client_id)
            return False
    
    async def _send_to_websocket(self, websocket: WebSocket, message: dict) -> None:
        """Send JSON message to a websocket."""
        await websocket.send_json(message)
    
    async def start_heartbeat(self) -> None:
        """Start the heartbeat monitoring loop."""
        if self._heartbeat_task is not None:
            return
        
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"Heartbeat started with {self._heartbeat_interval}s interval")
    
    async def stop_heartbeat(self) -> None:
        """Stop the heartbeat monitoring loop."""
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            logger.info("Heartbeat stopped")
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat pings to all connections."""
        while True:
            await asyncio.sleep(self._heartbeat_interval)
            
            heartbeat_message = {
                "type": "heartbeat",
                "payload": {
                    "server_time": datetime.utcnow().isoformat()
                }
            }
            
            await self.broadcast(heartbeat_message)
    
    async def update_heartbeat(self, client_id: str) -> None:
        """Update last heartbeat time for a client."""
        async with self._lock:
            if client_id in self._connections:
                self._connections[client_id].last_heartbeat = datetime.utcnow()
    
    def get_room_clients(self, room: str) -> List[str]:
        """Get list of client IDs in a room."""
        return list(self._rooms.get(room, set()))
    
    def get_client_rooms(self, client_id: str) -> List[str]:
        """Get list of rooms a client is in."""
        if client_id not in self._connections:
            return []
        return list(self._connections[client_id].rooms)
    
    def get_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "total_connections": self.connection_count,
            "total_rooms": self.room_count,
            "rooms": {
                room: len(clients)
                for room, clients in self._rooms.items()
            }
        }


# Global connection manager instance
manager = ConnectionManager()
