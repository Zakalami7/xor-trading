"""
XOR Trading Platform - Event System
Async event bus with Redis Pub/Sub for inter-service communication
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Type, TypeVar
from uuid import uuid4

import redis.asyncio as redis

from ..config import settings

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Standard event types in the system"""
    # Market Events
    MARKET_TICK = "market.tick"
    MARKET_ORDERBOOK = "market.orderbook"
    MARKET_TRADE = "market.trade"
    MARKET_KLINE = "market.kline"
    
    # Bot Events
    BOT_CREATED = "bot.created"
    BOT_STARTED = "bot.started"
    BOT_STOPPED = "bot.stopped"
    BOT_ERROR = "bot.error"
    BOT_SIGNAL = "bot.signal"
    
    # Order Events
    ORDER_CREATED = "order.created"
    ORDER_FILLED = "order.filled"
    ORDER_PARTIAL = "order.partial"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_REJECTED = "order.rejected"
    ORDER_ERROR = "order.error"
    
    # Position Events
    POSITION_OPENED = "position.opened"
    POSITION_CLOSED = "position.closed"
    POSITION_UPDATED = "position.updated"
    POSITION_LIQUIDATION_RISK = "position.liquidation_risk"
    
    # Risk Events
    RISK_ALERT = "risk.alert"
    RISK_LIMIT_EXCEEDED = "risk.limit_exceeded"
    RISK_KILL_SWITCH = "risk.kill_switch"
    
    # AI Events
    AI_SIGNAL = "ai.signal"
    AI_PREDICTION = "ai.prediction"
    
    # System Events
    SYSTEM_HEALTH = "system.health"
    SYSTEM_ERROR = "system.error"


@dataclass
class Event:
    """Base event class"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    source: str = "unknown"
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "correlation_id": self.correlation_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        """Create event from dictionary"""
        return cls(
            event_id=data.get("event_id", str(uuid4())),
            type=data["type"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.utcnow(),
            source=data.get("source", "unknown"),
            correlation_id=data.get("correlation_id"),
        )
    
    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """Deserialize from JSON string"""
        return cls.from_dict(json.loads(json_str))


# Type for event handlers
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """
    Async event bus with Redis Pub/Sub support.
    Enables decoupled communication between services.
    """
    
    def __init__(
        self,
        redis_url: str = None,
        service_name: str = "backend",
    ):
        self.redis_url = redis_url or settings.REDIS_URL
        self.service_name = service_name
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._running = False
        self._listener_task: Optional[asyncio.Task] = None
    
    async def connect(self):
        """Connect to Redis"""
        if self._redis is None:
            self._redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            self._pubsub = self._redis.pubsub()
            logger.info(f"EventBus connected to Redis: {self.redis_url}")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        self._running = False
        
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        
        if self._pubsub:
            await self._pubsub.close()
            self._pubsub = None
        
        if self._redis:
            await self._redis.close()
            self._redis = None
        
        logger.info("EventBus disconnected")
    
    def subscribe(self, event_type: str, handler: EventHandler):
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: Event type pattern (supports wildcards like "order.*")
            handler: Async function to handle the event
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(handler)
        logger.debug(f"Handler subscribed to: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: EventHandler):
        """Unsubscribe a handler from an event type"""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
            if not self._handlers[event_type]:
                del self._handlers[event_type]
    
    async def publish(self, event: Event):
        """
        Publish an event to Redis.
        
        Args:
            event: Event to publish
        """
        await self.connect()
        
        event.source = self.service_name
        channel = f"xor:events:{event.type}"
        
        await self._redis.publish(channel, event.to_json())
        
        logger.debug(f"Event published: {event.type} -> {event.event_id}")
    
    async def emit(
        self,
        event_type: str,
        data: dict,
        correlation_id: str = None,
    ) -> Event:
        """
        Convenience method to create and publish an event.
        
        Args:
            event_type: Type of event
            data: Event data
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            The created event
        """
        event = Event(
            type=event_type,
            data=data,
            source=self.service_name,
            correlation_id=correlation_id,
        )
        
        await self.publish(event)
        return event
    
    async def start_listening(self, patterns: List[str] = None):
        """
        Start listening for events on Redis.
        
        Args:
            patterns: List of event patterns to subscribe to.
                     Defaults to all registered handlers.
        """
        await self.connect()
        
        # Subscribe to patterns
        subscribe_patterns = patterns or list(self._handlers.keys())
        
        for pattern in subscribe_patterns:
            channel = f"xor:events:{pattern}"
            if "*" in pattern:
                await self._pubsub.psubscribe(channel)
            else:
                await self._pubsub.subscribe(channel)
        
        self._running = True
        self._listener_task = asyncio.create_task(self._listen())
        
        logger.info(f"EventBus listening on: {subscribe_patterns}")
    
    async def _listen(self):
        """Internal listener loop"""
        while self._running:
            try:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                
                if message and message["type"] in ("message", "pmessage"):
                    await self._handle_message(message)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event listener: {e}")
                await asyncio.sleep(1)
    
    async def _handle_message(self, message: dict):
        """Handle an incoming Redis message"""
        try:
            # Extract event type from channel
            channel = message.get("channel", message.get("pattern", ""))
            event_type = channel.replace("xor:events:", "")
            
            # Parse event
            event = Event.from_json(message["data"])
            
            # Find and execute matching handlers
            await self._dispatch_event(event)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _dispatch_event(self, event: Event):
        """Dispatch event to matching handlers"""
        tasks = []
        
        for pattern, handlers in self._handlers.items():
            if self._matches_pattern(event.type, pattern):
                for handler in handlers:
                    tasks.append(self._safe_handle(handler, event))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    @staticmethod
    def _matches_pattern(event_type: str, pattern: str) -> bool:
        """Check if event type matches pattern (supports wildcards)"""
        if pattern == "*":
            return True
        
        if "*" not in pattern:
            return event_type == pattern
        
        # Simple wildcard matching
        parts = pattern.split("*")
        if len(parts) == 2:
            prefix, suffix = parts
            return event_type.startswith(prefix) and event_type.endswith(suffix)
        
        return event_type.startswith(parts[0])
    
    @staticmethod
    async def _safe_handle(handler: EventHandler, event: Event):
        """Safely execute a handler with error logging"""
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Error in event handler: {e}", exc_info=True)


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create global event bus"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# Decorator for event handlers
def on_event(event_type: str):
    """
    Decorator to register a function as an event handler.
    
    Usage:
        @on_event("order.filled")
        async def handle_order_filled(event: Event):
            print(f"Order filled: {event.data}")
    """
    def decorator(func: EventHandler):
        get_event_bus().subscribe(event_type, func)
        return func
    return decorator
