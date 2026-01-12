"""
XOR Trading Platform - Strategy Schemas
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..models.strategy import StrategyType


class StrategyParams(BaseModel):
    """Generic strategy parameters"""
    params: Dict[str, Any] = Field(default_factory=dict)


class StrategyResponse(BaseModel):
    """Strategy response schema"""
    id: UUID
    name: str
    description: Optional[str]
    type: StrategyType
    is_system: bool
    config_schema: Dict[str, Any]
    default_params: Dict[str, Any]
    supported_markets: List[str]
    risk_level: str
    indicators: List[str]
    
    class Config:
        from_attributes = True


class GridStrategyParams(BaseModel):
    """Grid trading strategy parameters"""
    grid_type: str = Field(default="arithmetic", pattern=r"^(arithmetic|geometric)$")
    upper_price: float = Field(..., gt=0)
    lower_price: float = Field(..., gt=0)
    grid_count: int = Field(..., ge=2, le=200)
    order_size: float = Field(..., gt=0)
    trigger_price: Optional[float] = Field(None, gt=0)
    
    @property
    def grid_spacing(self) -> float:
        """Calculate spacing between grids"""
        if self.grid_type == "arithmetic":
            return (self.upper_price - self.lower_price) / self.grid_count
        else:  # geometric
            ratio = (self.upper_price / self.lower_price) ** (1 / self.grid_count)
            return ratio - 1


class DCAStrategyParams(BaseModel):
    """DCA strategy parameters"""
    base_order_size: float = Field(..., gt=0)
    safety_order_size: float = Field(..., gt=0)
    max_safety_orders: int = Field(default=5, ge=1, le=50)
    price_deviation_percent: float = Field(default=1.0, ge=0.1, le=50)
    safety_order_step_scale: float = Field(default=1.0, ge=1)
    safety_order_volume_scale: float = Field(default=1.0, ge=1)
    take_profit_percent: float = Field(default=1.5, ge=0.1)
    stop_loss_percent: Optional[float] = Field(None, ge=0)
    trailing_take_profit: bool = Field(default=False)
    trailing_deviation: Optional[float] = Field(None, ge=0.1)
    
    @property
    def max_investment(self) -> float:
        """Calculate maximum possible investment"""
        total = self.base_order_size
        size = self.safety_order_size
        for i in range(self.max_safety_orders):
            total += size
            size *= self.safety_order_volume_scale
        return total


class ScalpingStrategyParams(BaseModel):
    """Scalping strategy parameters"""
    spread_threshold: float = Field(..., ge=0)
    position_time_limit: int = Field(default=60, ge=1)
    take_profit_ticks: int = Field(..., ge=1)
    stop_loss_ticks: int = Field(..., ge=1)
    order_book_imbalance_threshold: float = Field(default=2.0, ge=1)
    volume_filter: Optional[float] = Field(None, ge=0)
    use_market_orders: bool = Field(default=True)
    max_positions: int = Field(default=1, ge=1, le=10)


class TrendFollowingParams(BaseModel):
    """Trend following strategy parameters"""
    fast_ma_period: int = Field(default=9, ge=1)
    slow_ma_period: int = Field(default=21, ge=1)
    ma_type: str = Field(default="ema", pattern=r"^(sma|ema|wma)$")
    atr_period: int = Field(default=14, ge=1)
    atr_multiplier: float = Field(default=2.0, ge=0.1)
    trend_filter_period: int = Field(default=200, ge=1)
    entry_type: str = Field(default="crossover", pattern=r"^(crossover|pullback)$")


class AISignalsParams(BaseModel):
    """AI signals strategy parameters"""
    model_type: str = Field(
        default="combined",
        pattern=r"^(price_predictor|sentiment|volatility|combined)$"
    )
    confidence_threshold: float = Field(default=0.7, ge=0.5, le=1.0)
    signal_cooldown: int = Field(default=60, ge=0)
    use_sentiment: bool = Field(default=True)
    use_volume_analysis: bool = Field(default=True)
    lookback_periods: int = Field(default=20, ge=5)


class BacktestRequest(BaseModel):
    """Backtest request schema"""
    strategy_id: UUID
    strategy_params: Dict[str, Any]
    symbol: str
    exchange: str
    start_date: str  # ISO format
    end_date: str
    initial_capital: float = Field(default=10000, gt=0)
    position_size: float = Field(..., gt=0)
    position_size_type: str = Field(default="fixed")
    leverage: int = Field(default=1, ge=1)
    maker_fee: float = Field(default=0.001, ge=0)
    taker_fee: float = Field(default=0.001, ge=0)
    slippage_percent: float = Field(default=0.05, ge=0)


class BacktestResult(BaseModel):
    """Backtest result schema"""
    # Summary
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_percent: float
    
    # Trades
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # Risk metrics
    max_drawdown: float
    max_drawdown_percent: float
    sharpe_ratio: Optional[float]
    sortino_ratio: Optional[float]
    calmar_ratio: Optional[float]
    profit_factor: float
    
    # Per trade metrics
    avg_trade_pnl: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_hold_time_minutes: float
    
    # Timeline
    equity_curve: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]
    monthly_returns: List[Dict[str, Any]]
    
    # Benchmark
    buy_hold_return: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
