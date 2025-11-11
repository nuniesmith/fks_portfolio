"""
AI-specific API routes
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from ..ai.client import AIServiceClient
from ..ai.signal_refiner import AISignalRefiner
from ..ai.bias_mitigation import AIBiasMitigator
from ..ai.btc_optimizer import BTCAIOptimizer
from ..signals.signal_generator import SignalGenerator
from ..signals.trade_categories import TradeCategory
from ..portfolio.portfolio import Portfolio
from ..data.manager import DataManager
from ..data.asset_config import AssetConfigManager
from ..backtesting.ai_comparison import AIComparisonBacktest
from datetime import datetime, timedelta


router = APIRouter(prefix="/api/ai", tags=["ai"])

# Initialize services
data_manager = DataManager()
config_manager = AssetConfigManager()
signal_generator = SignalGenerator(data_manager=data_manager, config_manager=config_manager)
ai_client = AIServiceClient()
signal_refiner = AISignalRefiner(ai_client=ai_client)
bias_mitigator = AIBiasMitigator(ai_client=ai_client)
btc_optimizer = BTCAIOptimizer(ai_client=ai_client)
comparison_backtest = AIComparisonBacktest(data_manager=data_manager, config_manager=config_manager)


class AIAnalysisResponse(BaseModel):
    """AI analysis response"""
    symbol: str
    confidence: float
    decision: str
    summary: str
    bull_consensus: Optional[float] = None
    bear_consensus: Optional[float] = None


class AIBiasResponse(BaseModel):
    """AI bias detection response"""
    bias_detected: bool
    bias_type: Optional[str] = None
    ai_confidence: float
    rule_based_flags: int
    mitigation: Dict[str, Any]
    recommendation: str


class BTCOptimizationResponse(BaseModel):
    """BTC optimization response"""
    current_allocation: float
    target_allocation: float
    action: str
    difference: float
    rationale: str


@router.get("/analyze/{symbol}")
async def analyze_symbol(symbol: str):
    """
    Get AI analysis for a symbol
    
    Args:
        symbol: Asset symbol
    
    Returns:
        AI analysis response
    """
    try:
        analysis = await ai_client.analyze_symbol(symbol.upper())
        
        return AIAnalysisResponse(
            symbol=symbol.upper(),
            confidence=analysis.get("confidence", 0.5),
            decision=analysis.get("final_decision", "HOLD"),
            summary=analysis.get("summary", ""),
            bull_consensus=analysis.get("bull_consensus"),
            bear_consensus=analysis.get("bear_consensus")
        )
    except Exception as e:
        logger.error(f"Error getting AI analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/enhanced")
async def get_enhanced_signals(
    category: str = "swing",
    symbols: Optional[str] = None
):
    """
    Get AI-enhanced trading signals
    
    Args:
        category: Trade category
        symbols: Comma-separated list of symbols
    
    Returns:
        List of AI-enhanced signals
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
        
        # Generate AI-enhanced signals
        signals = await signal_generator.generate_daily_signals(
            trade_category,
            symbol_list,
            ai_enhanced=True
        )
        
        return {
            "signals": [signal.to_dict() for signal in signals],
            "count": len(signals),
            "category": category,
            "ai_enhanced": True
        }
    except Exception as e:
        logger.error(f"Error generating AI-enhanced signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bias-check")
async def check_bias(signal_data: dict):
    """
    Check signal for bias using AI
    
    Args:
        signal_data: Signal data dictionary
    
    Returns:
        Bias detection response
    """
    try:
        from ..signals.trading_signal import TradingSignal, SignalType, SignalStrength
        from ..signals.trade_categories import TradeCategory
        from datetime import datetime
        
        # Reconstruct signal
        signal = TradingSignal(
            symbol=signal_data["symbol"],
            signal_type=SignalType(signal_data["signal_type"]),
            category=TradeCategory(signal_data["category"]),
            entry_price=signal_data["entry_price"],
            take_profit=signal_data["take_profit"],
            stop_loss=signal_data["stop_loss"],
            take_profit_pct=signal_data["take_profit_pct"],
            stop_loss_pct=signal_data["stop_loss_pct"],
            risk_reward_ratio=signal_data["risk_reward_ratio"],
            position_size_pct=signal_data["position_size_pct"],
            timestamp=datetime.fromisoformat(signal_data["timestamp"]),
            strength=SignalStrength(signal_data["strength"]),
            confidence=signal_data["confidence"]
        )
        
        # Check bias
        bias_result = await bias_mitigator.detect_and_mitigate(signal)
        
        return AIBiasResponse(**bias_result)
    except Exception as e:
        logger.error(f"Error checking bias: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/btc-optimization")
async def get_btc_optimization(
    allocations: Optional[str] = None
):
    """
    Get AI-optimized BTC allocation recommendation
    
    Args:
        allocations: JSON string of current allocations (optional)
    
    Returns:
        BTC optimization recommendation
    """
    try:
        # Create portfolio from allocations or use default
        portfolio = Portfolio()
        
        if allocations:
            import json
            alloc_dict = json.loads(allocations)
            from ..portfolio.asset import CryptoAsset, StockAsset
            
            for symbol, weight in alloc_dict.items():
                if symbol.upper() in ["BTC", "ETH", "LTC"]:
                    portfolio.add_asset(CryptoAsset(symbol.upper()), weight)
                else:
                    portfolio.add_asset(StockAsset(symbol.upper()), weight)
        else:
            # Default sample portfolio
            from ..portfolio.asset import CryptoAsset, StockAsset
            portfolio.add_asset(CryptoAsset("BTC"), 0.5)
            portfolio.add_asset(CryptoAsset("ETH"), 0.2)
            portfolio.add_asset(StockAsset("SPY"), 0.3)
        
        # Get optimization recommendation
        recommendation = await btc_optimizer.get_btc_rebalancing_recommendation(portfolio)
        
        return BTCOptimizationResponse(**recommendation)
    except Exception as e:
        logger.error(f"Error getting BTC optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def ai_service_health():
    """
    Check AI service health
    
    Returns:
        Health status
    """
    try:
        is_healthy = await ai_client.health_check()
        agent_status = await ai_client.get_agent_status()
        
        return {
            "ai_service_healthy": is_healthy,
            "agent_status": agent_status,
            "service_url": ai_client.base_url
        }
    except Exception as e:
        logger.error(f"Error checking AI service health: {e}")
        return {
            "ai_service_healthy": False,
            "error": str(e),
            "service_url": ai_client.base_url
        }


@router.get("/compare")
async def compare_baseline_vs_ai(
    category: str = "swing",
    symbols: Optional[str] = None,
    days: int = 30
):
    """
    Compare baseline vs AI-enhanced signals
    
    Args:
        category: Trade category
        symbols: Comma-separated list of symbols
        days: Number of days to compare (default: 30)
    
    Returns:
        Comparison results
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
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Run comparison
        comparison = await comparison_backtest.compare_baseline_vs_ai(
            start_date, end_date, trade_category, symbol_list
        )
        
        return comparison
    except Exception as e:
        logger.error(f"Error comparing baseline vs AI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance-report")
async def get_performance_report(
    category: str = "swing",
    symbols: Optional[str] = None,
    days: int = 30
):
    """
    Get comprehensive performance report comparing baseline vs AI
    
    Args:
        category: Trade category
        symbols: Comma-separated list of symbols
        days: Number of days to analyze
    
    Returns:
        Performance report with recommendations
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
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Generate report
        report = await comparison_backtest.generate_performance_report(
            start_date, end_date, trade_category, symbol_list
        )
        
        return report
    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

