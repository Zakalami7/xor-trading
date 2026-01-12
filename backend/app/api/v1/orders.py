"""
XOR Trading Platform - Order Routes
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...models.order import Order, OrderStatus
from ...models.user import User
from ...schemas.order import OrderResponse
from ..deps import get_current_user, get_pagination, Pagination

router = APIRouter()


@router.get("", response_model=List[OrderResponse])
async def list_orders(
    bot_id: Optional[UUID] = None,
    status_filter: Optional[OrderStatus] = None,
    pagination: Pagination = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List orders for the current user."""
    query = select(Order).where(Order.user_id == current_user.id)
    
    if bot_id:
        query = query.where(Order.bot_id == bot_id)
    if status_filter:
        query = query.where(Order.status == status_filter)
    
    query = query.order_by(Order.created_at.desc())
    query = query.offset(pagination.offset).limit(pagination.page_size)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get order by ID."""
    order = await db.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an open order."""
    order = await db.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if not order.is_open:
        raise HTTPException(status_code=400, detail="Order is not open")
    
    order.status = OrderStatus.CANCELLED
    await db.commit()
    return {"message": "Order cancelled"}
