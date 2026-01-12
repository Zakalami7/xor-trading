"""
XOR Trading Platform - Bot Schemas
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from ..models.bot import BotStatus


class BotBase(BaseModel):
    """Base bot schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    # Exchange config
    exchange: str = Field(..., pattern=r"^(binance|bybit|okx|kraken)$")
    symbol: str = Field(..., min_length=3, max_length=20)
    market_type: str = Field(default="spot", pattern=r"^(spot|futures|margin)$")
    
    # Strategy
    strategy_id: UUID
    strategy_params: Dict[str, Any] = Field(default_factory=dict)
    
    # Trading parameters
    position_size: float = Field(..., gt=0)
    position_size_type: str = Field(default="fixed", pattern=r"^(fixed|percent)$")
    max_positions: int = Field(default=1, ge=1, le=100)
    
    # Leverage (for futures)
    leverage: int = Field(default=1, ge=1, le=125)
    margin_type: str = Field(default="cross", pattern=r"^(cross|isolated)$")


class BotCreate(BotBase):
    """Schema for bot creation"""
    api_credential_id: UUID
    
    # Optional risk overrides
    max_drawdown_percent: Optional[float] = Field(None, ge=1, le=100)
    stop_loss_percent: Optional[float] = Field(None, ge=0.1, le=100)
    take_profit_percent: Optional[float] = Field(None, ge=0.1, le=1000)
    trailing_stop_percent: Optional[float] = Field(None, ge=0.1, le=50)
    
    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        # Normalize symbol format
        return v.upper().replace("/", "")


class BotUpdate(BaseModel):
    """Schema for bot update"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    strategy_params: Optional[Dict[str, Any]] = None
    position_size: Optional[float] = Field(None, gt=0)
    max_positions: Optional[int] = Field(None, ge=1, le=100)
    leverage: Optional[int] = Field(None, ge=1, le=125)
    max_drawdown_percent: Optional[float] = Field(None, ge=1, le=100)
    stop_loss_percent: Optional[float] = Field(None, ge=0.1, le=100)
    take_profit_percent: Optional[float] = Field(None, ge=0.1, le=1000)
    trailing_stop_percent: Optional[float] = Field(None, ge=0.1, le=50)


class BotResponse(BaseModel):
    """Schema for bot response"""
    id: UUID
    name: str
    description: Optional[str]
    
    # Exchange
    exchange: str
    symbol: str
    base_asset: str
    quote_asset: str
    market_type: str
    
    # Strategy
    strategy_id: UUID
    strategy_params: Dict[str, Any]
    
    # Trading params
    position_size: float
    position_size_type: str
    max_positions: int
    leverage: int
    margin_type: str
    
    # Status
    status: BotStatus
    status_message: Optional[str]
    
    # Risk
    max_drawdown_percent: Optional[float]
    stop_loss_percent: Optional[float]
    take_profit_percent: Optional[float]
    trailing_stop_percent: Optional[float]
    
    # Timing
    created_at: datetime
    started_at: Optional[datetime]
    stopped_at: Optional[datetime]
    last_trade_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class BotWithStats(BotResponse):
    """Bot response with performance statistics"""
    # Performance
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # PnL
    total_pnl: float
    total_pnl_percent: float
    total_fees: float
    
    # Drawdown
    current_drawdown: float
    max_drawdown_reached: float
    
    # Runtime
    runtime_seconds: Optional[int]
    
    # Active positions count
    open_positions: int = 0
    pending_orders: int = 0


class BotAction(BaseModel):
    """Schema for bot actions (start/stop/pause)"""
    action: str = Field(..., pattern=r"^(start|stop|pause|resume)$")
    reason: Optional[str] = Field(None, max_length=200)


class BotSignal(BaseModel):
    """Trading signal from strategy"""
    bot_id: UUID
    signal_type: str  # buy, sell, close_long, close_short
    symbol: str
    price: float
    quantity: Optional[float] = None
    confidence: float = Field(default=1.0, ge=0, le=1)
    reason: str
    indicators: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BotPerformance(BaseModel):
    """Bot performance summary"""
    bot_id: UUID
    period: str  # 1h, 24h, 7d, 30d, all
    
    # Trades
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # PnL
    gross_pnl: float
    net_pnl: float
    total_fees: float
    
    # Risk metrics
    max_drawdown: float
    sharpe_ratio: Optional[float]
    profit_factor: Optional[float]
    
    # Per trade
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_hold_time_seconds: int
    
    # Timeline
    pnl_history: List[Dict[str, Any]] = Field(default_factory=list)


class APICredentialCreate(BaseModel):
    """Schema for API credential creation"""
    name: str = Field(..., min_length=1, max_length=100)
    exchange: str = Field(..., pattern=r"^(binance|bybit|okx|kraken)$")
    api_key: str = Field(..., min_length=10)
    api_secret: str = Field(..., min_length=10)
    passphrase: Optional[str] = None  # For OKX
    is_testnet: bool = Field(default=False)


class APICredentialResponse(BaseModel):
    """Schema for API credential response (no secrets!)"""
    id: UUID
    name: str
    exchange: str
    api_key_last4: Optional[str]
    permissions: Dict[str, bool]
    is_valid: bool
    last_validated: Optional[datetime]
    is_testnet: bool
    is_safe: bool
    created_at: datetime
    last_used: Optional[datetime]
    
    class Config:
        from_attributes = True
