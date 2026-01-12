"""
XOR Exchange Adapter - Binance Implementation
Full Binance Spot and Futures API support
"""
import asyncio
import hashlib
import hmac
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import aiohttp

from .base import (
    Balance, BaseExchangeAdapter, OrderResult, OrderSide,
    OrderType, Position, Ticker
)


class BinanceAdapter(BaseExchangeAdapter):
    """Binance exchange adapter with spot and futures support."""
    
    name = "Binance"
    
    # API endpoints
    SPOT_REST = "https://api.binance.com"
    SPOT_WS = "wss://stream.binance.com:9443/ws"
    FUTURES_REST = "https://fapi.binance.com"
    FUTURES_WS = "wss://fstream.binance.com/ws"
    
    # Testnet
    TESTNET_SPOT_REST = "https://testnet.binance.vision"
    TESTNET_FUTURES_REST = "https://testnet.binancefuture.com"
    
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
        
        # Set endpoints
        if market_type == "futures":
            self.base_url = self.TESTNET_FUTURES_REST if testnet else self.FUTURES_REST
            self.ws_url = self.FUTURES_WS
        else:
            self.base_url = self.TESTNET_SPOT_REST if testnet else self.SPOT_REST
            self.ws_url = self.SPOT_WS
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
    
    async def connect(self):
        """Connect to Binance."""
        self.session = aiohttp.ClientSession()
        self.is_connected = True
    
    async def disconnect(self):
        """Disconnect from Binance."""
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()
        self.is_connected = False
    
    def _sign(self, params: dict) -> str:
        """Generate HMAC signature."""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode(),
            query_string.encode(),
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
        headers = {"X-MBX-APIKEY": self.api_key}
        
        params = params or {}
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._sign(params)
        
        async with self.session.request(method, url, params=params, headers=headers) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise Exception(f"Binance API error: {data}")
            return data
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """Get ticker for symbol."""
        endpoint = "/api/v3/ticker/24hr" if self.market_type == "spot" else "/fapi/v1/ticker/24hr"
        data = await self._request("GET", endpoint, {"symbol": symbol})
        
        return Ticker(
            symbol=symbol,
            price=float(data["lastPrice"]),
            bid=float(data.get("bidPrice", 0)),
            ask=float(data.get("askPrice", 0)),
            volume_24h=float(data["volume"]),
            change_24h=float(data["priceChangePercent"]),
            timestamp=datetime.utcnow(),
        )
    
    async def get_orderbook(self, symbol: str, limit: int = 20) -> dict:
        """Get orderbook."""
        endpoint = "/api/v3/depth" if self.market_type == "spot" else "/fapi/v1/depth"
        data = await self._request("GET", endpoint, {"symbol": symbol, "limit": limit})
        
        return {
            "bids": [[float(p), float(q)] for p, q in data["bids"]],
            "asks": [[float(p), float(q)] for p, q in data["asks"]],
        }
    
    async def get_balances(self) -> List[Balance]:
        """Get account balances."""
        if self.market_type == "futures":
            data = await self._request("GET", "/fapi/v2/account", signed=True)
            assets = data.get("assets", [])
        else:
            data = await self._request("GET", "/api/v3/account", signed=True)
            assets = data.get("balances", [])
        
        balances = []
        for asset in assets:
            free = float(asset.get("availableBalance", asset.get("free", 0)))
            total = float(asset.get("walletBalance", asset.get("free", 0))) + float(asset.get("locked", 0))
            
            if total > 0:
                balances.append(Balance(
                    asset=asset.get("asset", ""),
                    free=free,
                    locked=total - free,
                    total=total,
                ))
        
        return balances
    
    async def get_positions(self) -> List[Position]:
        """Get open positions (futures only)."""
        if self.market_type != "futures":
            return []
        
        data = await self._request("GET", "/fapi/v2/positionRisk", signed=True)
        
        positions = []
        for pos in data:
            qty = float(pos["positionAmt"])
            if qty != 0:
                positions.append(Position(
                    symbol=pos["symbol"],
                    side="long" if qty > 0 else "short",
                    quantity=abs(qty),
                    entry_price=float(pos["entryPrice"]),
                    mark_price=float(pos["markPrice"]),
                    liquidation_price=float(pos["liquidationPrice"]) if pos["liquidationPrice"] else None,
                    unrealized_pnl=float(pos["unRealizedProfit"]),
                    leverage=int(pos["leverage"]),
                    margin_type=pos["marginType"],
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
        endpoint = "/api/v3/order" if self.market_type == "spot" else "/fapi/v1/order"
        
        # Map order type
        type_map = {
            OrderType.MARKET: "MARKET",
            OrderType.LIMIT: "LIMIT",
            OrderType.STOP_MARKET: "STOP_MARKET",
            OrderType.STOP_LIMIT: "STOP",
        }
        
        params = {
            "symbol": symbol,
            "side": side.value.upper(),
            "type": type_map.get(order_type, "MARKET"),
            "quantity": str(quantity),
        }
        
        if price and order_type in (OrderType.LIMIT, OrderType.STOP_LIMIT):
            params["price"] = str(price)
            params["timeInForce"] = "GTC"
        
        if stop_price:
            params["stopPrice"] = str(stop_price)
        
        if reduce_only and self.market_type == "futures":
            params["reduceOnly"] = "true"
        
        if client_order_id:
            params["newClientOrderId"] = client_order_id
        
        data = await self._request("POST", endpoint, params, signed=True)
        
        return OrderResult(
            order_id=str(data["orderId"]),
            client_order_id=data.get("clientOrderId", ""),
            symbol=symbol,
            side=side.value,
            type=order_type.value,
            status=data["status"].lower(),
            price=float(data.get("price", 0)) or None,
            quantity=float(data["origQty"]),
            filled_quantity=float(data.get("executedQty", 0)),
            average_price=float(data.get("avgPrice", 0)) or None,
            fee=0,  # Need to get from trades
            fee_asset="",
            timestamp=datetime.utcnow(),
            raw=data,
        )
    
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order."""
        endpoint = "/api/v3/order" if self.market_type == "spot" else "/fapi/v1/order"
        
        try:
            await self._request("DELETE", endpoint, {
                "symbol": symbol,
                "orderId": order_id,
            }, signed=True)
            return True
        except Exception:
            return False
    
    async def get_order(self, symbol: str, order_id: str) -> OrderResult:
        """Get order status."""
        endpoint = "/api/v3/order" if self.market_type == "spot" else "/fapi/v1/order"
        
        data = await self._request("GET", endpoint, {
            "symbol": symbol,
            "orderId": order_id,
        }, signed=True)
        
        return OrderResult(
            order_id=str(data["orderId"]),
            client_order_id=data.get("clientOrderId", ""),
            symbol=symbol,
            side=data["side"].lower(),
            type=data["type"].lower(),
            status=data["status"].lower(),
            price=float(data.get("price", 0)) or None,
            quantity=float(data["origQty"]),
            filled_quantity=float(data.get("executedQty", 0)),
            average_price=float(data.get("avgPrice", 0)) or None,
            fee=0,
            fee_asset="",
            timestamp=datetime.utcnow(),
            raw=data,
        )
    
    async def get_open_orders(self, symbol: str = None) -> List[OrderResult]:
        """Get open orders."""
        endpoint = "/api/v3/openOrders" if self.market_type == "spot" else "/fapi/v1/openOrders"
        params = {"symbol": symbol} if symbol else {}
        
        data = await self._request("GET", endpoint, params, signed=True)
        
        return [
            OrderResult(
                order_id=str(o["orderId"]),
                client_order_id=o.get("clientOrderId", ""),
                symbol=o["symbol"],
                side=o["side"].lower(),
                type=o["type"].lower(),
                status=o["status"].lower(),
                price=float(o.get("price", 0)) or None,
                quantity=float(o["origQty"]),
                filled_quantity=float(o.get("executedQty", 0)),
                average_price=None,
                fee=0,
                fee_asset="",
                timestamp=datetime.utcnow(),
                raw=o,
            )
            for o in data
        ]
    
    async def set_leverage(self, symbol: str, leverage: int):
        """Set leverage for a symbol."""
        if self.market_type != "futures":
            return
        
        await self._request("POST", "/fapi/v1/leverage", {
            "symbol": symbol,
            "leverage": leverage,
        }, signed=True)
