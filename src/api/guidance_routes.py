"""
Guidance and decision support API routes
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from ..guidance.decision_support import DecisionSupport, DecisionRecommendation, RecommendationType
from ..guidance.workflow import ManualWorkflow, WorkflowStep
from ..guidance.tracking import PortfolioTracker
from ..signals.signal_generator import SignalGenerator
from ..signals.trade_categories import TradeCategory
from ..portfolio.portfolio import Portfolio
from ..data.manager import DataManager
from ..data.asset_config import AssetConfigManager
from ..data.btc_converter import BTCConverter


router = APIRouter(prefix="/api/guidance", tags=["guidance"])

# Initialize services
data_manager = DataManager()
config_manager = AssetConfigManager()
btc_converter = BTCConverter(data_manager=data_manager)
signal_generator = SignalGenerator(data_manager=data_manager, config_manager=config_manager)
decision_support = DecisionSupport(btc_converter=btc_converter)
workflow = ManualWorkflow()
tracker = PortfolioTracker(btc_converter=btc_converter, data_manager=data_manager)


class RecommendationResponse(BaseModel):
    """Recommendation response"""
    recommendation: str
    confidence: float
    risk_level: str
    rationale: str
    bias_warnings: List[str]
    alternatives: List[str]
    signal: dict


class WorkflowStepResponse(BaseModel):
    """Workflow step response"""
    step_number: int
    title: str
    description: str
    action_required: str
    completed: bool


@router.get("/recommendations")
async def get_recommendations(
    category: str = "swing",
    symbols: Optional[str] = None
):
    """
    Get decision recommendations for signals
    
    Args:
        category: Trade category
        symbols: Comma-separated list of symbols
    
    Returns:
        List of recommendations
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
        signals = await signal_generator.generate_daily_signals(trade_category, symbol_list, ai_enhanced=False)
        
        # Get recommendations
        recommendations = decision_support.get_decision_guidance(signals)
        
        # Convert to response
        response = [
            RecommendationResponse(
                recommendation=rec.recommendation.value,
                confidence=rec.confidence,
                risk_level=rec.risk_level,
                rationale=rec.rationale,
                bias_warnings=rec.bias_warnings,
                alternatives=rec.alternatives,
                signal=rec.signal.to_dict() if rec.signal else {}
            )
            for rec in recommendations
        ]
        
        return {
            "recommendations": response,
            "count": len(response)
        }
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow")
async def get_workflow(
    symbol: str,
    category: str = "swing"
):
    """
    Get execution workflow for a signal
    
    Args:
        symbol: Asset symbol
        category: Trade category
    
    Returns:
        Workflow steps
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
        
        # Generate signal
        signals = await signal_generator.generate_daily_signals(trade_category, [symbol], ai_enhanced=False)
        
        if not signals:
            raise HTTPException(status_code=404, detail=f"No signal found for {symbol}")
        
        signal = signals[0]
        recommendation = decision_support.analyze_signal(signal)
        
        # Create workflow
        steps = workflow.create_execution_workflow(signal, recommendation)
        
        # Convert to response
        response = [
            WorkflowStepResponse(
                step_number=step.step_number,
                title=step.title,
                description=step.description,
                action_required=step.action_required,
                completed=step.completed
            )
            for step in steps
        ]
        
        return {
            "symbol": symbol,
            "signal": signal.to_dict(),
            "recommendation": recommendation.recommendation.value,
            "workflow": response,
            "summary": workflow.get_workflow_summary(steps)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance(days: int = 30):
    """
    Get portfolio performance metrics
    
    Args:
        days: Number of days to analyze
    
    Returns:
        Performance metrics
    """
    try:
        metrics = tracker.get_performance_metrics(days=days)
        stats = tracker.get_decision_statistics()
        
        return {
            "metrics": metrics,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_decision_history(
    days: int = 30,
    symbol: Optional[str] = None
):
    """
    Get decision history
    
    Args:
        days: Number of days to look back
        symbol: Optional symbol filter
    
    Returns:
        Decision history
    """
    try:
        history = tracker.get_decision_history(days=days, symbol=symbol)
        
        return {
            "history": [log.to_dict() for log in history],
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/log")
async def log_decision(
    signal_data: dict,
    recommendation: str,
    decision: str,
    execution_price: Optional[float] = None,
    execution_notes: Optional[str] = None
):
    """
    Log a trading decision
    
    Args:
        signal_data: Signal data (from signal.to_dict())
        recommendation: Recommendation type
        decision: Decision made ("executed", "rejected", "pending")
        execution_price: Execution price
        execution_notes: Optional notes
    
    Returns:
        Success status
    """
    try:
        # Reconstruct signal (simplified - in production would use proper deserialization)
        from ..signals.trading_signal import TradingSignal, SignalType, SignalStrength
        from ..signals.trade_categories import TradeCategory
        
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
        
        # Create recommendation
        rec = DecisionRecommendation(
            recommendation=RecommendationType(recommendation),
            signal=signal,
            rationale="",
            confidence=signal_data["confidence"],
            risk_level="medium",
            bias_warnings=[],
            alternatives=[],
            timestamp=datetime.now()
        )
        
        # Log decision
        tracker.log_decision(signal, rec, decision, execution_price, execution_notes)
        
        return {"status": "logged", "decision": decision}
    except Exception as e:
        logger.error(f"Error logging decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

