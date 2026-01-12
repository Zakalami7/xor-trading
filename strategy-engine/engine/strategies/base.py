"""
XOR Strategy Engine - Base Strategy Class
Abstract base class for all trading strategies
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SignalType(str, Enum):
    """Trading signal types."""
    BUY = "buy"
    SELL = "sell"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"
    HOLD = "hold"


@dataclass
class Signal:
    """Trading signal from strategy."""
    type: SignalType
    symbol: str
    price: float
    quantity: Optional[float] = None
    confidence: float = 1.0
    reason: str = ""
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    indicators: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "symbol": self.symbol,
            "price": self.price,
            "quantity": self.quantity,
            "confidence": self.confidence,
            "reason": self.reason,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "indicators": self.indicators,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class MarketState:
    """Current market state for strategy."""
    symbol: str
    price: float
    bid: float
    ask: float
    volume_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.
    All strategies must implement the core methods.
    """
    
    name: str = "BaseStrategy"
    description: str = ""
    
    def __init__(self, symbol: str, params: Dict[str, Any]):
        self.symbol = symbol
        self.params = params
        self.is_running = False
        
        # Market data
        self.current_price: float = 0.0
        self.candles: List[Dict] = []
        self.orderbook: Dict = {}
        
        # Position tracking
        self.position_size: float = 0.0
        self.entry_price: float = 0.0
        self.unrealized_pnl: float = 0.0
    
    async def initialize(self):
        """Initialize strategy. Override for custom init."""
        self.is_running = True
    
    async def cleanup(self):
        """Cleanup strategy. Override for custom cleanup."""
        self.is_running = False
    
    @abstractmethod
    async def on_tick(self, tick: dict) -> Optional[Signal]:
        """
        Called on each price tick.
        Must return a Signal or None.
        """
        pass
    
    async def on_candle(self, candle: dict) -> Optional[Signal]:
        """Called when a new candle closes. Override if needed."""
        self.candles.append(candle)
        if len(self.candles) > 500:
            self.candles = self.candles[-500:]
        return None
    
    async def on_orderbook(self, orderbook: dict) -> Optional[Signal]:
        """Called on orderbook update. Override if needed."""
        self.orderbook = orderbook
        return None
    
    async def on_order_filled(self, order: dict):
        """Called when an order is filled. Override to track position."""
        pass
    
    async def on_position_update(self, position: dict):
        """Called when position changes. Override to track state."""
        self.position_size = position.get("quantity", 0)
        self.entry_price = position.get("entry_price", 0)
        self.unrealized_pnl = position.get("unrealized_pnl", 0)
    
    def has_position(self) -> bool:
        """Check if strategy has an open position."""
        return self.position_size != 0
    
    def validate_params(self) -> bool:
        """Validate strategy parameters. Override to add validation."""
        return True
