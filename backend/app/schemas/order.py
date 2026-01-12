"""
XOR Trading Platform - Order Schemas
"""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..models.order import OrderSide, OrderStatus, OrderType


class OrderCreate(BaseModel):
    """Schema for order creation"""
    symbol: str = Field(..., min_length=3, max_length=20)
    type: OrderType
    side: OrderSide
    quantity: float = Field(..., gt=0)
    price: Optional[float] = Field(None, gt=0)  # Required for limit orders
    stop_price: Optional[float] = Field(None, gt=0)  # For stop orders
    time_in_force: str = Field(default="GTC", pattern=r"^(GTC|IOC|FOK)$")
    reduce_only: bool = Field(default=False)
    
    # Trailing stop
    trailing_delta: Optional[float] = Field(None, gt=0)
    activation_price: Optional[float] = Field(None, gt=0)


class OrderResponse(BaseModel):
    """Schema for order response"""
    id: UUID
    bot_id: UUID
    
    # Exchange
    exchange: str
    exchange_order_id: Optional[str]
    client_order_id: Optional[str]
    
    # Symbol
    symbol: str
    
    # Order details
    type: OrderType
    side: OrderSide
    status: OrderStatus
    
    # Quantities
    quantity: float
    filled_quantity: float
    remaining_quantity: Optional[float]
    
    # Prices
    price: Optional[float]
    stop_price: Optional[float]
    average_price: Optional[float]
    
    # Value & fees
    quote_quantity: Optional[float]
    fee: float
    fee_asset: Optional[str]
    
    # Time in force
    time_in_force: str
    
    # Reason
    reason: Optional[str]
    
    # Timing
    created_at: datetime
    submitted_at: Optional[datetime]
    filled_at: Optional[datetime]
    
    # Latency
    latency_ms: Optional[int]
    
    class Config:
        from_attributes = True


class OrderUpdate(BaseModel):
    """Schema for order update (modify)"""
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)


class OrderCancel(BaseModel):
    """Schema for order cancellation"""
    reason: Optional[str] = Field(None, max_length=200)


class TradeResponse(BaseModel):
    """Schema for trade response"""
    id: UUID
    order_id: UUID
    bot_id: UUID
    position_id: Optional[UUID]
    
    # Exchange
    exchange: str
    exchange_trade_id: Optional[str]
    
    # Symbol
    symbol: str
    
    # Trade details
    side: str
    quantity: float
    price: float
    quote_quantity: float
    
    # Fees
    fee: float
    fee_asset: Optional[str]
    
    # PnL
    realized_pnl: Optional[float]
    realized_pnl_percent: Optional[float]
    
    # Timing
    executed_at: datetime
    is_maker: bool
    
    class Config:
        from_attributes = True


class PositionResponse(BaseModel):
    """Schema for position response"""
    id: UUID
    bot_id: UUID
    
    # Exchange
    exchange: str
    symbol: str
    
    # Position
    side: str
    status: str
    quantity: float
    
    # Entry
    entry_price: float
    average_entry_price: float
    entry_value: float
    
    # Current
    current_price: Optional[float]
    current_value: Optional[float]
    
    # PnL
    unrealized_pnl: float
    unrealized_pnl_percent: float
    realized_pnl: float
    realized_pnl_percent: float
    
    # Leverage
    leverage: float
    liquidation_price: Optional[float]
    
    # Risk management
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    trailing_stop_price: Optional[float]
    
    # DCA
    safety_orders_filled: int
    total_orders: int
    
    # Fees
    total_fees: float
    
    # Timing
    opened_at: datetime
    last_updated: datetime
    hold_time_seconds: Optional[int]
    
    class Config:
        from_attributes = True
