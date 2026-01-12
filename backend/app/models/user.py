"""
XOR Trading Platform - User Model
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, String, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped

from ..db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .bot import Bot
    from .api_credential import APICredential


class User(Base, UUIDMixin, TimestampMixin):
    """User model for authentication and ownership"""
    
    __tablename__ = "users"
    __allow_unmapped__ = True  # Allow legacy annotations
    
    # Authentication
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # MFA
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret_encrypted = Column(Text, nullable=True)  # Encrypted TOTP secret
    mfa_backup_codes = Column(JSON, nullable=True)  # Encrypted backup codes
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Verification
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Password reset
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Last activity
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)  # IPv6 compatible
    
    # Settings
    settings = Column(JSON, default=dict, nullable=False)
    
    # Risk settings
    risk_settings = Column(
        JSON,
        default={
            "max_drawdown_percent": 10.0,
            "max_position_size_percent": 5.0,
            "daily_loss_limit_percent": 3.0,
            "max_leverage": 10,
            "kill_switch_enabled": True,
        },
        nullable=False,
    )
    
    # Relationships
    bots = relationship("Bot", back_populates="user", lazy="dynamic")
    api_credentials = relationship(
        "APICredential",
        back_populates="user",
        lazy="dynamic",
    )
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"
    
    @property
    def display_name(self) -> str:
        return self.full_name or self.username
