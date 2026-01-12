"""
XOR Trading Platform - Bot Routes
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.events import EventType, get_event_bus
from ...db.session import get_db
from ...models.bot import Bot, BotStatus
from ...models.order import Order, OrderStatus
from ...models.position import Position, PositionStatus
from ...models.user import User
from ...schemas.bot import (
    BotAction,
    BotCreate,
    BotResponse,
    BotUpdate,
    BotWithStats,
)
from ..deps import get_current_user, get_pagination, Pagination

router = APIRouter()


@router.get("", response_model=List[BotWithStats])
async def list_bots(
    status_filter: BotStatus = None,
    pagination: Pagination = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all bots for the current user.
    """
    query = select(Bot).where(
        Bot.user_id == current_user.id,
        Bot.deleted_at.is_(None),
    )
    
    if status_filter:
        query = query.where(Bot.status == status_filter)
    
    query = query.offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(query)
    bots = result.scalars().all()
    
    # Enrich with open positions and pending orders count
    enriched_bots = []
    for bot in bots:
        # Count open positions
        pos_query = select(func.count(Position.id)).where(
            Position.bot_id == bot.id,
            Position.status == PositionStatus.OPEN,
        )
        pos_result = await db.execute(pos_query)
        open_positions = pos_result.scalar() or 0
        
        # Count pending orders
        ord_query = select(func.count(Order.id)).where(
            Order.bot_id == bot.id,
            Order.status.in_([OrderStatus.PENDING, OrderStatus.OPEN]),
        )
        ord_result = await db.execute(ord_query)
        pending_orders = ord_result.scalar() or 0
        
        bot_dict = {
            **bot.__dict__,
            "win_rate": bot.win_rate,
            "runtime_seconds": bot.runtime_seconds,
            "open_positions": open_positions,
            "pending_orders": pending_orders,
        }
        enriched_bots.append(bot_dict)
    
    return enriched_bots


@router.post("", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_create: BotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new trading bot.
    """
    # Parse symbol into base/quote
    symbol = bot_create.symbol.upper()
    # Simple parsing - in production would use exchange-specific parsing
    if "USDT" in symbol:
        base_asset = symbol.replace("USDT", "")
        quote_asset = "USDT"
    elif "USDC" in symbol:
        base_asset = symbol.replace("USDC", "")
        quote_asset = "USDC"
    elif "BTC" in symbol:
        base_asset = symbol.replace("BTC", "")
        quote_asset = "BTC"
    else:
        base_asset = symbol[:3]
        quote_asset = symbol[3:]
    
    bot = Bot(
        user_id=current_user.id,
        name=bot_create.name,
        description=bot_create.description,
        exchange=bot_create.exchange,
        api_credential_id=bot_create.api_credential_id,
        symbol=symbol,
        base_asset=base_asset,
        quote_asset=quote_asset,
        market_type=bot_create.market_type,
        strategy_id=bot_create.strategy_id,
        strategy_params=bot_create.strategy_params,
        position_size=bot_create.position_size,
        position_size_type=bot_create.position_size_type,
        max_positions=bot_create.max_positions,
        leverage=bot_create.leverage,
        margin_type=bot_create.margin_type,
        max_drawdown_percent=bot_create.max_drawdown_percent,
        stop_loss_percent=bot_create.stop_loss_percent,
        take_profit_percent=bot_create.take_profit_percent,
        trailing_stop_percent=bot_create.trailing_stop_percent,
    )
    
    db.add(bot)
    await db.commit()
    await db.refresh(bot)
    
    # Emit event
    event_bus = get_event_bus()
    await event_bus.emit(
        EventType.BOT_CREATED,
        {"bot_id": str(bot.id), "user_id": str(current_user.id)},
    )
    
    return bot


@router.get("/{bot_id}", response_model=BotWithStats)
async def get_bot(
    bot_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get bot details by ID.
    """
    bot = await db.get(Bot, bot_id)
    
    if not bot or bot.user_id != current_user.id or bot.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found",
        )
    
    # Count open positions
    pos_query = select(func.count(Position.id)).where(
        Position.bot_id == bot.id,
        Position.status == PositionStatus.OPEN,
    )
    pos_result = await db.execute(pos_query)
    open_positions = pos_result.scalar() or 0
    
    # Count pending orders
    ord_query = select(func.count(Order.id)).where(
        Order.bot_id == bot.id,
        Order.status.in_([OrderStatus.PENDING, OrderStatus.OPEN]),
    )
    ord_result = await db.execute(ord_query)
    pending_orders = ord_result.scalar() or 0
    
    return {
        **bot.__dict__,
        "win_rate": bot.win_rate,
        "runtime_seconds": bot.runtime_seconds,
        "open_positions": open_positions,
        "pending_orders": pending_orders,
    }


@router.patch("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: UUID,
    bot_update: BotUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update bot configuration.
    Only allowed when bot is stopped.
    """
    bot = await db.get(Bot, bot_id)
    
    if not bot or bot.user_id != current_user.id or bot.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found",
        )
    
    # Can only update stopped bots
    if bot.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a running bot. Stop it first.",
        )
    
    update_data = bot_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bot, field, value)
    
    await db.commit()
    await db.refresh(bot)
    
    return bot


@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a bot (soft delete).
    Must be stopped first.
    """
    bot = await db.get(Bot, bot_id)
    
    if not bot or bot.user_id != current_user.id or bot.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found",
        )
    
    if bot.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a running bot. Stop it first.",
        )
    
    bot.soft_delete()
    await db.commit()
    
    return {"message": "Bot deleted successfully"}


@router.post("/{bot_id}/action")
async def bot_action(
    bot_id: UUID,
    action: BotAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Perform an action on a bot (start/stop/pause/resume).
    """
    bot = await db.get(Bot, bot_id)
    
    if not bot or bot.user_id != current_user.id or bot.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found",
        )
    
    event_bus = get_event_bus()
    
    if action.action == "start":
        if bot.status in (BotStatus.RUNNING, BotStatus.STARTING):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is already running",
            )
        
        bot.status = BotStatus.STARTING
        bot.status_message = "Starting bot..."
        
        await event_bus.emit(
            EventType.BOT_STARTED,
            {"bot_id": str(bot.id), "user_id": str(current_user.id)},
        )
        
    elif action.action == "stop":
        if bot.status in (BotStatus.STOPPED, BotStatus.CREATED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is not running",
            )
        
        bot.status = BotStatus.STOPPING
        bot.status_message = action.reason or "Stopping bot..."
        
        await event_bus.emit(
            EventType.BOT_STOPPED,
            {"bot_id": str(bot.id), "reason": action.reason},
        )
        
    elif action.action == "pause":
        if bot.status != BotStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only pause a running bot",
            )
        
        bot.status = BotStatus.PAUSED
        bot.status_message = "Paused by user"
        
    elif action.action == "resume":
        if bot.status != BotStatus.PAUSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only resume a paused bot",
            )
        
        bot.status = BotStatus.RUNNING
        bot.status_message = "Resumed"
    
    await db.commit()
    
    return {"message": f"Bot {action.action} initiated", "status": bot.status.value}


@router.get("/{bot_id}/logs")
async def get_bot_logs(
    bot_id: UUID,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get recent logs for a bot.
    """
    bot = await db.get(Bot, bot_id)
    
    if not bot or bot.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found",
        )
    
    # In production, this would query a logging system
    # For now, return placeholder
    return {
        "bot_id": str(bot_id),
        "logs": [],
        "message": "Logs would be retrieved from logging system",
    }
