"""
XOR Trading Platform - Bot Service
Business logic for bot operations
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.events import EventType, get_event_bus
from ..models.bot import Bot, BotStatus
from ..models.order import Order, OrderStatus
from ..models.position import Position, PositionStatus
from ..schemas.bot import BotCreate, BotUpdate


class BotService:
    """Bot business logic service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.event_bus = get_event_bus()
    
    async def get_by_id(self, bot_id: UUID, user_id: UUID) -> Optional[Bot]:
        """Get bot by ID (owned by user)."""
        bot = await self.db.get(Bot, bot_id)
        if bot and bot.user_id == user_id and not bot.deleted_at:
            return bot
        return None
    
    async def list_user_bots(
        self,
        user_id: UUID,
        status: BotStatus = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Bot]:
        """List all bots for a user."""
        query = select(Bot).where(
            Bot.user_id == user_id,
            Bot.deleted_at.is_(None),
        )
        
        if status:
            query = query.where(Bot.status == status)
        
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create(self, user_id: UUID, data: BotCreate) -> Bot:
        """Create a new bot."""
        # Parse symbol
        symbol = data.symbol.upper()
        base_asset, quote_asset = self._parse_symbol(symbol)
        
        bot = Bot(
            user_id=user_id,
            name=data.name,
            description=data.description,
            exchange=data.exchange,
            api_credential_id=data.api_credential_id,
            symbol=symbol,
            base_asset=base_asset,
            quote_asset=quote_asset,
            market_type=data.market_type,
            strategy_id=data.strategy_id,
            strategy_params=data.strategy_params,
            position_size=data.position_size,
            position_size_type=data.position_size_type,
            max_positions=data.max_positions,
            leverage=data.leverage,
            margin_type=data.margin_type,
            max_drawdown_percent=data.max_drawdown_percent,
            stop_loss_percent=data.stop_loss_percent,
            take_profit_percent=data.take_profit_percent,
            trailing_stop_percent=data.trailing_stop_percent,
        )
        
        self.db.add(bot)
        await self.db.commit()
        await self.db.refresh(bot)
        
        # Emit event
        await self.event_bus.emit(EventType.BOT_CREATED, {
            "bot_id": str(bot.id),
            "user_id": str(user_id),
        })
        
        return bot
    
    async def update(self, bot: Bot, data: BotUpdate) -> Bot:
        """Update bot configuration."""
        if bot.is_active:
            raise ValueError("Cannot update a running bot")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(bot, field, value)
        
        await self.db.commit()
        await self.db.refresh(bot)
        
        return bot
    
    async def delete(self, bot: Bot):
        """Soft delete a bot."""
        if bot.is_active:
            raise ValueError("Cannot delete a running bot")
        
        bot.soft_delete()
        await self.db.commit()
    
    async def start(self, bot: Bot):
        """Start a bot."""
        if bot.status in (BotStatus.RUNNING, BotStatus.STARTING):
            raise ValueError("Bot is already running")
        
        bot.status = BotStatus.STARTING
        bot.status_message = "Starting bot..."
        
        await self.db.commit()
        
        await self.event_bus.emit(EventType.BOT_STARTED, {
            "bot_id": str(bot.id),
            "user_id": str(bot.user_id),
        })
    
    async def stop(self, bot: Bot, reason: str = None):
        """Stop a bot."""
        if bot.status in (BotStatus.STOPPED, BotStatus.CREATED):
            raise ValueError("Bot is not running")
        
        bot.status = BotStatus.STOPPING
        bot.status_message = reason or "Stopping bot..."
        
        await self.db.commit()
        
        await self.event_bus.emit(EventType.BOT_STOPPED, {
            "bot_id": str(bot.id),
            "reason": reason,
        })
    
    async def pause(self, bot: Bot):
        """Pause a bot."""
        if bot.status != BotStatus.RUNNING:
            raise ValueError("Can only pause a running bot")
        
        bot.status = BotStatus.PAUSED
        bot.status_message = "Paused by user"
        await self.db.commit()
    
    async def resume(self, bot: Bot):
        """Resume a paused bot."""
        if bot.status != BotStatus.PAUSED:
            raise ValueError("Can only resume a paused bot")
        
        bot.status = BotStatus.RUNNING
        bot.status_message = "Resumed"
        await self.db.commit()
    
    async def get_stats(self, bot: Bot) -> dict:
        """Get bot statistics."""
        # Open positions count
        pos_result = await self.db.execute(
            select(func.count(Position.id)).where(
                Position.bot_id == bot.id,
                Position.status == PositionStatus.OPEN,
            )
        )
        open_positions = pos_result.scalar() or 0
        
        # Pending orders count
        ord_result = await self.db.execute(
            select(func.count(Order.id)).where(
                Order.bot_id == bot.id,
                Order.status.in_([OrderStatus.PENDING, OrderStatus.OPEN]),
            )
        )
        pending_orders = ord_result.scalar() or 0
        
        return {
            "open_positions": open_positions,
            "pending_orders": pending_orders,
            "win_rate": bot.win_rate,
            "total_pnl": bot.total_pnl,
            "total_trades": bot.total_trades,
            "runtime_seconds": bot.runtime_seconds,
        }
    
    def _parse_symbol(self, symbol: str) -> tuple:
        """Parse trading symbol into base and quote assets."""
        for quote in ["USDT", "USDC", "BUSD", "BTC", "ETH"]:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                return base, quote
        return symbol[:3], symbol[3:]
