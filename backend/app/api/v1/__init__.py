"""API v1 router"""
from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .bots import router as bots_router
from .strategies import router as strategies_router
from .orders import router as orders_router
from .positions import router as positions_router
from .exchanges import router as exchanges_router
from .analytics import router as analytics_router
from .websocket import router as ws_router

api_router = APIRouter()

# Include all routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(bots_router, prefix="/bots", tags=["Bots"])
api_router.include_router(strategies_router, prefix="/strategies", tags=["Strategies"])
api_router.include_router(orders_router, prefix="/orders", tags=["Orders"])
api_router.include_router(positions_router, prefix="/positions", tags=["Positions"])
api_router.include_router(exchanges_router, prefix="/exchanges", tags=["Exchanges"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(ws_router, prefix="/ws", tags=["WebSocket"])
