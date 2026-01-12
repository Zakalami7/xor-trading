"""
XOR Strategy Engine - Event Bus
Redis-based pub/sub for event distribution
"""
import asyncio
import json
from datetime import datetime
from typing import Any, Callable, Dict, List
from uuid import uuid4

import redis.asyncio as redis


class EventBus:
    """Redis-based event bus for strategy engine."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.pubsub = redis_client.pubsub()
        self.handlers: Dict[str, List[Callable]] = {}
        self._listener_task = None
    
    async def subscribe(self, pattern: str, handler: Callable):
        """Subscribe to an event pattern."""
        if pattern not in self.handlers:
            self.handlers[pattern] = []
            if "*" in pattern:
                await self.pubsub.psubscribe(f"xor:{pattern}")
            else:
                await self.pubsub.subscribe(f"xor:{pattern}")
        
        self.handlers[pattern].append(handler)
        
        # Start listener if not running
        if self._listener_task is None:
            self._listener_task = asyncio.create_task(self._listen())
    
    async def publish(self, channel: str, data: dict):
        """Publish an event."""
        message = {
            "id": str(uuid4()),
            "type": channel,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.redis.publish(f"xor:{channel}", json.dumps(message))
    
    async def _listen(self):
        """Listen for incoming messages."""
        while True:
            try:
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )
                if message:
                    await self._handle_message(message)
            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(1)
    
    async def _handle_message(self, message: dict):
        """Handle incoming message."""
        channel = message.get("channel", b"").decode()
        data = message.get("data", b"")
        
        if isinstance(data, bytes):
            data = json.loads(data.decode())
        
        # Find matching handlers
        for pattern, handlers in self.handlers.items():
            if self._matches(channel, f"xor:{pattern}"):
                for handler in handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(data)
                        else:
                            handler(data)
                    except Exception as e:
                        pass  # Log error in production
    
    def _matches(self, channel: str, pattern: str) -> bool:
        """Check if channel matches pattern."""
        if "*" not in pattern:
            return channel == pattern
        
        parts = pattern.split("*")
        return channel.startswith(parts[0])
