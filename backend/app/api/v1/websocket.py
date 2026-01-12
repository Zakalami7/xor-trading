"""XOR Trading Platform - WebSocket Routes"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Set
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from ...core.auth import AuthManager
from ...models.user import User

router = APIRouter()
auth_manager = AuthManager()


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
    
    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for ws in self.active_connections[user_id].copy():
                try:
                    await ws.send_json(message)
                except Exception:
                    self.disconnect(user_id, ws)
    
    async def broadcast(self, message: dict):
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)


manager = ConnectionManager()


@router.websocket("/stream")
async def websocket_stream(websocket: WebSocket, token: str = None):
    """Main WebSocket endpoint for real-time updates."""
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return
    
    # Verify token
    payload = auth_manager.verify_token(token)
    if not payload:
        await websocket.close(code=4002, reason="Invalid token")
        return
    
    user_id = payload.sub
    await manager.connect(user_id, websocket)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to XOR Trading",
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Keep connection alive
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0
                )
                
                # Handle subscriptions
                if data.get("type") == "subscribe":
                    channel = data.get("channel")
                    await websocket.send_json({
                        "type": "subscribed",
                        "channel": channel,
                    })
                
                elif data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except asyncio.TimeoutError:
                # Send ping to keep alive
                await websocket.send_json({"type": "ping"})
                
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception:
        manager.disconnect(user_id, websocket)
