"""
XOR Trading Platform - Common Schemas
"""
from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field


# Generic type for paginated responses
T = TypeVar("T")


class ResponseBase(BaseModel):
    """Base response wrapper"""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DataResponse(ResponseBase, Generic[T]):
    """Response with data"""
    data: T


class PaginatedResponse(ResponseBase, Generic[T]):
    """Paginated response"""
    data: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1


class ErrorDetail(BaseModel):
    """Error detail"""
    field: Optional[str] = None
    value: Optional[Any] = None
    reason: str


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    error: dict = Field(
        ...,
        example={
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": [],
        }
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: dict = Field(
        default_factory=lambda: {
            "database": "unknown",
            "redis": "unknown",
            "exchange_connections": {},
        }
    )


class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str
    channel: str
    data: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MarketTick(BaseModel):
    """Market price tick"""
    symbol: str
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume_24h: Optional[float] = None
    change_24h: Optional[float] = None
    timestamp: datetime


class OrderBookLevel(BaseModel):
    """Order book level"""
    price: float
    quantity: float


class OrderBook(BaseModel):
    """Order book snapshot"""
    symbol: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: datetime


class CandleStick(BaseModel):
    """OHLCV candle"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    @property
    def is_bullish(self) -> bool:
        return self.close > self.open
    
    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)
    
    @property
    def range(self) -> float:
        return self.high - self.low
