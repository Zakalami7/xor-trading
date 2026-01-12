"""
XOR Trading Platform - User Schemas
"""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    full_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for user profile update"""
    full_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)
    settings: Optional[Dict[str, Any]] = None


class UserLogin(BaseModel):
    """Schema for login request"""
    email: EmailStr
    password: str
    mfa_code: Optional[str] = Field(None, min_length=6, max_length=6)


class UserResponse(BaseModel):
    """Schema for user response"""
    id: UUID
    email: EmailStr
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    mfa_enabled: bool
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    settings: Dict[str, Any]
    risk_settings: Dict[str, Any]
    
    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class MFASetup(BaseModel):
    """Schema for MFA setup response"""
    secret: str
    provisioning_uri: str
    backup_codes: list[str]


class MFAVerify(BaseModel):
    """Schema for MFA verification"""
    code: str = Field(..., min_length=6, max_length=6)


class RiskSettingsUpdate(BaseModel):
    """Schema for updating risk settings"""
    max_drawdown_percent: Optional[float] = Field(None, ge=1, le=100)
    max_position_size_percent: Optional[float] = Field(None, ge=0.1, le=100)
    daily_loss_limit_percent: Optional[float] = Field(None, ge=0.1, le=100)
    max_leverage: Optional[int] = Field(None, ge=1, le=125)
    kill_switch_enabled: Optional[bool] = None
