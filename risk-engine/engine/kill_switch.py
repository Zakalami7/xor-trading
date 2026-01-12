"""
XOR Risk Engine - Kill Switch
Emergency stop mechanism for trading
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)


class KillSwitchTrigger(str, Enum):
    """Reasons for kill switch activation."""
    MANUAL = "manual"
    MAX_DRAWDOWN = "max_drawdown"
    DAILY_LOSS = "daily_loss"
    EXCHANGE_ERROR = "exchange_error"
    POSITION_LIQUIDATION = "position_liquidation"
    ABNORMAL_VOLATILITY = "abnormal_volatility"
    CONNECTION_LOSS = "connection_loss"
    SYSTEM_ERROR = "system_error"


@dataclass
class KillSwitchEvent:
    """Kill switch activation event."""
    trigger: KillSwitchTrigger
    reason: str
    affected_bots: List[str]
    timestamp: datetime
    auto_reset_at: Optional[datetime] = None


class KillSwitch:
    """
    Emergency kill switch for trading operations.
    Immediately stops all trading when triggered.
    """
    
    def __init__(self):
        self.is_active = False
        self.events: List[KillSwitchEvent] = []
        self.affected_bots: List[str] = []
    
    def activate(
        self,
        trigger: KillSwitchTrigger,
        reason: str,
        bot_ids: List[str] = None,
    ) -> KillSwitchEvent:
        """
        Activate the kill switch.
        All trading operations should stop immediately.
        """
        self.is_active = True
        self.affected_bots = bot_ids or []
        
        event = KillSwitchEvent(
            trigger=trigger,
            reason=reason,
            affected_bots=self.affected_bots,
            timestamp=datetime.utcnow(),
        )
        
        self.events.append(event)
        
        logger.critical(
            f"KILL SWITCH ACTIVATED | Trigger: {trigger.value} | "
            f"Reason: {reason} | Bots affected: {len(self.affected_bots)}"
        )
        
        return event
    
    def deactivate(self, confirmation_code: str = None):
        """
        Deactivate the kill switch.
        Requires confirmation to prevent accidental reset.
        """
        # In production, would require proper confirmation
        if not confirmation_code:
            raise ValueError("Confirmation required to reset kill switch")
        
        self.is_active = False
        self.affected_bots = []
        
        logger.info("Kill switch deactivated")
    
    def check_conditions(
        self,
        current_drawdown: float,
        max_drawdown: float,
        daily_loss: float,
        max_daily_loss: float,
        exchange_healthy: bool = True,
    ) -> Optional[KillSwitchEvent]:
        """
        Check kill switch conditions and activate if needed.
        Returns event if triggered, None otherwise.
        """
        # Already active
        if self.is_active:
            return None
        
        # Check max drawdown
        if current_drawdown >= max_drawdown:
            return self.activate(
                KillSwitchTrigger.MAX_DRAWDOWN,
                f"Drawdown {current_drawdown:.2f}% exceeded limit {max_drawdown:.2f}%",
            )
        
        # Check daily loss
        if daily_loss >= max_daily_loss:
            return self.activate(
                KillSwitchTrigger.DAILY_LOSS,
                f"Daily loss {daily_loss:.2f}% exceeded limit {max_daily_loss:.2f}%",
            )
        
        # Check exchange health
        if not exchange_healthy:
            return self.activate(
                KillSwitchTrigger.EXCHANGE_ERROR,
                "Exchange connection unhealthy",
            )
        
        return None
    
    def get_status(self) -> dict:
        """Get current kill switch status."""
        return {
            "is_active": self.is_active,
            "affected_bots": self.affected_bots,
            "last_event": self.events[-1].reason if self.events else None,
            "total_activations": len(self.events),
        }
