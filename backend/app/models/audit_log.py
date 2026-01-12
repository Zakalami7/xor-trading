"""
XOR Trading Platform - Audit Log Model
Immutable audit trail for security-sensitive operations
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID

from ..db.base import Base, UUIDMixin


class AuditLog(Base, UUIDMixin):
    """
    Immutable audit log for security and compliance.
    All sensitive operations are logged here.
    """
    
    __tablename__ = "audit_logs"
    __allow_unmapped__ = True
    
    # Time
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    
    # User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Action
    action = Column(String(100), nullable=False, index=True)
    # Examples: login, logout, api_key_created, bot_started, order_placed, settings_changed
    
    # Resource
    resource_type = Column(String(50), nullable=False, index=True)
    # Examples: user, bot, order, api_credential, position
    
    resource_id = Column(String(100), nullable=True, index=True)
    
    # Request info
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    
    # Details
    details = Column(JSON, default=dict, nullable=False)
    
    # Outcome
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Request ID for tracing
    request_id = Column(String(100), nullable=True, index=True)
    
    def __repr__(self) -> str:
        return f"<AuditLog {self.action} on {self.resource_type}:{self.resource_id}>"
    
    # Note: This table should be append-only (no updates/deletes in application code)
    # Consider partitioning by timestamp for large deployments
