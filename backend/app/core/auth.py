"""
XOR Trading Platform - Authentication Module
JWT-based authentication with refresh tokens and MFA support
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

import pyotp
from jose import JWTError, jwt
from pydantic import BaseModel

from ..config import settings
from .security import get_security_manager


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # User ID
    exp: datetime
    iat: datetime
    type: str  # "access" or "refresh"
    jti: str  # JWT ID for revocation
    roles: list[str] = []
    permissions: list[str] = []


class TokenPair(BaseModel):
    """Access and refresh token pair"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


class AuthManager:
    """
    Authentication manager handling JWT tokens and MFA.
    """
    
    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = None,
        access_token_expire_minutes: int = None,
        refresh_token_expire_days: int = None,
    ):
        self.secret_key = secret_key or settings.JWT_SECRET_KEY
        self.algorithm = algorithm or settings.JWT_ALGORITHM
        self.access_token_expire = access_token_expire_minutes or settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire = refresh_token_expire_days or settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        
        # Token blacklist (should use Redis in production)
        self._blacklist: set = set()
    
    def create_token_pair(
        self,
        user_id: str,
        roles: list[str] = None,
        permissions: list[str] = None,
    ) -> TokenPair:
        """Create access and refresh token pair"""
        access_token = self.create_access_token(user_id, roles, permissions)
        refresh_token = self.create_refresh_token(user_id)
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire * 60,
            refresh_expires_in=self.refresh_token_expire * 24 * 60 * 60,
        )
    
    def create_access_token(
        self,
        user_id: str,
        roles: list[str] = None,
        permissions: list[str] = None,
        additional_claims: dict = None,
    ) -> str:
        """Create a new access token"""
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire)
        
        payload = {
            "sub": str(user_id),
            "type": "access",
            "iat": now,
            "exp": expire,
            "jti": secrets.token_urlsafe(16),
            "roles": roles or [],
            "permissions": permissions or [],
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a new refresh token"""
        now = datetime.utcnow()
        expire = now + timedelta(days=self.refresh_token_expire)
        
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": expire,
            "jti": secrets.token_urlsafe(16),
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[TokenPayload]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            TokenPayload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            
            # Check token type
            if payload.get("type") != token_type:
                return None
            
            # Check if blacklisted
            jti = payload.get("jti")
            if jti and jti in self._blacklist:
                return None
            
            return TokenPayload(**payload)
            
        except JWTError:
            return None
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token by adding its JTI to the blacklist.
        In production, use Redis with TTL.
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False},
            )
            
            jti = payload.get("jti")
            if jti:
                self._blacklist.add(jti)
                return True
            return False
            
        except JWTError:
            return False
    
    def refresh_access_token(
        self,
        refresh_token: str,
        roles: list[str] = None,
        permissions: list[str] = None,
    ) -> Optional[TokenPair]:
        """
        Create new token pair using refresh token.
        The old refresh token is revoked.
        """
        payload = self.verify_token(refresh_token, token_type="refresh")
        if not payload:
            return None
        
        # Revoke old refresh token (rotation)
        self.revoke_token(refresh_token)
        
        # Create new token pair
        return self.create_token_pair(payload.sub, roles, permissions)


class MFAManager:
    """
    Multi-Factor Authentication manager using TOTP.
    """
    
    ISSUER_NAME = "XOR Trading"
    
    def __init__(self):
        self.security = get_security_manager()
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def get_provisioning_uri(self, secret: str, user_email: str) -> str:
        """Get the URI for QR code generation"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=user_email, issuer_name=self.ISSUER_NAME)
    
    def verify_code(self, secret: str, code: str, valid_window: int = 1) -> bool:
        """
        Verify a TOTP code.
        
        Args:
            secret: User's TOTP secret
            code: 6-digit code from authenticator
            valid_window: Number of intervals to check before/after
            
        Returns:
            True if code is valid
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=valid_window)
    
    def generate_backup_codes(self, count: int = 10) -> list[str]:
        """Generate backup recovery codes"""
        return [secrets.token_hex(4).upper() for _ in range(count)]
    
    def encrypt_secret(self, secret: str, user_id: str) -> str:
        """Encrypt TOTP secret for storage"""
        return self.security.encrypt_to_string(
            secret,
            f"mfa:{user_id}".encode()
        )
    
    def decrypt_secret(self, encrypted_secret: str, user_id: str) -> str:
        """Decrypt TOTP secret"""
        return self.security.decrypt_from_string(
            encrypted_secret,
            f"mfa:{user_id}".encode()
        )


# Convenience functions
def create_access_token(
    user_id: str,
    roles: list[str] = None,
    permissions: list[str] = None,
) -> str:
    """Create a new access token"""
    auth = AuthManager()
    return auth.create_access_token(user_id, roles, permissions)


def verify_token(token: str, token_type: str = "access") -> Optional[TokenPayload]:
    """Verify and decode a JWT token"""
    auth = AuthManager()
    return auth.verify_token(token, token_type)


def create_token_pair(
    user_id: str,
    roles: list[str] = None,
    permissions: list[str] = None,
) -> TokenPair:
    """Create access and refresh token pair"""
    auth = AuthManager()
    return auth.create_token_pair(user_id, roles, permissions)
