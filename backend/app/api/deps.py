"""
XOR Trading Platform - API Dependencies
Common dependencies for API routes
"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..core.auth import AuthManager, TokenPayload
from ..core.exceptions import AuthenticationError, AuthorizationError
from ..core.security import RateLimiter
from ..db.session import get_db
from ..models.user import User

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)

# Auth manager
auth_manager = AuthManager()

# Rate limiter
rate_limiter = RateLimiter(
    max_requests=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    """
    Get current authenticated user from JWT token.
    Raises 401 if not authenticated.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = auth_manager.verify_token(token, token_type="access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = await db.get(User, UUID(payload.sub))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current user and verify they are active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current user and verify they are a superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


async def get_optional_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(db, credentials)
    except HTTPException:
        return None


def require_permissions(*permissions: str):
    """
    Dependency factory to check for required permissions.
    
    Usage:
        @router.get("/admin/users")
        async def list_users(
            user: User = Depends(require_permissions("users:read"))
        ):
            ...
    """
    async def check_permissions(
        current_user: User = Depends(get_current_user),
    ) -> User:
        # Superusers have all permissions
        if current_user.is_superuser:
            return current_user
        
        user_permissions = set(current_user.settings.get("permissions", []))
        required = set(permissions)
        
        if not required.issubset(user_permissions):
            missing = required - user_permissions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing)}",
            )
        
        return current_user
    
    return check_permissions


async def check_rate_limit(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Rate limiting dependency.
    Uses user ID as the rate limit key.
    """
    key = f"user:{current_user.id}"
    allowed, info = await rate_limiter.is_allowed(key)
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(info["limit"]),
                "X-RateLimit-Remaining": str(info["remaining"]),
                "X-RateLimit-Reset": str(info["reset"]),
                "Retry-After": str(info["reset"] - int(request.state.request_time.timestamp())),
            },
        )
    
    return info


class Pagination:
    """Pagination parameters"""
    
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100,
    ):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), max_page_size)
        self.offset = (self.page - 1) * self.page_size
    
    def paginate_query(self, query):
        """Apply pagination to SQLAlchemy query"""
        return query.offset(self.offset).limit(self.page_size)


def get_pagination(
    page: int = 1,
    page_size: int = 20,
) -> Pagination:
    """Get pagination parameters"""
    return Pagination(page=page, page_size=page_size)


async def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    # Check for proxy headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


async def get_user_agent(
    user_agent: str = Header(default="unknown")
) -> str:
    """Get user agent from request headers"""
    return user_agent
