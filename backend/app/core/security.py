"""
XOR Trading Platform - Security Module
AES-256-GCM encryption for API keys and sensitive data
"""
import base64
import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from passlib.context import CryptContext

from ..config import settings


# Password hashing context
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=4,
)


@dataclass
class EncryptedData:
    """Container for encrypted data with metadata"""
    ciphertext: bytes
    nonce: bytes
    tag: bytes
    version: int = 1
    
    def to_string(self) -> str:
        """Encode to base64 string for storage"""
        # Format: version:nonce:ciphertext (tag is included in ciphertext for AESGCM)
        combined = f"{self.version}:{base64.b64encode(self.nonce).decode()}:{base64.b64encode(self.ciphertext).decode()}"
        return combined
    
    @classmethod
    def from_string(cls, data: str) -> "EncryptedData":
        """Decode from base64 string"""
        parts = data.split(":")
        if len(parts) != 3:
            raise ValueError("Invalid encrypted data format")
        
        version = int(parts[0])
        nonce = base64.b64decode(parts[1])
        ciphertext = base64.b64decode(parts[2])
        
        return cls(
            ciphertext=ciphertext,
            nonce=nonce,
            tag=b"",  # Tag is included in ciphertext for AESGCM
            version=version,
        )


class SecurityManager:
    """
    Security manager for encryption/decryption operations.
    Uses AES-256-GCM for authenticated encryption.
    """
    
    NONCE_SIZE = 12  # 96 bits for GCM
    KEY_SIZE = 32    # 256 bits for AES-256
    
    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize with encryption key"""
        key = encryption_key or settings.ENCRYPTION_KEY
        if len(key) != self.KEY_SIZE:
            # Derive a proper key using SHA-256 if needed
            key = hashlib.sha256(key.encode()).digest()
        else:
            key = key.encode() if isinstance(key, str) else key
        
        self._key = key
        self._aesgcm = AESGCM(self._key)
    
    def encrypt(self, plaintext: str, associated_data: Optional[bytes] = None) -> EncryptedData:
        """
        Encrypt plaintext using AES-256-GCM
        
        Args:
            plaintext: Text to encrypt
            associated_data: Additional authenticated data (not encrypted)
            
        Returns:
            EncryptedData containing ciphertext and nonce
        """
        nonce = os.urandom(self.NONCE_SIZE)
        plaintext_bytes = plaintext.encode('utf-8')
        
        ciphertext = self._aesgcm.encrypt(
            nonce,
            plaintext_bytes,
            associated_data
        )
        
        return EncryptedData(
            ciphertext=ciphertext,
            nonce=nonce,
            tag=b"",  # Tag is included in ciphertext
        )
    
    def decrypt(self, encrypted: EncryptedData, associated_data: Optional[bytes] = None) -> str:
        """
        Decrypt ciphertext using AES-256-GCM
        
        Args:
            encrypted: EncryptedData object
            associated_data: Additional authenticated data used during encryption
            
        Returns:
            Decrypted plaintext
        """
        plaintext_bytes = self._aesgcm.decrypt(
            encrypted.nonce,
            encrypted.ciphertext,
            associated_data
        )
        
        return plaintext_bytes.decode('utf-8')
    
    def encrypt_to_string(self, plaintext: str, associated_data: Optional[bytes] = None) -> str:
        """Encrypt and return as base64 string"""
        encrypted = self.encrypt(plaintext, associated_data)
        return encrypted.to_string()
    
    def decrypt_from_string(self, data: str, associated_data: Optional[bytes] = None) -> str:
        """Decrypt from base64 string"""
        encrypted = EncryptedData.from_string(data)
        return self.decrypt(encrypted, associated_data)
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new random encryption key"""
        return secrets.token_hex(16)  # 32 hex chars = 256 bits
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using Argon2"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_api_secret() -> str:
        """Generate a secure API secret"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def compute_hmac(key: str, message: str) -> str:
        """Compute HMAC-SHA256 signature"""
        return hmac.new(
            key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def verify_hmac(key: str, message: str, signature: str) -> bool:
        """Verify HMAC-SHA256 signature (timing-safe)"""
        expected = SecurityManager.compute_hmac(key, message)
        return hmac.compare_digest(expected, signature)
    
    def encrypt_api_key(self, api_key: str, user_id: str) -> str:
        """
        Encrypt an API key with user-specific associated data.
        This ensures the key cannot be used if copied to another user.
        """
        associated_data = f"user:{user_id}".encode()
        return self.encrypt_to_string(api_key, associated_data)
    
    def decrypt_api_key(self, encrypted_key: str, user_id: str) -> str:
        """
        Decrypt an API key with user-specific associated data.
        Will fail if the user_id doesn't match the one used during encryption.
        """
        associated_data = f"user:{user_id}".encode()
        return self.decrypt_from_string(encrypted_key, associated_data)
    
    def generate_hmac(self, data: str) -> str:
        """Generate HMAC using the internal key"""
        return self.compute_hmac(self._key.hex() if isinstance(self._key, bytes) else self._key, data)


# Singleton instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """Get or create security manager singleton"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


def encrypt_api_key(api_key: str, user_id: str) -> str:
    """
    Encrypt an API key with user-specific associated data.
    This ensures the key cannot be used if copied to another user.
    """
    manager = get_security_manager()
    associated_data = f"user:{user_id}".encode()
    return manager.encrypt_to_string(api_key, associated_data)


def decrypt_api_key(encrypted_key: str, user_id: str) -> str:
    """
    Decrypt an API key with user-specific associated data.
    Will fail if the user_id doesn't match the one used during encryption.
    """
    manager = get_security_manager()
    associated_data = f"user:{user_id}".encode()
    return manager.decrypt_from_string(encrypted_key, associated_data)


class RateLimiter:
    """
    Token bucket rate limiter for API protection.
    Uses Redis for distributed rate limiting.
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        redis_client=None
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.redis = redis_client
        self._local_cache = {}  # Fallback when Redis not available
    
    async def is_allowed(self, key: str) -> Tuple[bool, dict]:
        """
        Check if request is allowed under rate limit.
        
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        if self.redis:
            return await self._check_redis(key)
        return self._check_local(key)
    
    async def _check_redis(self, key: str) -> Tuple[bool, dict]:
        """Check rate limit using Redis sliding window"""
        now = datetime.utcnow()
        window_key = f"ratelimit:{key}"
        
        pipe = self.redis.pipeline()
        pipe.zadd(window_key, {str(now.timestamp()): now.timestamp()})
        pipe.zremrangebyscore(
            window_key,
            0,
            (now - timedelta(seconds=self.window_seconds)).timestamp()
        )
        pipe.zcard(window_key)
        pipe.expire(window_key, self.window_seconds)
        
        results = await pipe.execute()
        current_count = results[2]
        
        remaining = max(0, self.max_requests - current_count)
        
        return current_count <= self.max_requests, {
            "limit": self.max_requests,
            "remaining": remaining,
            "reset": int(now.timestamp()) + self.window_seconds,
        }
    
    def _check_local(self, key: str) -> Tuple[bool, dict]:
        """Check rate limit using local memory (fallback)"""
        now = datetime.utcnow()
        
        if key not in self._local_cache:
            self._local_cache[key] = []
        
        # Remove old entries
        cutoff = now - timedelta(seconds=self.window_seconds)
        self._local_cache[key] = [
            ts for ts in self._local_cache[key]
            if ts > cutoff
        ]
        
        current_count = len(self._local_cache[key])
        
        if current_count < self.max_requests:
            self._local_cache[key].append(now)
            return True, {
                "limit": self.max_requests,
                "remaining": self.max_requests - current_count - 1,
                "reset": int(now.timestamp()) + self.window_seconds,
            }
        
        return False, {
            "limit": self.max_requests,
            "remaining": 0,
            "reset": int(now.timestamp()) + self.window_seconds,
        }


class AuditLogger:
    """
    Audit logger for security events.
    All sensitive operations must be logged.
    """
    
    def __init__(self, db_session=None):
        self.db = db_session
    
    async def log(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        ip_address: str,
        user_agent: str,
        details: Optional[dict] = None,
        success: bool = True,
    ):
        """Log an audit event"""
        from ..models.audit_log import AuditLog
        
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            success=success,
            timestamp=datetime.utcnow(),
        )
        
        if self.db:
            self.db.add(log_entry)
            await self.db.commit()
        
        return log_entry
