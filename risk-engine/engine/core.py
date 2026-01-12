"""
XOR Risk Engine - Core
Position and risk management for trading bots
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RiskLimits:
    """Risk limits configuration."""
    max_drawdown_percent: float = 10.0
    max_position_size_percent: float = 5.0
    daily_loss_limit_percent: float = 3.0
    max_leverage: int = 10
    max_open_positions: int = 10
    max_correlation: float = 0.7
    max_exposure_per_asset: float = 20.0


@dataclass
class PositionRisk:
    """Risk metrics for a single position."""
    symbol: str
    side: str
    size: float
    entry_price: float
    current_price: float
    leverage: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    liquidation_distance_percent: float = 0.0


@dataclass
class PortfolioRisk:
    """Portfolio-level risk metrics."""
    total_equity: float
    total_exposure: float
    total_unrealized_pnl: float
    total_realized_pnl_today: float
    current_drawdown_percent: float
    max_drawdown_percent: float
    open_positions: int
    daily_pnl_percent: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class RiskEngine:
    """
    Risk management engine.
    Validates orders and monitors portfolio risk.
    """
    
    def __init__(self, limits: RiskLimits = None):
        self.limits = limits or RiskLimits()
        
        # Portfolio tracking
        self.peak_equity: float = 0.0
        self.starting_equity_today: float = 0.0
        self.realized_pnl_today: float = 0.0
        self.positions: Dict[str, PositionRisk] = {}
        
        # Daily reset tracking
        self.last_reset_date: Optional[datetime] = None
        
        # Kill switch state
        self.is_killed = False
        self.kill_reason: Optional[str] = None
    
    def update_limits(self, limits: RiskLimits):
        """Update risk limits."""
        self.limits = limits
        logger.info(f"Risk limits updated: {limits}")
    
    async def validate_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        leverage: float = 1.0,
        portfolio_value: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Validate if an order passes risk checks.
        Returns validation result with reason if rejected.
        """
        if self.is_killed:
            return {
                "valid": False,
                "reason": f"Kill switch active: {self.kill_reason}",
            }
        
        # Check leverage
        if leverage > self.limits.max_leverage:
            return {
                "valid": False,
                "reason": f"Leverage {leverage}x exceeds max {self.limits.max_leverage}x",
            }
        
        # Check position size
        order_value = quantity * price
        position_size_percent = (order_value / portfolio_value) * 100 if portfolio_value else 0
        
        if position_size_percent > self.limits.max_position_size_percent:
            return {
                "valid": False,
                "reason": f"Position size {position_size_percent:.1f}% exceeds max {self.limits.max_position_size_percent}%",
            }
        
        # Check open positions limit
        if len(self.positions) >= self.limits.max_open_positions:
            if symbol not in self.positions:
                return {
                    "valid": False,
                    "reason": f"Max open positions ({self.limits.max_open_positions}) reached",
                }
        
        # Check daily loss limit
        if self._check_daily_loss_exceeded():
            return {
                "valid": False,
                "reason": f"Daily loss limit ({self.limits.daily_loss_limit_percent}%) exceeded",
            }
        
        # Check drawdown
        if self._check_max_drawdown_exceeded(portfolio_value):
            return {
                "valid": False,
                "reason": f"Max drawdown ({self.limits.max_drawdown_percent}%) exceeded",
            }
        
        return {"valid": True, "reason": None}
    
    def update_position(
        self,
        symbol: str,
        side: str,
        size: float,
        entry_price: float,
        current_price: float,
        leverage: float = 1.0,
    ):
        """Update position risk tracking."""
        if size == 0:
            if symbol in self.positions:
                del self.positions[symbol]
            return
        
        # Calculate PnL
        if side == "long":
            unrealized_pnl = (current_price - entry_price) * size
        else:
            unrealized_pnl = (entry_price - current_price) * size
        
        unrealized_pnl_percent = (unrealized_pnl / (entry_price * size)) * 100
        
        self.positions[symbol] = PositionRisk(
            symbol=symbol,
            side=side,
            size=size,
            entry_price=entry_price,
            current_price=current_price,
            leverage=leverage,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percent=unrealized_pnl_percent,
        )
    
    def calculate_portfolio_risk(self, total_equity: float) -> PortfolioRisk:
        """Calculate current portfolio risk metrics."""
        
        # Update peak equity
        if total_equity > self.peak_equity:
            self.peak_equity = total_equity
        
        # Calculate drawdown
        if self.peak_equity > 0:
            current_dd = ((self.peak_equity - total_equity) / self.peak_equity) * 100
        else:
            current_dd = 0.0
        
        # Calculate total unrealized PnL
        total_unrealized = sum(p.unrealized_pnl for p in self.positions.values())
        
        # Calculate exposure
        total_exposure = sum(
            p.size * p.current_price * p.leverage
            for p in self.positions.values()
        )
        
        # Daily PnL
        if self.starting_equity_today > 0:
            daily_pnl = ((total_equity - self.starting_equity_today) / self.starting_equity_today) * 100
        else:
            daily_pnl = 0.0
        
        return PortfolioRisk(
            total_equity=total_equity,
            total_exposure=total_exposure,
            total_unrealized_pnl=total_unrealized,
            total_realized_pnl_today=self.realized_pnl_today,
            current_drawdown_percent=current_dd,
            max_drawdown_percent=self.limits.max_drawdown_percent,
            open_positions=len(self.positions),
            daily_pnl_percent=daily_pnl,
        )
    
    def _check_daily_loss_exceeded(self) -> bool:
        """Check if daily loss limit is exceeded."""
        if self.starting_equity_today == 0:
            return False
        
        current_equity = self.starting_equity_today + self.realized_pnl_today
        daily_loss_pct = ((self.starting_equity_today - current_equity) / self.starting_equity_today) * 100
        
        return daily_loss_pct >= self.limits.daily_loss_limit_percent
    
    def _check_max_drawdown_exceeded(self, current_equity: float) -> bool:
        """Check if max drawdown is exceeded."""
        if self.peak_equity == 0:
            return False
        
        current_dd = ((self.peak_equity - current_equity) / self.peak_equity) * 100
        return current_dd >= self.limits.max_drawdown_percent
    
    def trigger_kill_switch(self, reason: str):
        """Activate kill switch - stop all trading."""
        self.is_killed = True
        self.kill_reason = reason
        logger.critical(f"KILL SWITCH ACTIVATED: {reason}")
    
    def reset_kill_switch(self):
        """Reset kill switch (requires confirmation)."""
        self.is_killed = False
        self.kill_reason = None
        logger.info("Kill switch reset")
    
    def reset_daily_tracking(self, current_equity: float):
        """Reset daily tracking (call at start of trading day)."""
        self.starting_equity_today = current_equity
        self.realized_pnl_today = 0.0
        self.last_reset_date = datetime.utcnow().date()
