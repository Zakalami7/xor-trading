"""XOR Trading Platform - Position Routes"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...models.position import Position, PositionStatus
from ...models.user import User
from ...schemas.order import PositionResponse
from ..deps import get_current_user, get_pagination, Pagination

router = APIRouter()


@router.get("", response_model=List[PositionResponse])
async def list_positions(
    bot_id: Optional[UUID] = None,
    status_filter: Optional[PositionStatus] = None,
    pagination: Pagination = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List positions for the current user."""
    query = select(Position).where(Position.user_id == current_user.id)
    
    if bot_id:
        query = query.where(Position.bot_id == bot_id)
    if status_filter:
        query = query.where(Position.status == status_filter)
    
    query = query.order_by(Position.opened_at.desc())
    query = query.offset(pagination.offset).limit(pagination.page_size)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/open", response_model=List[PositionResponse])
async def list_open_positions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all open positions."""
    query = select(Position).where(
        Position.user_id == current_user.id,
        Position.status == PositionStatus.OPEN,
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get position by ID."""
    position = await db.get(Position, position_id)
    if not position or position.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.post("/{position_id}/close")
async def close_position(
    position_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Request to close a position."""
    position = await db.get(Position, position_id)
    if not position or position.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Position not found")
    
    if not position.is_open:
        raise HTTPException(status_code=400, detail="Position is not open")
    
    # In production, this would trigger close order on exchange
    return {"message": "Position close requested", "position_id": str(position_id)}
