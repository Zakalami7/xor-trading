"""
XOR Trading Platform - User Service
Business logic for user operations
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import AuthManager, MFAManager
from ..core.security import SecurityManager
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate


class UserService:
    """User business logic service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.security = SecurityManager()
        self.auth = AuthManager()
        self.mfa = MFAManager()
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return await self.db.get(User, user_id)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def create(self, user_data: UserCreate) -> User:
        """Create a new user."""
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=self.security.hash_password(user_data.password),
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def update(self, user: User, update_data: UserUpdate) -> User:
        """Update user profile."""
        data = update_data.model_dump(exclude_unset=True)
        
        for field, value in data.items():
            setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password."""
        user = await self.get_by_email(email)
        
        if not user:
            return None
        
        if not self.security.verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def update_last_login(self, user: User, ip_address: str):
        """Update user's last login info."""
        user.last_login = datetime.utcnow()
        user.last_login_ip = ip_address
        await self.db.commit()
    
    async def change_password(self, user: User, new_password: str):
        """Change user's password."""
        user.hashed_password = self.security.hash_password(new_password)
        await self.db.commit()
    
    async def setup_mfa(self, user: User) -> dict:
        """Initialize MFA setup."""
        secret = self.mfa.generate_secret()
        provisioning_uri = self.mfa.get_provisioning_uri(secret, user.email)
        backup_codes = self.mfa.generate_backup_codes()
        
        # Store encrypted secret
        user.mfa_secret_encrypted = self.mfa.encrypt_secret(secret, str(user.id))
        await self.db.commit()
        
        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "backup_codes": backup_codes,
        }
    
    async def verify_mfa(self, user: User, code: str) -> bool:
        """Verify MFA code."""
        if not user.mfa_secret_encrypted:
            return False
        
        secret = self.mfa.decrypt_secret(user.mfa_secret_encrypted, str(user.id))
        return self.mfa.verify_code(secret, code)
    
    async def enable_mfa(self, user: User):
        """Enable MFA after verification."""
        user.mfa_enabled = True
        await self.db.commit()
    
    async def disable_mfa(self, user: User):
        """Disable MFA."""
        user.mfa_enabled = False
        user.mfa_secret_encrypted = None
        user.mfa_backup_codes = None
        await self.db.commit()
    
    async def deactivate(self, user: User):
        """Deactivate user account."""
        user.is_active = False
        await self.db.commit()
