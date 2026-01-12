"""XOR Trading Platform - Analytics Routes"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...models.bot import Bot
from ...models.order import Order, OrderStatus
from ...models.position import Position, PositionStatus
from ...models.trade import Trade
from ...models.user import User
from ..deps import get_current_user

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard statistics."""
    # Active bots
    bots_query = select(func.count(Bot.id)).where(
        Bot.user_id == current_user.id,
        Bot.deleted_at.is_(None),
    )
    total_bots = (await db.execute(bots_query)).scalar() or 0
    
    # Open positions
    pos_query = select(func.count(Position.id)).where(
        Position.user_id == current_user.id,
        Position.status == PositionStatus.OPEN,
    )
    open_positions = (await db.execute(pos_query)).scalar() or 0
    
    # 24h PnL
    yesterday = datetime.utcnow() - timedelta(days=1)
    pnl_query = select(func.sum(Trade.realized_pnl)).where(
        Trade.user_id == current_user.id,
        Trade.executed_at >= yesterday,
    )
    pnl_24h = (await db.execute(pnl_query)).scalar() or 0.0
    
    # Total trades 24h
    trades_query = select(func.count(Trade.id)).where(
        Trade.user_id == current_user.id,
        Trade.executed_at >= yesterday,
    )
    trades_24h = (await db.execute(trades_query)).scalar() or 0
    
    return {
        "total_bots": total_bots,
        "open_positions": open_positions,
        "pnl_24h": pnl_24h,
        "trades_24h": trades_24h,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/pnl")
async def get_pnl_history(
    period: str = Query(default="7d", pattern="^(24h|7d|30d|90d)$"),
    bot_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get PnL history over time."""
    periods = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}
    days = periods.get(period, 7)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = select(Trade).where(
        Trade.user_id == current_user.id,
        Trade.executed_at >= start_date,
    )
    if bot_id:
        query = query.where(Trade.bot_id == bot_id)
    
    query = query.order_by(Trade.executed_at)
    result = await db.execute(query)
    trades = result.scalars().all()
    
    # Build cumulative PnL
    cumulative = 0.0
    history = []
    for trade in trades:
        cumulative += trade.realized_pnl or 0
        history.append({
            "timestamp": trade.executed_at.isoformat(),
            "pnl": trade.realized_pnl,
            "cumulative_pnl": cumulative,
        })
    
    return {"period": period, "total_pnl": cumulative, "history": history}


@router.get("/performance/{bot_id}")
async def get_bot_performance(
    bot_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed bot performance metrics."""
    bot = await db.get(Bot, bot_id)
    if not bot or bot.user_id != current_user.id:
        return {"error": "Bot not found"}
    
    return {
        "bot_id": str(bot_id),
        "name": bot.name,
        "total_trades": bot.total_trades,
        "winning_trades": bot.winning_trades,
        "losing_trades": bot.losing_trades,
        "win_rate": bot.win_rate,
        "total_pnl": bot.total_pnl,
        "total_pnl_percent": bot.total_pnl_percent,
        "max_drawdown": bot.max_drawdown_reached,
        "total_fees": bot.total_fees,
    }
