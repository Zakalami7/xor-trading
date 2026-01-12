"""
XOR Exchange Adapter - Bybit Implementation
Bybit V5 API support for spot and futures
"""
import hashlib
import hmac
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import aiohttp

from ..base import (
    Balance, BaseExchangeAdapter, OrderResult, OrderSide,
    OrderType, Position, Ticker
)


class BybitAdapter(BaseExchangeAdapter):
    """Bybit exchange adapter with unified V5 API support."""
    
    name = "Bybit"
    
    # API endpoints
    REST_URL = "https://api.bybit.com"
    TESTNET_REST_URL = "https://api-testnet.bybit.com"
    WS_URL = "wss://stream.bybit.com/v5/public"
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        market_type: str = "spot",
        **kwargs,
    ):
        super().__init__(api_key, api_secret, testnet)
        self.market_type = market_type
        self.base_url = self.TESTNET_REST_URL if testnet else self.REST_URL
        
        # Category for V5 API
        if market_type == "futures":
            self.category = "linear"
        else:
            self.category = "spot"
        
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def connect(self):
        """Connect to Bybit."""
        self.session = aiohttp.ClientSession()
        self.is_connected = True
    
    async def disconnect(self):
        """Disconnect from Bybit."""
        if self.session:
            await self.session.close()
        self.is_connected = False
    
    def _sign(self, timestamp: int, params: dict) -> str:
        """Generate HMAC signature for Bybit V5."""
        recv_window = "5000"
        param_str = urlencode(sorted(params.items()))
        sign_str = f"{timestamp}{self.api_key}{recv_window}{param_str}"
        
        signature = hmac.new(
            self.api_secret.encode(),
            sign_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        signed: bool = False,
    ) -> dict:
        """Make API request."""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        params = params or {}
        
        if signed:
            timestamp = int(time.time() * 1000)
            signature = self._sign(timestamp, params)
            
            headers = {
                "X-BAPI-API-KEY": self.api_key,
                "X-BAPI-SIGN": signature,
                "X-BAPI-TIMESTAMP": str(timestamp),
                "X-BAPI-RECV-WINDOW": "5000",
            }
        
        async with self.session.request(method, url, params=params, headers=headers) as resp:
            data = await resp.json()
            
            if data.get("retCode") != 0:
                raise Exception(f"Bybit API error: {data.get('retMsg')}")
            
            return data.get("result", {})
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """Get ticker for symbol."""
        data = await self._request(
            "GET",
            "/v5/market/tickers",
            {"category": self.category, "symbol": symbol}
        )
        
        ticker = data.get("list", [{}])[0]
        
        return Ticker(
            symbol=symbol,
            price=float(ticker.get("lastPrice", 0)),
            bid=float(ticker.get("bid1Price", 0)),
            ask=float(ticker.get("ask1Price", 0)),
            volume_24h=float(ticker.get("volume24h", 0)),
            change_24h=float(ticker.get("price24hPcnt", 0)) * 100,
            timestamp=datetime.utcnow(),
        )
    
    async def get_orderbook(self, symbol: str, limit: int = 20) -> dict:
        """Get orderbook."""
        data = await self._request(
            "GET",
            "/v5/market/orderbook",
            {"category": self.category, "symbol": symbol, "limit": limit}
        )
        
        return {
            "bids": [[float(p), float(q)] for p, q in data.get("b", [])],
            "asks": [[float(p), float(q)] for p, q in data.get("a", [])],
        }
    
    async def get_balances(self) -> List[Balance]:
        """Get account balances."""
        account_type = "UNIFIED" if self.market_type == "futures" else "SPOT"
        
        data = await self._request(
            "GET",
            "/v5/account/wallet-balance",
            {"accountType": account_type},
            signed=True
        )
        
        balances = []
        for account in data.get("list", []):
            for coin in account.get("coin", []):
                total = float(coin.get("walletBalance", 0))
                free = float(coin.get("availableToWithdraw", 0))
                
                if total > 0:
                    balances.append(Balance(
                        asset=coin.get("coin", ""),
                        free=free,
                        locked=total - free,
                        total=total,
                    ))
        
        return balances
    
    async def get_positions(self) -> List[Position]:
        """Get open positions (futures only)."""
        if self.category != "linear":
            return []
        
        data = await self._request(
            "GET",
            "/v5/position/list",
            {"category": self.category, "settleCoin": "USDT"},
            signed=True
        )
        
        positions = []
        for pos in data.get("list", []):
            size = float(pos.get("size", 0))
            if size != 0:
                positions.append(Position(
                    symbol=pos.get("symbol", ""),
                    side=pos.get("side", "").lower(),
                    quantity=abs(size),
                    entry_price=float(pos.get("avgPrice", 0)),
                    mark_price=float(pos.get("markPrice", 0)),
                    liquidation_price=float(pos.get("liqPrice", 0)) if pos.get("liqPrice") else None,
                    unrealized_pnl=float(pos.get("unrealisedPnl", 0)),
                    leverage=int(pos.get("leverage", 1)),
                    margin_type=pos.get("tradeMode", "cross"),
                ))
        
        return positions
    
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
        # Map order type
        type_map = {
            OrderType.MARKET: "Market",
            OrderType.LIMIT: "Limit",
        }
        
        params = {
            "category": self.category,
            "symbol": symbol,
            "side": side.value.capitalize(),
            "orderType": type_map.get(order_type, "Market"),
            "qty": str(quantity),
        }
        
        if price and order_type == OrderType.LIMIT:
            params["price"] = str(price)
        
        if reduce_only and self.category == "linear":
            params["reduceOnly"] = True
        
        if client_order_id:
            params["orderLinkId"] = client_order_id
        
        data = await self._request("POST", "/v5/order/create", params, signed=True)
        
        return OrderResult(
            order_id=data.get("orderId", ""),
            client_order_id=data.get("orderLinkId", ""),
            symbol=symbol,
            side=side.value,
            type=order_type.value,
            status="new",
            price=price,
            quantity=quantity,
            filled_quantity=0,
            average_price=None,
            fee=0,
            fee_asset="",
            timestamp=datetime.utcnow(),
            raw=data,
        )
    
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order."""
        try:
            await self._request(
                "POST",
                "/v5/order/cancel",
                {"category": self.category, "symbol": symbol, "orderId": order_id},
                signed=True
            )
            return True
        except Exception:
            return False
    
    async def get_order(self, symbol: str, order_id: str) -> OrderResult:
        """Get order status."""
        data = await self._request(
            "GET",
            "/v5/order/realtime",
            {"category": self.category, "symbol": symbol, "orderId": order_id},
            signed=True
        )
        
        order = data.get("list", [{}])[0]
        
        return OrderResult(
            order_id=order.get("orderId", ""),
            client_order_id=order.get("orderLinkId", ""),
            symbol=symbol,
            side=order.get("side", "").lower(),
            type=order.get("orderType", "").lower(),
            status=order.get("orderStatus", "").lower(),
            price=float(order.get("price", 0)) or None,
            quantity=float(order.get("qty", 0)),
            filled_quantity=float(order.get("cumExecQty", 0)),
            average_price=float(order.get("avgPrice", 0)) or None,
            fee=float(order.get("cumExecFee", 0)),
            fee_asset="",
            timestamp=datetime.utcnow(),
            raw=order,
        )
    
    async def get_open_orders(self, symbol: str = None) -> List[OrderResult]:
        """Get open orders."""
        params = {"category": self.category}
        if symbol:
            params["symbol"] = symbol
        
        data = await self._request("GET", "/v5/order/realtime", params, signed=True)
        
        return [
            OrderResult(
                order_id=o.get("orderId", ""),
                client_order_id=o.get("orderLinkId", ""),
                symbol=o.get("symbol", ""),
                side=o.get("side", "").lower(),
                type=o.get("orderType", "").lower(),
                status=o.get("orderStatus", "").lower(),
                price=float(o.get("price", 0)) or None,
                quantity=float(o.get("qty", 0)),
                filled_quantity=float(o.get("cumExecQty", 0)),
                average_price=None,
                fee=0,
                fee_asset="",
                timestamp=datetime.utcnow(),
                raw=o,
            )
            for o in data.get("list", [])
        ]
    
    async def set_leverage(self, symbol: str, leverage: int):
        """Set leverage for a symbol."""
        if self.category != "linear":
            return
        
        await self._request(
            "POST",
            "/v5/position/set-leverage",
            {"category": self.category, "symbol": symbol, "buyLeverage": str(leverage), "sellLeverage": str(leverage)},
            signed=True
        )
