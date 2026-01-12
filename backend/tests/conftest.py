"""
Test fixtures and configuration
"""
import os

# Set environment variables BEFORE importing app modules
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-dev-only123")
os.environ.setdefault("JWT_SECRET_KEY", "jwt-secret-key-for-testing1234")
os.environ.setdefault("ENCRYPTION_KEY", "12345678901234567890123456789012")  # 32 bytes
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import asyncio
import pytest
from typing import AsyncGenerator
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.models.user import User
from app.core.security import SecurityManager

# Test database URL (file-based to allow shared access across async connections)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def cleanup_db():
    """Cleanup test database file after session."""
    yield
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest.fixture(scope="function")
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def security_manager():
    """Create security manager instance."""
    return SecurityManager()


@pytest.fixture
async def test_user(db_session: AsyncSession, security_manager: SecurityManager) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=security_manager.hash_password("TestPassword123"),
        is_active=True,
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession, security_manager: SecurityManager) -> User:
    """Create an admin user."""
    user = User(
        id=uuid4(),
        email="admin@example.com",
        username="adminuser",
        full_name="Admin User",
        hashed_password=security_manager.hash_password("AdminPassword123"),
        is_active=True,
        is_superuser=True,
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user
