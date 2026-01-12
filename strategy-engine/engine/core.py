"""
XOR Strategy Engine - Core Engine
Main orchestrator for strategy execution
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import redis.asyncio as redis

from .event_bus import EventBus
from .strategies.base import BaseStrategy, Signal

logger = logging.getLogger(__name__)


class StrategyEngine:
    """
    Core strategy execution engine.
    Manages strategy instances and processes market data.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.event_bus: Optional[EventBus] = None
        
        self.strategies: Dict[str, BaseStrategy] = {}
        self.running = False
        self._tasks: List[asyncio.Task] = []
    
    async def start(self):
        """Start the strategy engine."""
        logger.info("Starting Strategy Engine...")
        
        # Connect to Redis
        self.redis = await redis.from_url(self.redis_url)
        self.event_bus = EventBus(self.redis)
        
        # Subscribe to market events
        await self.event_bus.subscribe("market.*", self._on_market_event)
        await self.event_bus.subscribe("bot.*", self._on_bot_event)
        
        self.running = True
        
        # Start main loop
        self._tasks.append(asyncio.create_task(self._main_loop()))
        
        logger.info("Strategy Engine started")
    
    async def stop(self):
        """Stop the strategy engine."""
        logger.info("Stopping Strategy Engine...")
        self.running = False
        
        # Cancel tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Disconnect
        if self.redis:
            await self.redis.close()
        
        logger.info("Strategy Engine stopped")
    
    async def register_strategy(self, bot_id: str, strategy: BaseStrategy):
        """Register a strategy for a bot."""
        self.strategies[bot_id] = strategy
        await strategy.initialize()
        logger.info(f"Strategy registered for bot {bot_id}: {strategy.name}")
    
    async def unregister_strategy(self, bot_id: str):
        """Unregister a strategy."""
        if bot_id in self.strategies:
            await self.strategies[bot_id].cleanup()
            del self.strategies[bot_id]
            logger.info(f"Strategy unregistered for bot {bot_id}")
    
    async def _main_loop(self):
        """Main processing loop."""
        while self.running:
            try:
                await asyncio.sleep(0.1)  # 100ms tick
            except asyncio.CancelledError:
                break
    
    async def _on_market_event(self, event: dict):
        """Handle market data events."""
        event_type = event.get("type", "")
        data = event.get("data", {})
        symbol = data.get("symbol")
        
        if not symbol:
            return
        
        # Process for each strategy interested in this symbol
        for bot_id, strategy in self.strategies.items():
            if strategy.symbol == symbol:
                try:
                    if event_type == "market.tick":
                        signal = await strategy.on_tick(data)
                    elif event_type == "market.kline":
                        signal = await strategy.on_candle(data)
                    elif event_type == "market.orderbook":
                        signal = await strategy.on_orderbook(data)
                    else:
                        signal = None
                    
                    if signal:
                        await self._emit_signal(bot_id, signal)
                        
                except Exception as e:
                    logger.error(f"Strategy error for {bot_id}: {e}")
    
    async def _on_bot_event(self, event: dict):
        """Handle bot lifecycle events."""
        event_type = event.get("type", "")
        data = event.get("data", {})
        bot_id = data.get("bot_id")
        
        if event_type == "bot.started":
            logger.info(f"Bot started: {bot_id}")
        elif event_type == "bot.stopped":
            await self.unregister_strategy(bot_id)
    
    async def _emit_signal(self, bot_id: str, signal: Signal):
        """Emit a trading signal."""
        await self.event_bus.publish("bot.signal", {
            "bot_id": bot_id,
            "signal": signal.to_dict(),
            "timestamp": datetime.utcnow().isoformat(),
        })
        logger.info(f"Signal emitted for {bot_id}: {signal.type.value}")
