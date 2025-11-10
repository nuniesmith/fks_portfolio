"""
Trade Category Definitions
Categorizes trades by time horizon and strategy
"""
from enum import Enum
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import timedelta


class TradeCategory(Enum):
    """Trade category types"""
    SCALP = "scalp"           # Seconds to minutes
    INTRADAY = "intraday"     # Minutes to hours
    SWING = "swing"           # Days to weeks
    LONG_TERM = "long_term"   # Weeks to months/years


@dataclass
class TradeCategoryConfig:
    """Configuration for a trade category"""
    category: TradeCategory
    time_horizon_min: timedelta
    time_horizon_max: timedelta
    take_profit_pct: Tuple[float, float]  # Min and max TP %
    stop_loss_pct: Tuple[float, float]     # Min and max SL %
    indicators: list                        # Recommended indicators
    description: str


class TradeCategoryClassifier:
    """Classifies trades into categories"""
    
    # Category configurations
    CATEGORIES: Dict[TradeCategory, TradeCategoryConfig] = {
        TradeCategory.SCALP: TradeCategoryConfig(
            category=TradeCategory.SCALP,
            time_horizon_min=timedelta(seconds=30),
            time_horizon_max=timedelta(minutes=15),
            take_profit_pct=(0.1, 0.5),      # 0.1% to 0.5%
            stop_loss_pct=(0.05, 0.2),       # 0.05% to 0.2%
            indicators=["order_book", "tick_data", "momentum", "volume_spike"],
            description="Very short-term trades, seconds to minutes"
        ),
        TradeCategory.INTRADAY: TradeCategoryConfig(
            category=TradeCategory.INTRADAY,
            time_horizon_min=timedelta(minutes=15),
            time_horizon_max=timedelta(hours=24),
            take_profit_pct=(0.5, 2.0),      # 0.5% to 2%
            stop_loss_pct=(0.2, 1.0),       # 0.2% to 1%
            indicators=["rsi", "macd", "bollinger_bands", "volume", "support_resistance"],
            description="Intraday trades, minutes to hours, closed same day"
        ),
        TradeCategory.SWING: TradeCategoryConfig(
            category=TradeCategory.SWING,
            time_horizon_min=timedelta(days=1),
            time_horizon_max=timedelta(weeks=4),
            take_profit_pct=(2.0, 10.0),     # 2% to 10%
            stop_loss_pct=(1.0, 5.0),        # 1% to 5%
            indicators=["ema", "sma", "rsi", "macd", "fibonacci", "chart_patterns"],
            description="Swing trades, days to weeks"
        ),
        TradeCategory.LONG_TERM: TradeCategoryConfig(
            category=TradeCategory.LONG_TERM,
            time_horizon_min=timedelta(weeks=4),
            time_horizon_max=timedelta(days=365),
            take_profit_pct=(10.0, 50.0),    # 10% to 50%
            stop_loss_pct=(5.0, 15.0),       # 5% to 15%
            indicators=["fundamentals", "trend", "ema_long", "support_resistance_major"],
            description="Long-term positions, weeks to months/years"
        )
    }
    
    @classmethod
    def get_config(cls, category: TradeCategory) -> TradeCategoryConfig:
        """Get configuration for a category"""
        return cls.CATEGORIES[category]
    
    @classmethod
    def classify_by_time_horizon(cls, time_horizon: timedelta) -> TradeCategory:
        """
        Classify trade by time horizon
        
        Args:
            time_horizon: Expected trade duration
        
        Returns:
            Trade category
        """
        for category, config in cls.CATEGORIES.items():
            if config.time_horizon_min <= time_horizon <= config.time_horizon_max:
                return category
        
        # Default to swing if not in range
        return TradeCategory.SWING
    
    @classmethod
    def classify_by_tp_sl(
        cls,
        take_profit_pct: float,
        stop_loss_pct: float
    ) -> TradeCategory:
        """
        Classify trade by TP/SL percentages
        
        Args:
            take_profit_pct: Take profit percentage
            stop_loss_pct: Stop loss percentage
        
        Returns:
            Trade category
        """
        # Calculate risk/reward ratio
        risk_reward = take_profit_pct / stop_loss_pct if stop_loss_pct > 0 else 0
        
        # Classify based on TP/SL ranges
        for category, config in cls.CATEGORIES.items():
            tp_min, tp_max = config.take_profit_pct
            sl_min, sl_max = config.stop_loss_pct
            
            if (tp_min <= take_profit_pct <= tp_max and
                sl_min <= stop_loss_pct <= sl_max):
                return category
        
        # Default classification based on TP size
        if take_profit_pct < 0.5:
            return TradeCategory.SCALP
        elif take_profit_pct < 2.0:
            return TradeCategory.INTRADAY
        elif take_profit_pct < 10.0:
            return TradeCategory.SWING
        else:
            return TradeCategory.LONG_TERM
    
    @classmethod
    def get_tp_sl_range(cls, category: TradeCategory) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Get TP/SL range for a category
        
        Args:
            category: Trade category
        
        Returns:
            Tuple of (TP range, SL range)
        """
        config = cls.get_config(category)
        return config.take_profit_pct, config.stop_loss_pct
    
    @classmethod
    def get_recommended_indicators(cls, category: TradeCategory) -> list:
        """Get recommended indicators for a category"""
        config = cls.get_config(category)
        return config.indicators
    
    @classmethod
    def get_all_categories(cls) -> list:
        """Get all trade categories"""
        return list(cls.CATEGORIES.keys())
    
    @classmethod
    def get_category_description(cls, category: TradeCategory) -> str:
        """Get description for a category"""
        config = cls.get_config(category)
        return config.description

