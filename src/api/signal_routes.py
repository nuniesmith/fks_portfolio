"""
Signal generation API routes
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from ..signals.signal_generator import SignalGenerator
from ..signals.trade_categories import TradeCategory
from ..signals.trading_signal import TradingSignal
from ..data.manager import DataManager
from ..data.asset_config import AssetConfigManager


router = APIRouter(prefix="/api/signals", tags=["signals"])

# Initialize services
data_manager = DataManager()
config_manager = AssetConfigManager()
signal_generator = SignalGenerator(data_manager=data_manager, config_manager=config_manager)


class SignalResponse(BaseModel):
    """Signal response model"""
    symbol: str
    signal_type: str
    category: str
    entry_price: float
    take_profit: float
    stop_loss: float
    take_profit_pct: float
    stop_loss_pct: float
    risk_reward_ratio: float
    position_size_pct: float
    strength: str
    confidence: float
    timestamp: str
    is_valid: bool


@router.get("/generate")
async def generate_signals(
    category: str = "swing",
    symbols: Optional[str] = None,
    ai_enhanced: bool = False
):
    """
    Generate trading signals
    
    Args:
        category: Trade category (scalp, intraday, swing, long_term)
        symbols: Comma-separated list of symbols (default: enabled assets)
    
    Returns:
        List of trading signals
    """
    try:
        # Parse category
        category_map = {
            "scalp": TradeCategory.SCALP,
            "intraday": TradeCategory.INTRADAY,
            "swing": TradeCategory.SWING,
            "long_term": TradeCategory.LONG_TERM
        }
        
        trade_category = category_map.get(category.lower(), TradeCategory.SWING)
        
        # Parse symbols
        symbol_list = None
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
        
        # Generate signals
        signals = await signal_generator.generate_daily_signals(trade_category, symbol_list, ai_enhanced=ai_enhanced)
        
        # Convert to response format
        response = [SignalResponse(**signal.to_dict()) for signal in signals]
        
        return {
            "signals": response,
            "count": len(response),
            "category": category
        }
    except Exception as e:
        logger.error(f"Error generating signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_signal_summary(
    category: str = "swing",
    symbols: Optional[str] = None
):
    """
    Get signal summary
    
    Args:
        category: Trade category
        symbols: Comma-separated list of symbols
    
    Returns:
        Signal summary statistics
    """
    try:
        category_map = {
            "scalp": TradeCategory.SCALP,
            "intraday": TradeCategory.INTRADAY,
            "swing": TradeCategory.SWING,
            "long_term": TradeCategory.LONG_TERM
        }
        
        trade_category = category_map.get(category.lower(), TradeCategory.SWING)
        
        symbol_list = None
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
        
        signals = await signal_generator.generate_daily_signals(trade_category, symbol_list, ai_enhanced=False)
        summary = signal_generator.get_signal_summary(signals)
        
        return summary
    except Exception as e:
        logger.error(f"Error getting signal summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_categories():
    """Get all trade categories"""
    from ..signals.trade_categories import TradeCategoryClassifier
    
    categories = []
    for cat in TradeCategoryClassifier.get_all_categories():
        config = TradeCategoryClassifier.get_config(cat)
        categories.append({
            "category": cat.value,
            "description": config.description,
            "tp_range": config.take_profit_pct,
            "sl_range": config.stop_loss_pct,
            "time_horizon_min_hours": config.time_horizon_min.total_seconds() / 3600,
            "time_horizon_max_hours": config.time_horizon_max.total_seconds() / 3600,
            "indicators": config.indicators
        })
    
    return {"categories": categories}

