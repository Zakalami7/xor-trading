"""
XOR Trading Platform - Position Model
"""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum

from ..db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .bot import Bot


class PositionSide(str, Enum):
    """Position side"""
    LONG = "long"
    SHORT = "short"


class PositionStatus(str, Enum):
    """Position status"""
    OPEN = "open"
    CLOSED = "closed"
    LIQUIDATED = "liquidated"


class Position(Base, UUIDMixin, TimestampMixin):
    """
    Trading position.
    Tracks open positions with entry, current value, and PnL.
    """
    
    __tablename__ = "positions"
    __allow_unmapped__ = True
    
    # References
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Exchange
    exchange = Column(String(50), nullable=False)
    
    # Symbol
    symbol = Column(String(20), nullable=False, index=True)
    base_asset = Column(String(10), nullable=False)
    quote_asset = Column(String(10), nullable=False)
    
    # Position details
    side = Column(SQLEnum(PositionSide, name="position_side"), nullable=False)
    status = Column(
        SQLEnum(PositionStatus, name="position_status"),
        default=PositionStatus.OPEN,
        nullable=False,
        index=True,
    )
    
    # Quantities
    quantity = Column(Float, nullable=False)
    initial_quantity = Column(Float, nullable=False)
    
    # Entry
    entry_price = Column(Float, nullable=False)
    average_entry_price = Column(Float, nullable=False)
    entry_value = Column(Float, nullable=False)  # In quote currency
    
    # Current (updated in real-time)
    current_price = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    
    # Exit (when closed)
    exit_price = Column(Float, nullable=True)
    average_exit_price = Column(Float, nullable=True)
    exit_value = Column(Float, nullable=True)
    
    # PnL
    unrealized_pnl = Column(Float, default=0.0, nullable=False)
    unrealized_pnl_percent = Column(Float, default=0.0, nullable=False)
    realized_pnl = Column(Float, default=0.0, nullable=False)
    realized_pnl_percent = Column(Float, default=0.0, nullable=False)
    
    # Max values (for drawdown calculation)
    max_unrealized_pnl = Column(Float, default=0.0, nullable=False)
    max_drawdown = Column(Float, default=0.0, nullable=False)
    
    # Fees
    total_fees = Column(Float, default=0.0, nullable=False)
    
    # Leverage (for futures)
    leverage = Column(Float, default=1.0, nullable=False)
    liquidation_price = Column(Float, nullable=True)
    margin_type = Column(String(20), default="cross", nullable=False)
    margin_used = Column(Float, nullable=True)
    
    # DCA
    safety_orders_filled = Column(Float, default=0, nullable=False)
    total_orders = Column(Float, default=1, nullable=False)
    
    # Risk management
    stop_loss_price = Column(Float, nullable=True)
    take_profit_price = Column(Float, nullable=True)
    trailing_stop_price = Column(Float, nullable=True)
    
    # Timing
    opened_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Reason for close
    close_reason = Column(String(50), nullable=True)  # take_profit, stop_loss, manual, liquidation
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Raw data
    raw_data = Column(JSON, nullable=True)
    
    # Relationships
    bot = relationship("Bot", back_populates="positions")
    
    def __repr__(self) -> str:
        return f"<Position {self.side.value} {self.quantity} {self.symbol}>"
    
    @property
    def is_open(self) -> bool:
        return self.status == PositionStatus.OPEN
    
    @property
    def is_profitable(self) -> bool:
        if self.is_open:
            return self.unrealized_pnl > 0
        return self.realized_pnl > 0
    
    @property
    def hold_time_seconds(self) -> Optional[int]:
        """Time position has been held"""
        end_time = self.closed_at or datetime.utcnow()
        return int((end_time - self.opened_at).total_seconds())
    
    def update_unrealized_pnl(self, current_price: float):
        """Update unrealized PnL based on current price"""
        self.current_price = current_price
        self.current_value = self.quantity * current_price
        
        if self.side == PositionSide.LONG:
            self.unrealized_pnl = (current_price - self.average_entry_price) * self.quantity
        else:  # SHORT
            self.unrealized_pnl = (self.average_entry_price - current_price) * self.quantity
        
        self.unrealized_pnl -= self.total_fees
        self.unrealized_pnl_percent = (self.unrealized_pnl / self.entry_value) * 100
        
        # Track max PnL for drawdown
        if self.unrealized_pnl > self.max_unrealized_pnl:
            self.max_unrealized_pnl = self.unrealized_pnl
        
        # Calculate drawdown from peak
        if self.max_unrealized_pnl > 0:
            drawdown = self.max_unrealized_pnl - self.unrealized_pnl
            if drawdown > self.max_drawdown:
                self.max_drawdown = drawdown
        
        self.last_updated = datetime.utcnow()
    
    def close(self, exit_price: float, reason: str = None):
        """Close the position"""
        self.status = PositionStatus.CLOSED
        self.exit_price = exit_price
        self.average_exit_price = exit_price
        self.exit_value = self.quantity * exit_price
        
        if self.side == PositionSide.LONG:
            self.realized_pnl = (exit_price - self.average_entry_price) * self.quantity
        else:
            self.realized_pnl = (self.average_entry_price - exit_price) * self.quantity
        
        self.realized_pnl -= self.total_fees
        self.realized_pnl_percent = (self.realized_pnl / self.entry_value) * 100
        
        self.closed_at = datetime.utcnow()
        self.close_reason = reason
        self.quantity = 0
