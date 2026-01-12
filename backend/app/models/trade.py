"""
XOR Trading Platform - Trade Model
Executed trades (fills)
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .order import Order


class Trade(Base, UUIDMixin, TimestampMixin):
    """
    Individual trade execution.
    A single order can result in multiple trades (partial fills).
    """
    
    __tablename__ = "trades"
    __allow_unmapped__ = True
    
    # References
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    position_id = Column(UUID(as_uuid=True), ForeignKey("positions.id"), nullable=True, index=True)
    
    # Exchange reference
    exchange = Column(String(50), nullable=False)
    exchange_trade_id = Column(String(100), nullable=True, index=True)
    exchange_order_id = Column(String(100), nullable=True)
    
    # Symbol
    symbol = Column(String(20), nullable=False, index=True)
    
    # Trade details
    side = Column(String(10), nullable=False)  # buy, sell
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    
    # Value
    quote_quantity = Column(Float, nullable=False)  # quantity * price
    
    # Fees
    fee = Column(Float, default=0.0, nullable=False)
    fee_asset = Column(String(10), nullable=True)
    
    # PnL (calculated for closing trades)
    realized_pnl = Column(Float, nullable=True)
    realized_pnl_percent = Column(Float, nullable=True)
    
    # Execution timing
    executed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Role
    is_maker = Column(String(10), default="false", nullable=False)  # Maker or taker
    
    # Raw data
    raw_data = Column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Trade {self.side} {self.quantity} {self.symbol} @ {self.price}>"
    
    @property
    def value(self) -> float:
        return self.quantity * self.price
    
    @property
    def net_value(self) -> float:
        """Value after fees"""
        return self.value - self.fee
