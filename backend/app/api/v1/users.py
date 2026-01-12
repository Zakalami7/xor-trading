"""
XOR Trading Platform - User Routes
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...models.user import User
from ...schemas.user import RiskSettingsUpdate, UserResponse, UserUpdate
from ..deps import get_current_user, get_current_superuser, get_pagination, Pagination

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current user profile.
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user profile.
    """
    update_data = user_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.patch("/me/risk-settings", response_model=UserResponse)
async def update_risk_settings(
    settings: RiskSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user's risk management settings.
    """
    update_data = settings.model_dump(exclude_unset=True)
    
    # Merge with existing settings
    risk_settings = current_user.risk_settings.copy()
    risk_settings.update(update_data)
    current_user.risk_settings = risk_settings
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.delete("/me")
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete current user account.
    This is a soft delete - account is deactivated.
    """
    current_user.is_active = False
    await db.commit()
    
    return {"message": "Account deactivated successfully"}


# Admin routes

@router.get("", response_model=List[UserResponse])
async def list_users(
    pagination: Pagination = Depends(get_pagination),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    List all users (admin only).
    """
    query = select(User).offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user by ID (admin only).
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.patch("/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Activate a user account (admin only).
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user.is_active = True
    await db.commit()
    
    return {"message": "User activated"}


@router.patch("/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate a user account (admin only).
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )
    
    user.is_active = False
    await db.commit()
    
    return {"message": "User deactivated"}
