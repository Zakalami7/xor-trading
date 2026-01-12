"""
XOR Trading Platform - Custom Exceptions
Centralized exception definitions for consistent error handling
"""
from typing import Any, Dict, Optional


class XORException(Exception):
    """Base exception for all XOR Trading Platform errors"""
    
    def __init__(
        self,
        message: str = "An error occurred",
        code: str = "XOR_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """Convert to API response format"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


# Authentication Errors (401)
class AuthenticationError(XORException):
    """Authentication failed"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="AUTH_FAILED",
            status_code=401,
            details=details,
        )


class InvalidTokenError(AuthenticationError):
    """Invalid or expired token"""
    
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message=message, details={"token_valid": False})


class MFARequiredError(AuthenticationError):
    """MFA verification required"""
    
    def __init__(self, message: str = "MFA verification required"):
        super().__init__(message=message, details={"mfa_required": True})


# Authorization Errors (403)
class AuthorizationError(XORException):
    """Authorization/permission error"""
    
    def __init__(
        self,
        message: str = "Permission denied",
        required_permission: str = None,
    ):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            details={"required_permission": required_permission} if required_permission else {},
        )


class InsufficientPermissions(AuthorizationError):
    """User lacks required permissions"""
    
    def __init__(self, permission: str):
        super().__init__(
            message=f"Insufficient permissions: {permission} required",
            required_permission=permission,
        )


# Resource Errors (404, 409)
class ResourceNotFoundError(XORException):
    """Resource not found"""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} not found: {resource_id}",
            code="NOT_FOUND",
            status_code=404,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )


class ResourceExistsError(XORException):
    """Resource already exists"""
    
    def __init__(self, resource_type: str, identifier: str):
        super().__init__(
            message=f"{resource_type} already exists: {identifier}",
            code="CONFLICT",
            status_code=409,
            details={
                "resource_type": resource_type,
                "identifier": identifier,
            },
        )


# Validation Errors (400, 422)
class ValidationError(XORException):
    """Request validation failed"""
    
    def __init__(self, message: str, errors: list = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details={"errors": errors or []},
        )


class InvalidParameterError(ValidationError):
    """Invalid parameter value"""
    
    def __init__(self, parameter: str, value: Any, reason: str = None):
        super().__init__(
            message=f"Invalid value for {parameter}: {value}",
            errors=[{
                "field": parameter,
                "value": str(value),
                "reason": reason,
            }],
        )


# Exchange Errors
class ExchangeError(XORException):
    """Exchange-related error"""
    
    def __init__(
        self,
        exchange: str,
        message: str,
        code: str = "EXCHANGE_ERROR",
        details: Optional[Dict] = None,
    ):
        super().__init__(
            message=f"[{exchange}] {message}",
            code=code,
            status_code=503,
            details={"exchange": exchange, **(details or {})},
        )


class ExchangeConnectionError(ExchangeError):
    """Failed to connect to exchange"""
    
    def __init__(self, exchange: str, reason: str = None):
        super().__init__(
            exchange=exchange,
            message=f"Connection failed: {reason}" if reason else "Connection failed",
            code="EXCHANGE_CONNECTION_ERROR",
        )


class ExchangeAuthError(ExchangeError):
    """Exchange API authentication failed"""
    
    def __init__(self, exchange: str, reason: str = None):
        super().__init__(
            exchange=exchange,
            message=f"API authentication failed: {reason}" if reason else "API authentication failed",
            code="EXCHANGE_AUTH_ERROR",
        )


class OrderRejectedError(ExchangeError):
    """Order rejected by exchange"""
    
    def __init__(self, exchange: str, reason: str, order_id: str = None):
        super().__init__(
            exchange=exchange,
            message=f"Order rejected: {reason}",
            code="ORDER_REJECTED",
            details={"order_id": order_id, "reason": reason},
        )


# Risk Management Errors
class RiskLimitExceeded(XORException):
    """Risk limit exceeded"""
    
    def __init__(
        self,
        limit_type: str,
        current_value: float,
        limit_value: float,
        message: str = None,
    ):
        super().__init__(
            message=message or f"Risk limit exceeded: {limit_type}",
            code="RISK_LIMIT_EXCEEDED",
            status_code=400,
            details={
                "limit_type": limit_type,
                "current_value": current_value,
                "limit_value": limit_value,
            },
        )


class MaxDrawdownExceeded(RiskLimitExceeded):
    """Maximum drawdown limit exceeded"""
    
    def __init__(self, current_dd: float, max_dd: float):
        super().__init__(
            limit_type="max_drawdown",
            current_value=current_dd,
            limit_value=max_dd,
            message=f"Maximum drawdown exceeded: {current_dd:.2f}% > {max_dd:.2f}%",
        )


class PositionSizeLimitExceeded(RiskLimitExceeded):
    """Position size limit exceeded"""
    
    def __init__(self, current_size: float, max_size: float):
        super().__init__(
            limit_type="position_size",
            current_value=current_size,
            limit_value=max_size,
            message=f"Position size limit exceeded: {current_size} > {max_size}",
        )


class DailyLossLimitExceeded(RiskLimitExceeded):
    """Daily loss limit exceeded"""
    
    def __init__(self, current_loss: float, max_loss: float):
        super().__init__(
            limit_type="daily_loss",
            current_value=current_loss,
            limit_value=max_loss,
            message=f"Daily loss limit exceeded: {current_loss:.2f}% > {max_loss:.2f}%",
        )


# Trading Errors
class InsufficientBalance(XORException):
    """Insufficient balance for operation"""
    
    def __init__(self, asset: str, required: float, available: float):
        super().__init__(
            message=f"Insufficient {asset} balance: required {required}, available {available}",
            code="INSUFFICIENT_BALANCE",
            status_code=400,
            details={
                "asset": asset,
                "required": required,
                "available": available,
            },
        )


class InvalidOrderError(XORException):
    """Invalid order parameters"""
    
    def __init__(self, message: str, order_params: dict = None):
        super().__init__(
            message=message,
            code="INVALID_ORDER",
            status_code=400,
            details={"order_params": order_params},
        )


class StrategyError(XORException):
    """Strategy execution error"""
    
    def __init__(self, strategy: str, message: str, details: dict = None):
        super().__init__(
            message=f"Strategy error [{strategy}]: {message}",
            code="STRATEGY_ERROR",
            status_code=500,
            details={"strategy": strategy, **(details or {})},
        )


# Rate Limiting
class RateLimitExceeded(XORException):
    """Rate limit exceeded"""
    
    def __init__(self, limit: int, window: int, retry_after: int = None):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window}s",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={
                "limit": limit,
                "window": window,
                "retry_after": retry_after,
            },
        )


# System Errors
class ServiceUnavailableError(XORException):
    """Service temporarily unavailable"""
    
    def __init__(self, service: str, message: str = None):
        super().__init__(
            message=message or f"Service unavailable: {service}",
            code="SERVICE_UNAVAILABLE",
            status_code=503,
            details={"service": service},
        )


class KillSwitchActivated(XORException):
    """Emergency kill switch activated"""
    
    def __init__(self, reason: str, affected_bots: list = None):
        super().__init__(
            message=f"Kill switch activated: {reason}",
            code="KILL_SWITCH_ACTIVATED",
            status_code=503,
            details={
                "reason": reason,
                "affected_bots": affected_bots or [],
            },
        )
