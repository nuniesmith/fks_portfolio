"""
Signal generation API routes
"""
import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger
from datetime import datetime

from ..signals.signal_generator import SignalGenerator
from ..signals.trade_categories import TradeCategory
from ..signals.trading_signal import TradingSignal
from ..data.manager import DataManager
from ..data.asset_config import AssetConfigManager

# Import lot size calculator from local utils
try:
    from ..utils.signal_utils import SignalLotSizeCalculator, EntryPriceManager
    from ..utils.registry import AssetCategory
    LOT_SIZE_AVAILABLE = True
except ImportError as e:
    LOT_SIZE_AVAILABLE = False
    logger.warning(f"Lot size calculator not available: {e}")


router = APIRouter(prefix="/api/signals", tags=["signals"])

# Initialize services
data_manager = DataManager()
config_manager = AssetConfigManager()
signal_generator = SignalGenerator(data_manager=data_manager, config_manager=config_manager)

# Initialize lot size calculator if available
lot_calculator = None
entry_manager = None
if LOT_SIZE_AVAILABLE:
    lot_calculator = SignalLotSizeCalculator(account_balance_usd=10000.0, risk_per_trade_pct=1.0)
    entry_manager = EntryPriceManager()


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


@router.get("/from-files")
async def get_signals_from_files(
    date: Optional[str] = None,
    category: Optional[str] = None,
    symbol: Optional[str] = None,
    include_lot_size: bool = True
):
    """
    Load signals from JSON files in signals directory
    
    Args:
        date: Date in YYYYMMDD format (default: today)
        category: Filter by category (scalp, swing, long_term)
        symbol: Filter by symbol
        include_lot_size: Include lot size calculations
    
    Returns:
        Dictionary with signals and metadata
    """
    try:
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        
        # Use environment variable or fallback to default path
        # In Docker, this will be /app/signals (mounted volume)
        # Locally, it will be the absolute path
        signals_dir = Path(os.getenv(
            "SIGNALS_DIR",
            "/app/signals" if os.path.exists("/app/signals") else "/home/jordan/Nextcloud/code/repos/fks/signals"
        ))
        signals = {}
        
        # Load category-specific files
        categories_to_load = [category] if category else ["scalp", "swing", "long_term"]
        
        for cat in categories_to_load:
            signal_file = signals_dir / f"signals_{cat}_{date}.json"
            
            if signal_file.exists():
                with open(signal_file, 'r') as f:
                    cat_signals = json.load(f)
                    if isinstance(cat_signals, list):
                        signals[cat] = cat_signals
                    else:
                        signals[cat] = [cat_signals]
            else:
                signals[cat] = []
        
        # Filter by symbol if provided
        if symbol:
            for cat in signals:
                signals[cat] = [s for s in signals[cat] if s.get("symbol", "").upper() == symbol.upper()]
        
        # Enrich with lot sizes if requested
        if include_lot_size and lot_calculator:
            for cat in signals:
                for signal in signals[cat]:
                    try:
                        lot_calc = lot_calculator.calculate_for_signal(signal)
                        signal["lot_size"] = lot_calc.to_dict()
                        
                        if entry_manager:
                            # Add entry planning
                            # Determine asset category from symbol
                            from ..utils.registry import get_asset, AssetCategory
                            asset = get_asset(signal.get("symbol", ""))
                            asset_cat = asset.category if asset else AssetCategory.CRYPTO  # Default to crypto
                            
                            entry_info = entry_manager.calculate_entry_price_for_next_day(
                                current_price=signal.get("entry_price", 0),
                                signal=signal,
                                asset_category=asset_cat
                            )
                            signal["entry_planning"] = entry_info
                    except Exception as e:
                        logger.warning(f"Error calculating lot size for signal: {e}")
        
        # Load summary and performance
        summary = None
        summary_file = signals_dir / f"daily_signals_summary_{date}.json"
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                summary = json.load(f)
        
        performance = None
        perf_file = signals_dir / "performance" / f"performance_{date}.json"
        if perf_file.exists():
            with open(perf_file, 'r') as f:
                performance = json.load(f)
        
        return {
            "date": date,
            "signals": signals,
            "summary": summary,
            "performance": performance,
            "lot_size_enabled": include_lot_size and lot_calculator is not None
        }
    
    except Exception as e:
        logger.error(f"Error loading signals from files: {e}")
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

