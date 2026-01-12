"""
XOR Strategy Engine - Scalping Strategy
High-frequency trading for small profits
"""
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from .base import BaseStrategy, Signal, SignalType


class ScalpingStrategy(BaseStrategy):
    """
    Scalping Strategy.
    Fast execution for small profits using orderbook analysis.
    """
    
    name = "Scalping"
    description = "High-frequency scalping using orderbook imbalance"
    
    def __init__(self, symbol: str, params: Dict[str, Any]):
        super().__init__(symbol, params)
        
        # Scalping parameters
        self.spread_threshold = params["spread_threshold"]
        self.take_profit_ticks = params["take_profit_ticks"]
        self.stop_loss_ticks = params["stop_loss_ticks"]
        self.imbalance_threshold = params.get("order_book_imbalance_threshold", 2.0)
        self.position_time_limit = params.get("position_time_limit", 60)
        self.use_market_orders = params.get("use_market_orders", True)
        
        # State
        self.tick_size = 0.01  # Will be set from exchange
        self.price_history = deque(maxlen=100)
        self.position_open_time: Optional[datetime] = None
        self.entry_side: Optional[str] = None
    
    async def on_tick(self, tick: dict) -> Optional[Signal]:
        """Process price tick."""
        price = tick.get("price", 0)
        bid = tick.get("bid", 0)
        ask = tick.get("ask", 0)
        
        if not all([price, bid, ask]):
            return None
        
        self.current_price = price
        self.price_history.append(price)
        
        spread = ((ask - bid) / bid) * 100
        
        # Check position timeout
        if self.has_position() and self.position_open_time:
            hold_time = (datetime.utcnow() - self.position_open_time).total_seconds()
            if hold_time >= self.position_time_limit:
                return Signal(
                    type=SignalType.CLOSE_LONG if self.entry_side == "long" else SignalType.CLOSE_SHORT,
                    symbol=self.symbol,
                    price=price,
                    reason="Position time limit reached",
                )
        
        # Check take profit / stop loss
        if self.has_position():
            return self._check_exit(price)
        
        # Entry logic
        if spread <= self.spread_threshold:
            return await self._check_entry(bid, ask)
        
        return None
    
    async def on_orderbook(self, orderbook: dict) -> Optional[Signal]:
        """Analyze orderbook for entry signals."""
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])
        
        if not bids or not asks:
            return None
        
        # Calculate imbalance
        bid_volume = sum(level[1] for level in bids[:10])
        ask_volume = sum(level[1] for level in asks[:10])
        
        if ask_volume == 0:
            return None
        
        imbalance = bid_volume / ask_volume
        
        # Store for entry decisions
        self.orderbook = {
            "bid_volume": bid_volume,
            "ask_volume": ask_volume,
            "imbalance": imbalance,
        }
        
        return None
    
    async def _check_entry(self, bid: float, ask: float) -> Optional[Signal]:
        """Check for entry conditions."""
        imbalance = self.orderbook.get("imbalance", 1.0)
        
        # Strong buying pressure
        if imbalance >= self.imbalance_threshold:
            self.entry_side = "long"
            self.position_open_time = datetime.utcnow()
            
            return Signal(
                type=SignalType.BUY,
                symbol=self.symbol,
                price=ask if self.use_market_orders else bid,
                reason=f"Orderbook imbalance: {imbalance:.2f}",
                stop_loss=bid - (self.stop_loss_ticks * self.tick_size),
                take_profit=ask + (self.take_profit_ticks * self.tick_size),
                indicators={"imbalance": imbalance},
            )
        
        # Strong selling pressure
        elif imbalance <= 1 / self.imbalance_threshold:
            self.entry_side = "short"
            self.position_open_time = datetime.utcnow()
            
            return Signal(
                type=SignalType.SELL,
                symbol=self.symbol,
                price=bid if self.use_market_orders else ask,
                reason=f"Orderbook imbalance: {imbalance:.2f}",
                stop_loss=ask + (self.stop_loss_ticks * self.tick_size),
                take_profit=bid - (self.take_profit_ticks * self.tick_size),
                indicators={"imbalance": imbalance},
            )
        
        return None
    
    def _check_exit(self, price: float) -> Optional[Signal]:
        """Check for exit conditions."""
        pnl_ticks = 0
        
        if self.entry_side == "long":
            pnl_ticks = (price - self.entry_price) / self.tick_size
        else:
            pnl_ticks = (self.entry_price - price) / self.tick_size
        
        if pnl_ticks >= self.take_profit_ticks:
            signal_type = SignalType.CLOSE_LONG if self.entry_side == "long" else SignalType.CLOSE_SHORT
            return Signal(
                type=signal_type,
                symbol=self.symbol,
                price=price,
                reason=f"Take profit: {pnl_ticks:.0f} ticks",
            )
        
        if pnl_ticks <= -self.stop_loss_ticks:
            signal_type = SignalType.CLOSE_LONG if self.entry_side == "long" else SignalType.CLOSE_SHORT
            return Signal(
                type=signal_type,
                symbol=self.symbol,
                price=price,
                reason=f"Stop loss: {pnl_ticks:.0f} ticks",
            )
        
        return None
    
    def validate_params(self) -> bool:
        if self.take_profit_ticks <= 0:
            return False
        if self.stop_loss_ticks <= 0:
            return False
        return True
