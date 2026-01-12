"""
XOR Exchange Adapter - Base Class
Abstract interface for all exchange adapters
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Balance:
    """Account balance."""
    asset: str
    free: float
    locked: float
    total: float


@dataclass
class Ticker:
    """Market ticker."""
    symbol: str
    price: float
    bid: float
    ask: float
    volume_24h: float
    change_24h: float
    timestamp: datetime


@dataclass
class OrderResult:
    """Order execution result."""
    order_id: str
    client_order_id: str
    symbol: str
    side: str
    type: str
    status: str
    price: Optional[float]
    quantity: float
    filled_quantity: float
    average_price: Optional[float]
    fee: float
    fee_asset: str
    timestamp: datetime
    raw: dict


@dataclass
class Position:
    """Open position."""
    symbol: str
    side: str
    quantity: float
    entry_price: float
    mark_price: float
    liquidation_price: Optional[float]
    unrealized_pnl: float
    leverage: int
    margin_type: str


class BaseExchangeAdapter(ABC):
    """
    Abstract base class for exchange adapters.
    All exchange implementations must inherit from this.
    """
    
    name: str = "BaseExchange"
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        passphrase: str = None,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.passphrase = passphrase
        self.is_connected = False
    
    @abstractmethod
    async def connect(self):
        """Connect to the exchange."""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from the exchange."""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker:
        """Get current ticker for a symbol."""
        pass
    
    @abstractmethod
    async def get_orderbook(self, symbol: str, limit: int = 20) -> dict:
        """Get orderbook for a symbol."""
        pass
    
    @abstractmethod
    async def get_balances(self) -> List[Balance]:
        """Get account balances."""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get open positions (futures)."""
        pass
    
    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float = None,
        stop_price: float = None,
        reduce_only: bool = False,
        client_order_id: str = None,
    ) -> OrderResult:
        """Place an order."""
        pass
    
    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order."""
        pass
    
    @abstractmethod
    async def get_order(self, symbol: str, order_id: str) -> OrderResult:
        """Get order status."""
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: str = None) -> List[OrderResult]:
        """Get all open orders."""
        pass
    
    async def set_leverage(self, symbol: str, leverage: int):
        """Set leverage for a symbol (futures)."""
        pass
    
    async def subscribe_ticker(self, symbol: str, callback):
        """Subscribe to ticker updates via WebSocket."""
        pass
    
    async def subscribe_orderbook(self, symbol: str, callback):
        """Subscribe to orderbook updates via WebSocket."""
        pass
    
    async def subscribe_trades(self, symbol: str, callback):
        """Subscribe to trade updates via WebSocket."""
        pass
    
    async def subscribe_user_data(self, callback):
        """Subscribe to user data updates (orders, positions)."""
        pass
