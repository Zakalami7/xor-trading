"""
Tests for user service
"""
import pytest
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.user_service import UserService
from app.schemas.user import UserCreate


class TestUserService:
    """Test UserService class."""
    
    @pytest.fixture
    def user_service(self, db_session: AsyncSession):
        return UserService(db_session)
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, user_service: UserService, test_user: User):
        """Test get user by ID."""
        user = await user_service.get_by_id(test_user.id)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, user_service: UserService):
        """Test get user by non-existent ID."""
        user = await user_service.get_by_id(uuid4())
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_by_email(self, user_service: UserService, test_user: User):
        """Test get user by email."""
        user = await user_service.get_by_email(test_user.email)
        
        assert user is not None
        assert user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_get_by_username(self, user_service: UserService, test_user: User):
        """Test get user by username."""
        user = await user_service.get_by_username(test_user.username)
        
        assert user is not None
        assert user.username == test_user.username
    
    @pytest.mark.asyncio
    async def test_create(self, user_service: UserService, db_session: AsyncSession):
        """Test user creation."""
        user_data = UserCreate(
            email="newuser@example.com",
            username="newuser",
            password="SecurePassword123",
            full_name="New User",
        )
        
        user = await user_service.create(user_data)
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        assert user.hashed_password != "SecurePassword123"
        assert user.is_active is True
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self, user_service: UserService, test_user: User):
        """Test successful authentication."""
        user = await user_service.authenticate(
            email=test_user.email,
            password="TestPassword123",
        )
        
        assert user is not None
        assert user.id == test_user.id
    
    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, user_service: UserService, test_user: User):
        """Test authentication with wrong password."""
        user = await user_service.authenticate(
            email=test_user.email,
            password="WrongPassword",
        )
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_wrong_email(self, user_service: UserService):
        """Test authentication with non-existent email."""
        user = await user_service.authenticate(
            email="nonexistent@example.com",
            password="AnyPassword",
        )
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_change_password(self, user_service: UserService, test_user: User):
        """Test password change."""
        new_password = "NewSecurePassword456"
        await user_service.change_password(test_user, new_password)
        
        # Should be able to authenticate with new password
        user = await user_service.authenticate(
            email=test_user.email,
            password=new_password,
        )
        
        assert user is not None
    
    @pytest.mark.asyncio
    async def test_deactivate(self, user_service: UserService, test_user: User, db_session: AsyncSession):
        """Test user deactivation."""
        await user_service.deactivate(test_user)
        
        # Refresh from DB
        await db_session.refresh(test_user)
        
        assert test_user.is_active is False
