"""
XOR Trading Platform - Order Model
"""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum

from ..db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .bot import Bot


class OrderType(str, Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"
    TAKE_PROFIT_MARKET = "take_profit_market"
    TAKE_PROFIT_LIMIT = "take_profit_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(str, Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """Order status"""
    PENDING = "pending"          # Created, not sent
    SUBMITTED = "submitted"      # Sent to exchange
    OPEN = "open"               # Accepted by exchange
    PARTIAL = "partial"         # Partially filled
    FILLED = "filled"           # Completely filled
    CANCELLED = "cancelled"     # Cancelled by user
    REJECTED = "rejected"       # Rejected by exchange
    EXPIRED = "expired"         # Order expired


class Order(Base, UUIDMixin, TimestampMixin):
    """Trading order"""
    
    __tablename__ = "orders"
    __allow_unmapped__ = True
    
    # Bot reference
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Exchange reference
    exchange = Column(String(50), nullable=False)
    exchange_order_id = Column(String(100), nullable=True, index=True)
    client_order_id = Column(String(100), nullable=True, unique=True)
    
    # Symbol
    symbol = Column(String(20), nullable=False, index=True)
    
    # Order details
    type = Column(SQLEnum(OrderType, name="order_type"), nullable=False)
    side = Column(SQLEnum(OrderSide, name="order_side"), nullable=False)
    status = Column(
        SQLEnum(OrderStatus, name="order_status"),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True,
    )
    
    # Quantities
    quantity = Column(Float, nullable=False)
    filled_quantity = Column(Float, default=0.0, nullable=False)
    remaining_quantity = Column(Float, nullable=True)
    
    # Prices
    price = Column(Float, nullable=True)  # Limit price
    stop_price = Column(Float, nullable=True)  # Stop/trigger price
    average_price = Column(Float, nullable=True)  # Average fill price
    
    # Trailing
    trailing_delta = Column(Float, nullable=True)
    activation_price = Column(Float, nullable=True)
    
    # Value
    quote_quantity = Column(Float, nullable=True)  # Value in quote currency
    
    # Fees
    fee = Column(Float, default=0.0, nullable=False)
    fee_asset = Column(String(10), nullable=True)
    
    # Time in force
    time_in_force = Column(String(10), default="GTC", nullable=False)  # GTC, IOC, FOK
    
    # Reduce only (futures)
    reduce_only = Column(String(10), default="false", nullable=False)
    
    # Reason for order
    reason = Column(String(50), nullable=True)  # signal, safety_order, take_profit, stop_loss, etc.
    
    # Error info
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timing
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    filled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Latency tracking
    latency_ms = Column(Integer, nullable=True)  # Time from submit to exchange confirmation
    
    # Raw exchange response
    raw_data = Column(JSON, nullable=True)
    
    # Relationships
    bot = relationship("Bot", back_populates="orders")
    
    def __repr__(self) -> str:
        return f"<Order {self.side.value} {self.quantity} {self.symbol} @ {self.price or 'market'}>"
    
    @property
    def is_open(self) -> bool:
        return self.status in (OrderStatus.OPEN, OrderStatus.PARTIAL, OrderStatus.SUBMITTED)
    
    @property
    def is_filled(self) -> bool:
        return self.status == OrderStatus.FILLED
    
    @property
    def fill_percent(self) -> float:
        if self.quantity == 0:
            return 0.0
        return (self.filled_quantity / self.quantity) * 100
    
    @property
    def value(self) -> Optional[float]:
        """Calculate order value in quote currency"""
        if self.average_price:
            return self.filled_quantity * self.average_price
        elif self.price:
            return self.quantity * self.price
        return None
