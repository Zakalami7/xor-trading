"""
XOR Strategy Engine - DCA (Dollar Cost Averaging) Strategy
Safety orders to lower average entry price
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .base import BaseStrategy, Signal, SignalType


@dataclass 
class SafetyOrder:
    """Represents a safety order."""
    order_num: int
    deviation_percent: float
    size: float
    trigger_price: float = 0.0
    is_filled: bool = False


class DCAStrategy(BaseStrategy):
    """
    DCA (Dollar Cost Averaging) Strategy.
    Places base order then safety orders as price drops.
    Takes profit when price rises above average entry.
    """
    
    name = "DCA"
    description = "Dollar Cost Averaging with safety orders"
    
    def __init__(self, symbol: str, params: Dict[str, Any]):
        super().__init__(symbol, params)
        
        # DCA parameters
        self.base_order_size = params["base_order_size"]
        self.safety_order_size = params["safety_order_size"]
        self.max_safety_orders = params.get("max_safety_orders", 5)
        self.price_deviation = params.get("price_deviation_percent", 1.0)
        self.step_scale = params.get("safety_order_step_scale", 1.0)
        self.volume_scale = params.get("safety_order_volume_scale", 1.0)
        self.take_profit_pct = params.get("take_profit_percent", 1.5)
        self.stop_loss_pct = params.get("stop_loss_percent")
        
        # State
        self.safety_orders: List[SafetyOrder] = []
        self.base_order_filled = False
        self.average_entry = 0.0
        self.total_quantity = 0.0
        self.total_invested = 0.0
    
    async def initialize(self):
        await super().initialize()
        self._build_safety_orders()
    
    def _build_safety_orders(self):
        """Build safety order ladder."""
        self.safety_orders = []
        
        current_deviation = self.price_deviation
        current_size = self.safety_order_size
        
        for i in range(self.max_safety_orders):
            self.safety_orders.append(SafetyOrder(
                order_num=i + 1,
                deviation_percent=current_deviation,
                size=current_size,
            ))
            current_deviation += self.price_deviation * self.step_scale
            current_size *= self.volume_scale
    
    async def on_tick(self, tick: dict) -> Optional[Signal]:
        """Process price tick."""
        price = tick.get("price", 0)
        if not price:
            return None
        
        self.current_price = price
        
        # Place base order if not yet filled
        if not self.base_order_filled:
            self.base_order_filled = True
            self.entry_price = price
            self._update_safety_triggers(price)
            
            return Signal(
                type=SignalType.BUY,
                symbol=self.symbol,
                price=price,
                quantity=self.base_order_size,
                reason="DCA base order",
                indicators={"order_type": "base"},
            )
        
        # Check take profit
        if self.total_quantity > 0:
            pnl_percent = ((price - self.average_entry) / self.average_entry) * 100
            
            if pnl_percent >= self.take_profit_pct:
                return Signal(
                    type=SignalType.SELL,
                    symbol=self.symbol,
                    price=price,
                    quantity=self.total_quantity,
                    reason=f"Take profit at {pnl_percent:.2f}%",
                    indicators={"pnl_percent": pnl_percent},
                )
            
            # Check stop loss
            if self.stop_loss_pct and pnl_percent <= -self.stop_loss_pct:
                return Signal(
                    type=SignalType.SELL,
                    symbol=self.symbol,
                    price=price,
                    quantity=self.total_quantity,
                    reason=f"Stop loss at {pnl_percent:.2f}%",
                    indicators={"pnl_percent": pnl_percent},
                )
        
        # Check safety orders
        for so in self.safety_orders:
            if so.is_filled:
                continue
            
            if price <= so.trigger_price:
                so.is_filled = True
                
                return Signal(
                    type=SignalType.BUY,
                    symbol=self.symbol,
                    price=price,
                    quantity=so.size,
                    reason=f"Safety order #{so.order_num}",
                    indicators={
                        "order_type": "safety",
                        "order_num": so.order_num,
                    },
                )
        
        return None
    
    def _update_safety_triggers(self, entry_price: float):
        """Update safety order trigger prices."""
        for so in self.safety_orders:
            so.trigger_price = entry_price * (1 - so.deviation_percent / 100)
    
    async def on_order_filled(self, order: dict):
        """Update state when order fills."""
        quantity = order.get("quantity", 0)
        price = order.get("price", 0)
        
        self.total_quantity += quantity
        self.total_invested += quantity * price
        self.average_entry = self.total_invested / self.total_quantity
    
    def validate_params(self) -> bool:
        if self.base_order_size <= 0:
            return False
        if self.safety_order_size <= 0:
            return False
        if self.take_profit_pct <= 0:
            return False
        return True
