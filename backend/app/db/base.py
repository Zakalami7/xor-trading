"""
XOR Trading Platform - SQLAlchemy Base Model
Base class with common fields and utilities
"""
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Column, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    """Base class for all database models"""
    
    id: Any
    __name__: str
    __allow_unmapped__ = True  # Allow legacy type annotations without Mapped[]
    
    # Generate __tablename__ automatically from class name
    @declared_attr
    def __tablename__(cls) -> str:
        # Convert CamelCase to snake_case
        name = cls.__name__
        return ''.join(['_' + c.lower() if c.isupper() else c for c in name]).lstrip('_')


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class UUIDMixin:
    """Mixin for UUID primary key"""
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    def soft_delete(self):
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        self.deleted_at = None
