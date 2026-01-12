"""
XOR Trading Platform - Authentication Routes
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.auth import AuthManager, MFAManager, TokenPair
from ...core.security import SecurityManager
from ...db.session import get_db
from ...models.user import User
from ...schemas.common import TokenResponse
from ...schemas.user import (
    MFASetup,
    MFAVerify,
    PasswordChange,
    UserCreate,
    UserLogin,
    UserResponse,
)
from ..deps import get_client_ip, get_current_user, get_user_agent

router = APIRouter()
auth_manager = AuthManager()
mfa_manager = MFAManager()
security_manager = SecurityManager()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account.
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_create.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    
    # Check if username exists
    result = await db.execute(
        select(User).where(User.username == user_create.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )
    
    # Create user
    user = User(
        email=user_create.email,
        username=user_create.username,
        full_name=user_create.full_name,
        hashed_password=security_manager.hash_password(user_create.password),
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
    client_ip: str = Depends(get_client_ip),
):
    """
    Login with email and password.
    Returns access and refresh tokens.
    """
    # Find user
    result = await db.execute(
        select(User).where(User.email == login_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Verify password
    if not security_manager.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    
    # Check MFA if enabled
    if user.mfa_enabled:
        if not login_data.mfa_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA code required",
                headers={"X-MFA-Required": "true"},
            )
        
        # Decrypt and verify MFA
        try:
            secret = mfa_manager.decrypt_secret(
                user.mfa_secret_encrypted,
                str(user.id),
            )
            if not mfa_manager.verify_code(secret, login_data.mfa_code):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid MFA code",
                )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA verification failed",
            )
    
    # Update last login
    user.last_login = datetime.utcnow()
    user.last_login_ip = client_ip
    await db.commit()
    
    # Generate tokens
    token_pair = auth_manager.create_token_pair(
        user_id=str(user.id),
        roles=["user"] + (["admin"] if user.is_superuser else []),
    )
    
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        expires_in=token_pair.expires_in,
        refresh_expires_in=token_pair.refresh_expires_in,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    """
    payload = auth_manager.verify_token(refresh_token, token_type="refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    # Get user
    user = await db.get(User, payload.sub)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Generate new token pair
    token_pair = auth_manager.refresh_access_token(
        refresh_token,
        roles=["user"] + (["admin"] if user.is_superuser else []),
    )
    
    if not token_pair:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed",
        )
    
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        expires_in=token_pair.expires_in,
        refresh_expires_in=token_pair.refresh_expires_in,
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
):
    """
    Logout and invalidate current token.
    """
    # In production with Redis, we would add the token to a blacklist
    return {"message": "Successfully logged out"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change current user's password.
    """
    # Verify current password
    if not security_manager.verify_password(
        password_data.current_password,
        current_user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    # Update password
    current_user.hashed_password = security_manager.hash_password(
        password_data.new_password
    )
    await db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/mfa/setup", response_model=MFASetup)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Initialize MFA setup. Returns secret and QR code data.
    """
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled",
        )
    
    # Generate secret
    secret = mfa_manager.generate_secret()
    provisioning_uri = mfa_manager.get_provisioning_uri(secret, current_user.email)
    backup_codes = mfa_manager.generate_backup_codes()
    
    # Store encrypted secret temporarily (will be confirmed on verify)
    current_user.mfa_secret_encrypted = mfa_manager.encrypt_secret(
        secret,
        str(current_user.id),
    )
    await db.commit()
    
    return MFASetup(
        secret=secret,
        provisioning_uri=provisioning_uri,
        backup_codes=backup_codes,
    )


@router.post("/mfa/verify")
async def verify_mfa(
    verify_data: MFAVerify,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify MFA code to complete setup.
    """
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled",
        )
    
    if not current_user.mfa_secret_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA setup not initiated",
        )
    
    # Verify code
    secret = mfa_manager.decrypt_secret(
        current_user.mfa_secret_encrypted,
        str(current_user.id),
    )
    
    if not mfa_manager.verify_code(secret, verify_data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA code",
        )
    
    # Enable MFA
    current_user.mfa_enabled = True
    await db.commit()
    
    return {"message": "MFA enabled successfully"}


@router.post("/mfa/disable")
async def disable_mfa(
    verify_data: MFAVerify,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Disable MFA after verifying current code.
    """
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled",
        )
    
    # Verify code
    secret = mfa_manager.decrypt_secret(
        current_user.mfa_secret_encrypted,
        str(current_user.id),
    )
    
    if not mfa_manager.verify_code(secret, verify_data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA code",
        )
    
    # Disable MFA
    current_user.mfa_enabled = False
    current_user.mfa_secret_encrypted = None
    current_user.mfa_backup_codes = None
    await db.commit()
    
    return {"message": "MFA disabled successfully"}
