import asyncio
from typing import Optional, Dict
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    def _generate_connection_key(self, user_id: str, agent_id: str) -> str:
        return f"{user_id}:{agent_id}"

    async def connect(self, websocket: WebSocket, user_id: str, agent_id: str) -> str:
        await websocket.accept()
        connection_key = self._generate_connection_key(user_id, agent_id)

        async with self._lock:
            if connection_key in self.active_connections:
                old_websocket = self.active_connections[connection_key]
                try:
                    await old_websocket.close()
                except Exception:
                    pass

            self.active_connections[connection_key] = websocket

        logger.info(f"WebSocket connected: {connection_key}")
        return connection_key

    async def disconnect(self, user_id: str, agent_id: str) -> None:
        connection_key = self._generate_connection_key(user_id, agent_id)

        async with self._lock:
            if connection_key in self.active_connections:
                del self.active_connections[connection_key]
                logger.info(f"WebSocket disconnected: {connection_key}")

    async def send_message(self, user_id: str, agent_id: str, message: str) -> bool:
        connection_key = self._generate_connection_key(user_id, agent_id)

        async with self._lock:
            websocket = self.active_connections.get(connection_key)

        if websocket:
            try:
                await websocket.send_text(message)
                return True
            except Exception as e:
                logger.error(f"Failed to send message to {connection_key}: {e}")
                await self.disconnect(user_id, agent_id)
                return False

        logger.warning(f"No active connection found for {connection_key}")
        return False

    async def broadcast_to_user(self, user_id: str, message: str) -> int:
        sent_count = 0
        user_connections = [
            (key, ws) for key, ws in self.active_connections.items()
            if key.startswith(f"{user_id}:")
        ]

        for connection_key, websocket in user_connections:
            try:
                await websocket.send_text(message)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to broadcast to {connection_key}: {e}")

        return sent_count

    def is_connected(self, user_id: str, agent_id: str) -> bool:
        connection_key = self._generate_connection_key(user_id, agent_id)
        return connection_key in self.active_connections

    def get_connection_count(self) -> int:
        return len(self.active_connections)


ws_manager = ConnectionManager()