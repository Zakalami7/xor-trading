"""Core module - Security, Auth, Events"""
from .security import SecurityManager, encrypt_api_key, decrypt_api_key
from .auth import AuthManager, create_access_token, verify_token
from .events import EventBus, Event
from .exceptions import (
    XORException,
    AuthenticationError,
    AuthorizationError,
    ExchangeError,
    RiskLimitExceeded,
    InsufficientBalance,
)

__all__ = [
    "SecurityManager",
    "encrypt_api_key",
    "decrypt_api_key",
    "AuthManager",
    "create_access_token",
    "verify_token",
    "EventBus",
    "Event",
    "XORException",
    "AuthenticationError",
    "AuthorizationError",
    "ExchangeError",
    "RiskLimitExceeded",
    "InsufficientBalance",
]
