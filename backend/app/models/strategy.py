"""
XOR Trading Platform - Strategy Model
"""
from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum

from ..db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .bot import Bot


class StrategyType(str, Enum):
    """Built-in strategy types"""
    GRID = "grid"                    # Grid trading
    DCA = "dca"                      # Dollar Cost Averaging
    SCALPING = "scalping"            # High-frequency scalping
    TREND_FOLLOWING = "trend_following"  # Trend following
    MEAN_REVERSION = "mean_reversion"    # Mean reversion
    AI_SIGNALS = "ai_signals"        # AI-based signals
    CUSTOM = "custom"                # User-defined


class Strategy(Base, UUIDMixin, TimestampMixin):
    """Trading strategy configuration"""
    
    __tablename__ = "strategies"
    __allow_unmapped__ = True
    
    # Basic info
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Type
    type = Column(
        SQLEnum(StrategyType, name="strategy_type"),
        nullable=False,
        index=True,
    )
    
    # System strategy (built-in)
    is_system = Column(Boolean, default=False, nullable=False)
    
    # Configuration schema
    # Defines the parameters the strategy accepts
    config_schema = Column(
        JSON,
        nullable=False,
        default={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
    
    # Default parameters
    default_params = Column(JSON, default=dict, nullable=False)
    
    # Supported features
    supported_markets = Column(
        JSON,
        default=["spot", "futures"],
        nullable=False,
    )
    
    # Risk profile
    risk_level = Column(String(20), default="medium", nullable=False)  # low, medium, high
    
    # Code/Logic (for custom strategies)
    # Stores the strategy logic as a Python expression or references
    logic = Column(JSON, nullable=True)
    
    # Indicators used
    indicators = Column(JSON, default=list, nullable=False)
    
    # Relationships
    bots = relationship("Bot", back_populates="strategy", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<Strategy {self.name} ({self.type.value})>"


# Pre-defined strategy configurations
GRID_STRATEGY_SCHEMA = {
    "type": "object",
    "properties": {
        "grid_type": {
            "type": "string",
            "enum": ["arithmetic", "geometric"],
            "default": "arithmetic",
            "description": "Grid spacing type",
        },
        "upper_price": {
            "type": "number",
            "minimum": 0,
            "description": "Upper price bound",
        },
        "lower_price": {
            "type": "number",
            "minimum": 0,
            "description": "Lower price bound",
        },
        "grid_count": {
            "type": "integer",
            "minimum": 2,
            "maximum": 200,
            "default": 10,
            "description": "Number of grid levels",
        },
        "order_size": {
            "type": "number",
            "minimum": 0,
            "description": "Size per grid order",
        },
        "trigger_price": {
            "type": "number",
            "description": "Price to start the grid (optional)",
        },
    },
    "required": ["upper_price", "lower_price", "grid_count", "order_size"],
}

DCA_STRATEGY_SCHEMA = {
    "type": "object",
    "properties": {
        "base_order_size": {
            "type": "number",
            "minimum": 0,
            "description": "Initial order size",
        },
        "safety_order_size": {
            "type": "number",
            "minimum": 0,
            "description": "Safety order size",
        },
        "max_safety_orders": {
            "type": "integer",
            "minimum": 1,
            "maximum": 50,
            "default": 5,
            "description": "Maximum safety orders",
        },
        "price_deviation_percent": {
            "type": "number",
            "minimum": 0.1,
            "maximum": 50,
            "default": 1.0,
            "description": "Price deviation to trigger safety order (%)",
        },
        "safety_order_step_scale": {
            "type": "number",
            "minimum": 1,
            "default": 1.0,
            "description": "Safety order step scale (multiplier)",
        },
        "safety_order_volume_scale": {
            "type": "number",
            "minimum": 1,
            "default": 1.0,
            "description": "Safety order volume scale (multiplier)",
        },
        "take_profit_percent": {
            "type": "number",
            "minimum": 0.1,
            "default": 1.5,
            "description": "Take profit target (%)",
        },
        "stop_loss_percent": {
            "type": "number",
            "minimum": 0,
            "description": "Stop loss (%)",
        },
        "trailing_take_profit": {
            "type": "boolean",
            "default": False,
            "description": "Enable trailing take profit",
        },
    },
    "required": ["base_order_size", "safety_order_size", "take_profit_percent"],
}

SCALPING_STRATEGY_SCHEMA = {
    "type": "object",
    "properties": {
        "spread_threshold": {
            "type": "number",
            "minimum": 0,
            "description": "Minimum spread to enter (%)",
        },
        "position_time_limit": {
            "type": "integer",
            "minimum": 1,
            "description": "Max position hold time (seconds)",
        },
        "take_profit_ticks": {
            "type": "integer",
            "minimum": 1,
            "description": "Take profit in ticks",
        },
        "stop_loss_ticks": {
            "type": "integer",
            "minimum": 1,
            "description": "Stop loss in ticks",
        },
        "order_book_imbalance_threshold": {
            "type": "number",
            "minimum": 1,
            "default": 2.0,
            "description": "Order book imbalance ratio threshold",
        },
        "volume_filter": {
            "type": "number",
            "minimum": 0,
            "description": "Minimum volume filter",
        },
        "use_market_orders": {
            "type": "boolean",
            "default": True,
            "description": "Use market orders for faster execution",
        },
    },
    "required": ["spread_threshold", "take_profit_ticks", "stop_loss_ticks"],
}

TREND_FOLLOWING_SCHEMA = {
    "type": "object",
    "properties": {
        "fast_ma_period": {
            "type": "integer",
            "minimum": 1,
            "default": 9,
            "description": "Fast moving average period",
        },
        "slow_ma_period": {
            "type": "integer",
            "minimum": 1,
            "default": 21,
            "description": "Slow moving average period",
        },
        "ma_type": {
            "type": "string",
            "enum": ["sma", "ema", "wma"],
            "default": "ema",
            "description": "Moving average type",
        },
        "atr_period": {
            "type": "integer",
            "minimum": 1,
            "default": 14,
            "description": "ATR period for volatility",
        },
        "atr_multiplier": {
            "type": "number",
            "minimum": 0.1,
            "default": 2.0,
            "description": "ATR multiplier for stop loss",
        },
        "trend_filter_period": {
            "type": "integer",
            "minimum": 1,
            "default": 200,
            "description": "Long-term trend filter period",
        },
        "entry_type": {
            "type": "string",
            "enum": ["crossover", "pullback"],
            "default": "crossover",
            "description": "Entry signal type",
        },
    },
    "required": ["fast_ma_period", "slow_ma_period"],
}

AI_SIGNALS_SCHEMA = {
    "type": "object",
    "properties": {
        "model_type": {
            "type": "string",
            "enum": ["price_predictor", "sentiment", "volatility", "combined"],
            "default": "combined",
            "description": "AI model type",
        },
        "confidence_threshold": {
            "type": "number",
            "minimum": 0.5,
            "maximum": 1.0,
            "default": 0.7,
            "description": "Minimum confidence for signals",
        },
        "signal_cooldown": {
            "type": "integer",
            "minimum": 0,
            "default": 60,
            "description": "Cooldown between signals (seconds)",
        },
        "use_sentiment": {
            "type": "boolean",
            "default": True,
            "description": "Include sentiment analysis",
        },
        "use_volume_analysis": {
            "type": "boolean",
            "default": True,
            "description": "Include volume analysis",
        },
    },
    "required": ["confidence_threshold"],
}
