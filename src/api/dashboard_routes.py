"""
Dashboard API routes
Provides data endpoints for dashboard visualization
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from loguru import logger

from ..dashboard.data_provider import DashboardDataProvider
from ..dashboard.charts import ChartDataGenerator
from ..data.manager import DataManager
from ..data.asset_config import AssetConfigManager


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# Initialize services
data_manager = DataManager()
config_manager = AssetConfigManager()
data_provider = DashboardDataProvider(data_manager=data_manager, config_manager=config_manager)
chart_generator = ChartDataGenerator(data_manager=data_manager, config_manager=config_manager)


@router.get("/overview")
async def get_dashboard_overview():
    """
    Get dashboard overview data
    
    Returns:
        Portfolio overview with assets, prices, and signals
    """
    try:
        overview = await data_provider.get_portfolio_overview()
        return overview
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_portfolio_performance(days: int = 30):
    """
    Get portfolio performance metrics
    
    Args:
        days: Number of days to analyze
    
    Returns:
        Performance metrics for tracked assets
    """
    try:
        performance = await data_provider.get_portfolio_performance(days=days)
        return performance
    except Exception as e:
        logger.error(f"Error getting portfolio performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/summary")
async def get_signal_summary(category: Optional[str] = None):
    """
    Get signal summary for dashboard
    
    Args:
        category: Optional trade category filter
    
    Returns:
        Signal summary by category
    """
    try:
        summary = await data_provider.get_signal_summary(category=category)
        return summary
    except Exception as e:
        logger.error(f"Error getting signal summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correlation")
async def get_correlation_matrix(
    symbols: Optional[str] = None,
    days: int = 90
):
    """
    Get asset correlation matrix
    
    Args:
        symbols: Comma-separated list of symbols (default: enabled assets)
        days: Number of days for correlation calculation
    
    Returns:
        Correlation matrix data
    """
    try:
        symbol_list = None
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
        
        correlation = await data_provider.get_asset_correlation_matrix(
            symbols=symbol_list,
            days=days
        )
        return correlation
    except Exception as e:
        logger.error(f"Error getting correlation matrix: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/price/{symbol}")
async def get_price_chart(
    symbol: str,
    days: int = 30
):
    """
    Get price chart data for a symbol
    
    Args:
        symbol: Asset symbol
        days: Number of days of data
    
    Returns:
        Price chart data
    """
    try:
        chart_data = chart_generator.generate_price_chart_data(symbol.upper(), days=days)
        return chart_data
    except Exception as e:
        logger.error(f"Error generating price chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/allocation")
async def get_allocation_chart(allocations: Optional[str] = None):
    """
    Get portfolio allocation chart data
    
    Args:
        allocations: JSON string of allocations (optional, uses default if not provided)
    
    Returns:
        Allocation chart data
    """
    try:
        if allocations:
            import json
            alloc_dict = json.loads(allocations)
        else:
            # Default allocation (BTC-focused)
            alloc_dict = {
                "BTC": 0.55,
                "ETH": 0.20,
                "SPY": 0.15,
                "GLD": 0.10
            }
        
        chart_data = chart_generator.generate_portfolio_allocation_chart(alloc_dict)
        return chart_data
    except Exception as e:
        logger.error(f"Error generating allocation chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/performance")
async def get_performance_comparison_chart(
    symbols: Optional[str] = None,
    days: int = 30
):
    """
    Get performance comparison chart data
    
    Args:
        symbols: Comma-separated list of symbols
        days: Number of days to compare
    
    Returns:
        Performance comparison chart data
    """
    try:
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
        else:
            # Default to top enabled assets
            enabled = config_manager.get_enabled_assets()
            symbol_list = [a.symbol for a in enabled[:5]]
        
        chart_data = chart_generator.generate_performance_comparison_chart(symbol_list, days=days)
        return chart_data
    except Exception as e:
        logger.error(f"Error generating performance comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/signals")
async def get_signal_distribution_chart(category: Optional[str] = None):
    """
    Get signal distribution chart data
    
    Args:
        category: Optional trade category filter
    
    Returns:
        Signal distribution chart data
    """
    try:
        from ..signals.signal_generator import SignalGenerator
        from ..signals.trade_categories import TradeCategory
        
        signal_gen = SignalGenerator(data_manager=data_manager, config_manager=config_manager)
        
        if category:
            category_map = {
                "scalp": TradeCategory.SCALP,
                "intraday": TradeCategory.INTRADAY,
                "swing": TradeCategory.SWING,
                "long_term": TradeCategory.LONG_TERM
            }
            trade_category = category_map.get(category.lower(), TradeCategory.SWING)
            signals = await signal_gen.generate_daily_signals(trade_category, ai_enhanced=False)
        else:
            # Get signals from all categories
            signals = []
            for cat in [TradeCategory.SCALP, TradeCategory.INTRADAY, TradeCategory.SWING, TradeCategory.LONG_TERM]:
                cat_signals = await signal_gen.generate_daily_signals(cat, ai_enhanced=False)
                signals.extend(cat_signals)
        
        chart_data = chart_generator.generate_signal_distribution_chart(signals)
        return chart_data
    except Exception as e:
        logger.error(f"Error generating signal distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

