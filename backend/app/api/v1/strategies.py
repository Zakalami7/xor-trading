"""
XOR Trading Platform - Strategy Routes
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...models.strategy import (
    Strategy,
    StrategyType,
    GRID_STRATEGY_SCHEMA,
    DCA_STRATEGY_SCHEMA,
    SCALPING_STRATEGY_SCHEMA,
    TREND_FOLLOWING_SCHEMA,
    AI_SIGNALS_SCHEMA,
)
from ...models.user import User
from ...schemas.strategy import StrategyResponse
from ..deps import get_current_user

router = APIRouter()


@router.get("", response_model=List[StrategyResponse])
async def list_strategies(
    strategy_type: StrategyType = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all available strategies.
    Includes both system strategies and user-created ones.
    """
    query = select(Strategy)
    
    if strategy_type:
        query = query.where(Strategy.type == strategy_type)
    
    # Show system strategies + user's own strategies
    query = query.where(
        (Strategy.is_system == True) | 
        (Strategy.is_system == False)  # In production: filter by user
    )
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get strategy details by ID.
    """
    strategy = await db.get(Strategy, strategy_id)
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found",
        )
    
    return strategy


@router.get("/type/{strategy_type}/schema")
async def get_strategy_schema(
    strategy_type: StrategyType,
    current_user: User = Depends(get_current_user),
):
    """
    Get the configuration schema for a strategy type.
    """
    schemas = {
        StrategyType.GRID: GRID_STRATEGY_SCHEMA,
        StrategyType.DCA: DCA_STRATEGY_SCHEMA,
        StrategyType.SCALPING: SCALPING_STRATEGY_SCHEMA,
        StrategyType.TREND_FOLLOWING: TREND_FOLLOWING_SCHEMA,
        StrategyType.AI_SIGNALS: AI_SIGNALS_SCHEMA,
    }
    
    if strategy_type not in schemas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No schema for strategy type: {strategy_type.value}",
        )
    
    return {
        "type": strategy_type.value,
        "schema": schemas[strategy_type],
    }


@router.post("/validate")
async def validate_strategy_params(
    strategy_type: StrategyType,
    params: dict,
    current_user: User = Depends(get_current_user),
):
    """
    Validate strategy parameters against schema.
    """
    from jsonschema import validate, ValidationError
    
    schemas = {
        StrategyType.GRID: GRID_STRATEGY_SCHEMA,
        StrategyType.DCA: DCA_STRATEGY_SCHEMA,
        StrategyType.SCALPING: SCALPING_STRATEGY_SCHEMA,
        StrategyType.TREND_FOLLOWING: TREND_FOLLOWING_SCHEMA,
        StrategyType.AI_SIGNALS: AI_SIGNALS_SCHEMA,
    }
    
    schema = schemas.get(strategy_type)
    if not schema:
        return {"valid": False, "error": f"Unknown strategy type: {strategy_type.value}"}
    
    try:
        validate(instance=params, schema=schema)
        return {"valid": True, "params": params}
    except ValidationError as e:
        return {"valid": False, "error": str(e.message), "path": list(e.path)}


# Initialize system strategies on startup
async def init_system_strategies(db: AsyncSession):
    """Initialize built-in system strategies"""
    
    system_strategies = [
        {
            "name": "Grid Trading",
            "description": "Automatically place buy and sell orders at predefined price intervals. Profits from market volatility within a range.",
            "type": StrategyType.GRID,
            "is_system": True,
            "config_schema": GRID_STRATEGY_SCHEMA,
            "default_params": {
                "grid_type": "arithmetic",
                "grid_count": 10,
            },
            "supported_markets": ["spot", "futures"],
            "risk_level": "medium",
            "indicators": [],
        },
        {
            "name": "DCA (Dollar Cost Averaging)",
            "description": "Reduce average entry price by buying more as price drops. Includes safety orders and take profit.",
            "type": StrategyType.DCA,
            "is_system": True,
            "config_schema": DCA_STRATEGY_SCHEMA,
            "default_params": {
                "max_safety_orders": 5,
                "price_deviation_percent": 1.0,
                "safety_order_step_scale": 1.0,
                "safety_order_volume_scale": 1.0,
                "take_profit_percent": 1.5,
            },
            "supported_markets": ["spot", "futures"],
            "risk_level": "medium",
            "indicators": [],
        },
        {
            "name": "Scalping",
            "description": "High-frequency trading strategy for quick profits from small price movements.",
            "type": StrategyType.SCALPING,
            "is_system": True,
            "config_schema": SCALPING_STRATEGY_SCHEMA,
            "default_params": {
                "position_time_limit": 60,
                "order_book_imbalance_threshold": 2.0,
                "use_market_orders": True,
            },
            "supported_markets": ["spot", "futures"],
            "risk_level": "high",
            "indicators": ["order_book", "volume"],
        },
        {
            "name": "Trend Following",
            "description": "Follow market trends using moving average crossovers with ATR-based risk management.",
            "type": StrategyType.TREND_FOLLOWING,
            "is_system": True,
            "config_schema": TREND_FOLLOWING_SCHEMA,
            "default_params": {
                "fast_ma_period": 9,
                "slow_ma_period": 21,
                "ma_type": "ema",
                "atr_period": 14,
                "atr_multiplier": 2.0,
                "trend_filter_period": 200,
                "entry_type": "crossover",
            },
            "supported_markets": ["spot", "futures"],
            "risk_level": "medium",
            "indicators": ["ma", "atr"],
        },
        {
            "name": "AI Signals",
            "description": "AI-powered trading signals using machine learning for price prediction and sentiment analysis.",
            "type": StrategyType.AI_SIGNALS,
            "is_system": True,
            "config_schema": AI_SIGNALS_SCHEMA,
            "default_params": {
                "model_type": "combined",
                "confidence_threshold": 0.7,
                "signal_cooldown": 60,
                "use_sentiment": True,
                "use_volume_analysis": True,
            },
            "supported_markets": ["spot", "futures"],
            "risk_level": "medium",
            "indicators": ["ai_prediction", "sentiment", "volume"],
        },
    ]
    
    for strategy_data in system_strategies:
        # Check if exists
        result = await db.execute(
            select(Strategy).where(
                Strategy.name == strategy_data["name"],
                Strategy.is_system == True,
            )
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            strategy = Strategy(**strategy_data)
            db.add(strategy)
    
    await db.commit()
