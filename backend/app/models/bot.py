"""
XOR Trading Platform - Bot Model
"""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLEnum, Float,
    ForeignKey, Integer, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.orm import relationship

from ..db.base import Base, TimestampMixin, UUIDMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .user import User
    from .strategy import Strategy
    from .order import Order
    from .position import Position


class BotStatus(str, Enum):
    """Bot status enumeration"""
    CREATED = "created"      # Just created, not started
    STARTING = "starting"    # Starting up, connecting
    RUNNING = "running"      # Active and trading
    PAUSED = "paused"        # Temporarily paused
    STOPPING = "stopping"    # Graceful shutdown
    STOPPED = "stopped"      # Stopped by user
    ERROR = "error"          # Stopped due to error
    KILLED = "killed"        # Kill switch activated


class Bot(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Trading bot configuration and state"""
    
    __tablename__ = "bots"
    __allow_unmapped__ = True
    
    # Basic info
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Ownership
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Exchange configuration
    exchange = Column(String(50), nullable=False)  # binance, bybit, okx, etc.
    api_credential_id = Column(UUID(as_uuid=True), ForeignKey("api_credentials.id"), nullable=False)
    
    # Trading pair
    symbol = Column(String(20), nullable=False, index=True)  # BTC/USDT, ETH/USDT
    base_asset = Column(String(10), nullable=False)  # BTC, ETH
    quote_asset = Column(String(10), nullable=False)  # USDT, USDC
    
    # Market type
    market_type = Column(String(20), default="spot", nullable=False)  # spot, futures, margin
    
    # Strategy configuration
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    strategy_params = Column(JSON, default=dict, nullable=False)
    
    # Status
    status = Column(
        SQLEnum(BotStatus, name="bot_status"),
        default=BotStatus.CREATED,
        nullable=False,
        index=True,
    )
    status_message = Column(Text, nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Trading parameters
    position_size = Column(Float, default=100.0, nullable=False)  # In quote currency
    position_size_type = Column(String(20), default="fixed", nullable=False)  # fixed, percent
    max_positions = Column(Integer, default=1, nullable=False)
    
    # Leverage (for futures)
    leverage = Column(Integer, default=1, nullable=False)
    margin_type = Column(String(20), default="cross", nullable=False)  # cross, isolated
    
    # Risk parameters (bot-specific, override user defaults)
    max_drawdown_percent = Column(Float, nullable=True)
    stop_loss_percent = Column(Float, nullable=True)
    take_profit_percent = Column(Float, nullable=True)
    trailing_stop_percent = Column(Float, nullable=True)
    
    # Performance tracking
    total_trades = Column(Integer, default=0, nullable=False)
    winning_trades = Column(Integer, default=0, nullable=False)
    losing_trades = Column(Integer, default=0, nullable=False)
    total_pnl = Column(Float, default=0.0, nullable=False)
    total_pnl_percent = Column(Float, default=0.0, nullable=False)
    total_fees = Column(Float, default=0.0, nullable=False)
    
    # Peak and drawdown
    peak_balance = Column(Float, default=0.0, nullable=False)
    current_drawdown = Column(Float, default=0.0, nullable=False)
    max_drawdown_reached = Column(Float, default=0.0, nullable=False)
    
    # Runtime info
    started_at = Column(DateTime(timezone=True), nullable=True)
    stopped_at = Column(DateTime(timezone=True), nullable=True)
    last_trade_at = Column(DateTime(timezone=True), nullable=True)
    last_signal_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="bots")
    strategy = relationship("Strategy", back_populates="bots")
    orders = relationship("Order", back_populates="bot", lazy="dynamic")
    positions = relationship("Position", back_populates="bot", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<Bot {self.name} ({self.symbol})>"
    
    @property
    def is_active(self) -> bool:
        return self.status in (BotStatus.RUNNING, BotStatus.STARTING)
    
    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100
    
    @property
    def runtime_seconds(self) -> Optional[int]:
        if not self.started_at:
            return None
        end_time = self.stopped_at or datetime.utcnow()
        return int((end_time - self.started_at).total_seconds())
