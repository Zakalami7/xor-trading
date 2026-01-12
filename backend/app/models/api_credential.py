"""
XOR Trading Platform - API Credential Model
Securely stores encrypted exchange API keys
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..db.base import Base, TimestampMixin, UUIDMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .user import User


class APICredential(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Encrypted exchange API credentials.
    
    Security measures:
    - API keys encrypted with AES-256-GCM
    - User-specific encryption context
    - No withdrawal permissions stored
    - Access logging for auditing
    """
    
    __tablename__ = "api_credentials"
    __allow_unmapped__ = True
    
    # Ownership
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Exchange
    exchange = Column(String(50), nullable=False, index=True)  # binance, bybit, okx, etc.
    
    # Friendly name
    name = Column(String(100), nullable=False)
    
    # Encrypted credentials
    # These are encrypted with AES-256-GCM using user-specific context
    api_key_encrypted = Column(Text, nullable=False)
    api_secret_encrypted = Column(Text, nullable=False)
    passphrase_encrypted = Column(Text, nullable=True)  # For OKX and others that require it
    
    # API key metadata (not encrypted, for display)
    api_key_last4 = Column(String(4), nullable=True)  # Last 4 chars for identification
    
    # Permissions (verified from exchange)
    permissions = Column(
        JSON,
        default={
            "spot": False,
            "futures": False,
            "margin": False,
            "withdrawal": False,  # Should always be False!
        },
        nullable=False,
    )
    
    # Validation status
    is_valid = Column(Boolean, default=False, nullable=False)
    last_validated = Column(DateTime(timezone=True), nullable=True)
    validation_error = Column(Text, nullable=True)
    
    # IP whitelist (recommended)
    ip_whitelist = Column(JSON, default=list, nullable=False)
    
    # Usage tracking
    last_used = Column(DateTime(timezone=True), nullable=True)
    total_requests = Column(JSON, default=dict, nullable=False)
    
    # Rate limit tracking
    rate_limit_remaining = Column(JSON, nullable=True)
    
    # Testnet/Live
    is_testnet = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="api_credentials")
    
    def __repr__(self) -> str:
        return f"<APICredential {self.exchange}:{self.name}>"
    
    @property
    def is_safe(self) -> bool:
        """Check if credentials follow security best practices"""
        # No withdrawal permission
        if self.permissions.get("withdrawal", False):
            return False
        
        # Has IP whitelist (at least one IP)
        if not self.ip_whitelist:
            return False
        
        return True
    
    def update_last_used(self):
        """Update last used timestamp and increment counter"""
        self.last_used = datetime.utcnow()
        if not self.total_requests or "total" not in self.total_requests:
            self.total_requests = {"total": 0}
        self.total_requests["total"] += 1
