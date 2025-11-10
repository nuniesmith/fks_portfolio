"""
Trading Signal Data Structure
Represents a trading signal with entry, TP, SL, and metadata
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum

from .trade_categories import TradeCategory


class SignalType(Enum):
    """Signal type"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"


class SignalStrength(Enum):
    """Signal strength"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass
class TradingSignal:
    """Trading signal with entry, TP, SL"""
    
    symbol: str
    signal_type: SignalType
    category: TradeCategory
    
    # Price levels
    entry_price: float
    take_profit: float
    stop_loss: float
    
    # Percentages
    take_profit_pct: float
    stop_loss_pct: float
    
    # Risk metrics
    risk_reward_ratio: float
    position_size_pct: float  # Recommended position size (1-2% risk)
    
    # Timing
    timestamp: datetime
    expected_duration: Optional[timedelta] = None
    expiry: Optional[datetime] = None
    
    # Signal metadata
    strength: SignalStrength = SignalStrength.MODERATE
    confidence: float = 0.5  # 0.0 to 1.0
    indicators: Dict[str, Any] = None  # Indicator values used
    
    # Bias flags
    bias_flags: list = field(default_factory=list)  # List of detected biases
    
    # AI enhancements
    ai_enhancements: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize default values"""
        if self.indicators is None:
            self.indicators = {}
        if self.expected_duration is None:
            # Set default based on category
            from .trade_categories import TradeCategoryClassifier
            config = TradeCategoryClassifier.get_config(self.category)
            self.expected_duration = config.time_horizon_max
    
    def calculate_risk_reward(self) -> float:
        """Calculate risk/reward ratio"""
        if self.stop_loss_pct == 0:
            return 0.0
        return self.take_profit_pct / self.stop_loss_pct
    
    def is_valid(self) -> bool:
        """Check if signal is valid"""
        # Check if signal has expired
        if self.expiry and datetime.now() > self.expiry:
            return False
        
        # Check if risk/reward is reasonable (at least 1:1)
        if self.risk_reward_ratio < 1.0:
            return False
        
        # Check if position size is within limits (1-2% risk)
        if not (0.01 <= self.position_size_pct <= 0.02):
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """Convert signal to dictionary"""
        return {
            "symbol": self.symbol,
            "signal_type": self.signal_type.value,
            "category": self.category.value,
            "entry_price": self.entry_price,
            "take_profit": self.take_profit,
            "stop_loss": self.stop_loss,
            "take_profit_pct": self.take_profit_pct,
            "stop_loss_pct": self.stop_loss_pct,
            "risk_reward_ratio": self.risk_reward_ratio,
            "position_size_pct": self.position_size_pct,
            "timestamp": self.timestamp.isoformat(),
            "expected_duration_hours": self.expected_duration.total_seconds() / 3600 if self.expected_duration else None,
            "expiry": self.expiry.isoformat() if self.expiry else None,
            "strength": self.strength.value,
            "confidence": self.confidence,
            "indicators": self.indicators,
            "bias_flags": [str(flag) for flag in self.bias_flags],
            "ai_enhancements": self.ai_enhancements,
            "is_valid": self.is_valid()
        }

