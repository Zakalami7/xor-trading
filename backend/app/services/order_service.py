"""
XOR Trading Platform - Order Service
Business logic for order operations
"""
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.events import EventType, get_event_bus
from ..models.order import Order, OrderStatus, OrderType, OrderSide
from ..models.trade import Trade


class OrderService:
    """Order business logic service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.event_bus = get_event_bus()
    
    async def get_by_id(self, order_id: UUID, user_id: UUID) -> Optional[Order]:
        """Get order by ID (owned by user)."""
        order = await self.db.get(Order, order_id)
        if order and order.user_id == user_id:
            return order
        return None
    
    async def list_orders(
        self,
        user_id: UUID,
        bot_id: UUID = None,
        status: OrderStatus = None,
        symbol: str = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Order]:
        """List orders with filters."""
        query = select(Order).where(Order.user_id == user_id)
        
        if bot_id:
            query = query.where(Order.bot_id == bot_id)
        if status:
            query = query.where(Order.status == status)
        if symbol:
            query = query.where(Order.symbol == symbol.upper())
        
        query = query.order_by(Order.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_active_orders(self, user_id: UUID) -> List[Order]:
        """Get all active (open) orders."""
        query = select(Order).where(
            Order.user_id == user_id,
            Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIAL, OrderStatus.SUBMITTED]),
        ).order_by(Order.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create_order(
        self,
        user_id: UUID,
        bot_id: UUID,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float = None,
        stop_price: float = None,
        reduce_only: bool = False,
    ) -> Order:
        """Create a new order."""
        order = Order(
            user_id=user_id,
            bot_id=bot_id,
            symbol=symbol.upper(),
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            reduce_only=reduce_only,
            status=OrderStatus.PENDING,
        )
        
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        
        # Emit for execution engine
        await self.event_bus.emit(EventType.ORDER_PLACED, {
            "order_id": str(order.id),
            "bot_id": str(bot_id),
            "symbol": symbol,
            "side": side.value,
            "type": order_type.value,
            "quantity": quantity,
            "price": price,
        })
        
        return order
    
    async def cancel_order(self, order: Order) -> Order:
        """Request order cancellation."""
        if not order.is_open:
            raise ValueError(f"Cannot cancel order with status: {order.status.value}")
        
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.utcnow()
        
        await self.db.commit()
        
        await self.event_bus.emit(EventType.ORDER_CANCELLED, {
            "order_id": str(order.id),
            "exchange_order_id": order.exchange_order_id,
        })
        
        return order
    
    async def cancel_all_orders(
        self,
        user_id: UUID,
        bot_id: UUID = None,
        symbol: str = None,
    ) -> int:
        """Cancel all open orders."""
        query = select(Order).where(
            Order.user_id == user_id,
            Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIAL]),
        )
        
        if bot_id:
            query = query.where(Order.bot_id == bot_id)
        if symbol:
            query = query.where(Order.symbol == symbol.upper())
        
        result = await self.db.execute(query)
        orders = result.scalars().all()
        
        count = 0
        for order in orders:
            order.status = OrderStatus.CANCELLED
            order.cancelled_at = datetime.utcnow()
            count += 1
        
        await self.db.commit()
        return count
    
    async def update_order_status(
        self,
        order: Order,
        status: OrderStatus,
        filled_quantity: float = None,
        average_price: float = None,
        fee: float = None,
        exchange_order_id: str = None,
    ) -> Order:
        """Update order status from exchange."""
        order.status = status
        
        if filled_quantity is not None:
            order.filled_quantity = filled_quantity
        if average_price is not None:
            order.average_price = average_price
        if fee is not None:
            order.fee = fee
        if exchange_order_id:
            order.exchange_order_id = exchange_order_id
        
        if status == OrderStatus.FILLED:
            order.filled_at = datetime.utcnow()
        
        await self.db.commit()
        
        # Emit event
        await self.event_bus.emit(EventType.ORDER_FILLED, {
            "order_id": str(order.id),
            "status": status.value,
        })
        
        return order
    
    async def get_order_stats(
        self,
        user_id: UUID,
        bot_id: UUID = None,
        period_hours: int = 24,
    ) -> dict:
        """Get order statistics."""
        start_time = datetime.utcnow() - timedelta(hours=period_hours)
        
        query = select(Order).where(
            Order.user_id == user_id,
            Order.created_at >= start_time,
        )
        
        if bot_id:
            query = query.where(Order.bot_id == bot_id)
        
        result = await self.db.execute(query)
        orders = list(result.scalars().all())
        
        filled = [o for o in orders if o.status == OrderStatus.FILLED]
        cancelled = [o for o in orders if o.status == OrderStatus.CANCELLED]
        
        return {
            "total_orders": len(orders),
            "filled_orders": len(filled),
            "cancelled_orders": len(cancelled),
            "fill_rate": len(filled) / len(orders) * 100 if orders else 0,
            "total_volume": sum(o.quote_quantity or 0 for o in filled),
            "total_fees": sum(o.fee for o in filled),
            "avg_latency_ms": sum(o.latency_ms or 0 for o in filled) / len(filled) if filled else 0,
        }
