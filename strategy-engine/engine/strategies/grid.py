"""
XOR Strategy Engine - Grid Trading Strategy
Automated grid of buy/sell orders within a price range
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .base import BaseStrategy, Signal, SignalType


@dataclass
class GridLevel:
    """Represents a grid level."""
    price: float
    is_buy: bool
    is_filled: bool = False
    order_id: Optional[str] = None


class GridStrategy(BaseStrategy):
    """
    Grid Trading Strategy.
    Places buy and sell orders at regular intervals within a price range.
    Profits from price oscillation within the range.
    """
    
    name = "Grid Trading"
    description = "Automated grid of orders within a price range"
    
    def __init__(self, symbol: str, params: Dict[str, Any]):
        super().__init__(symbol, params)
        
        # Grid parameters
        self.grid_type = params.get("grid_type", "arithmetic")
        self.upper_price = params["upper_price"]
        self.lower_price = params["lower_price"]
        self.grid_count = params["grid_count"]
        self.order_size = params["order_size"]
        self.trigger_price = params.get("trigger_price")
        
        # State
        self.grid_levels: List[GridLevel] = []
        self.is_active = False
        self.total_profit = 0.0
    
    async def initialize(self):
        await super().initialize()
        self._build_grid()
    
    def _build_grid(self):
        """Build the grid levels."""
        self.grid_levels = []
        
        if self.grid_type == "arithmetic":
            step = (self.upper_price - self.lower_price) / self.grid_count
            for i in range(self.grid_count + 1):
                price = self.lower_price + (i * step)
                self.grid_levels.append(GridLevel(price=price, is_buy=True))
        else:  # geometric
            ratio = (self.upper_price / self.lower_price) ** (1 / self.grid_count)
            for i in range(self.grid_count + 1):
                price = self.lower_price * (ratio ** i)
                self.grid_levels.append(GridLevel(price=price, is_buy=True))
    
    async def on_tick(self, tick: dict) -> Optional[Signal]:
        """Process price tick."""
        price = tick.get("price", 0)
        if not price:
            return None
        
        self.current_price = price
        
        # Check trigger
        if self.trigger_price and not self.is_active:
            if price >= self.trigger_price:
                self.is_active = True
            else:
                return None
        else:
            self.is_active = True
        
        # Check if price is outside grid range
        if price > self.upper_price or price < self.lower_price:
            return None
        
        # Find which levels to execute
        for level in self.grid_levels:
            if level.is_filled:
                continue
            
            if level.is_buy and price <= level.price:
                # Buy at this level
                level.is_filled = True
                level.is_buy = False  # Next action at this level is sell
                
                return Signal(
                    type=SignalType.BUY,
                    symbol=self.symbol,
                    price=level.price,
                    quantity=self.order_size,
                    reason=f"Grid buy at {level.price}",
                    indicators={"grid_level": level.price},
                )
            
            elif not level.is_buy and price >= level.price:
                # Sell at this level
                level.is_filled = False
                level.is_buy = True  # Reset for next cycle
                
                return Signal(
                    type=SignalType.SELL,
                    symbol=self.symbol,
                    price=level.price,
                    quantity=self.order_size,
                    reason=f"Grid sell at {level.price}",
                    indicators={"grid_level": level.price},
                )
        
        return None
    
    def get_active_orders_count(self) -> int:
        """Get count of active grid levels."""
        return sum(1 for level in self.grid_levels if not level.is_filled)
    
    def validate_params(self) -> bool:
        """Validate grid parameters."""
        if self.upper_price <= self.lower_price:
            return False
        if self.grid_count < 2:
            return False
        if self.order_size <= 0:
            return False
        return True
