"""
AI Comparison Backtesting
Compare baseline vs AI-enhanced signals
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from ..signals.signal_generator import SignalGenerator
from ..signals.trade_categories import TradeCategory
from ..signals.trading_signal import TradingSignal
from ..data.manager import DataManager
from ..data.asset_config import AssetConfigManager


class AIComparisonBacktest:
    """Compare baseline vs AI-enhanced signals"""
    
    def __init__(
        self,
        data_manager: Optional[DataManager] = None,
        config_manager: Optional[AssetConfigManager] = None
    ):
        """
        Initialize comparison backtest
        
        Args:
            data_manager: DataManager instance
            config_manager: AssetConfigManager instance
        """
        self.data_manager = data_manager or DataManager()
        self.config_manager = config_manager or AssetConfigManager()
        self.signal_generator = SignalGenerator(
            data_manager=self.data_manager,
            config_manager=self.config_manager
        )
        self.logger = logger.bind(component="AIComparisonBacktest")
    
    async def compare_baseline_vs_ai(
        self,
        start_date: datetime,
        end_date: datetime,
        category: TradeCategory = TradeCategory.SWING,
        symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare baseline vs AI-enhanced signals
        
        Args:
            start_date: Start date for backtest
            end_date: End date for backtest
            category: Trade category
            symbols: Optional list of symbols
        
        Returns:
            Comparison results
        """
        try:
            self.logger.info(f"Comparing baseline vs AI from {start_date} to {end_date}")
            
            # Generate baseline signals
            baseline_signals = await self.signal_generator.generate_daily_signals(
                category, symbols, ai_enhanced=False
            )
            
            # Generate AI-enhanced signals
            ai_signals = await self.signal_generator.generate_daily_signals(
                category, symbols, ai_enhanced=True
            )
            
            # Calculate metrics for baseline
            baseline_metrics = self._calculate_metrics(baseline_signals, "baseline")
            
            # Calculate metrics for AI
            ai_metrics = self._calculate_metrics(ai_signals, "ai_enhanced")
            
            # Calculate improvements
            improvements = self._calculate_improvements(baseline_metrics, ai_metrics)
            
            return {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "baseline": baseline_metrics,
                "ai_enhanced": ai_metrics,
                "improvements": improvements,
                "summary": self._generate_summary(baseline_metrics, ai_metrics, improvements)
            }
            
        except Exception as e:
            self.logger.error(f"Error in comparison backtest: {e}")
            raise
    
    def _calculate_metrics(
        self,
        signals: List[TradingSignal],
        signal_type: str
    ) -> Dict[str, Any]:
        """
        Calculate metrics for signals
        
        Args:
            signals: List of signals
            signal_type: "baseline" or "ai_enhanced"
        
        Returns:
            Metrics dictionary
        """
        if not signals:
            return {
                "signal_count": 0,
                "avg_confidence": 0.0,
                "avg_risk_reward": 0.0,
                "avg_position_size": 0.0,
                "strong_signals": 0,
                "very_strong_signals": 0
            }
        
        from ..signals.trading_signal import SignalStrength
        
        strong_count = sum(1 for s in signals if s.strength == SignalStrength.STRONG)
        very_strong_count = sum(1 for s in signals if s.strength == SignalStrength.VERY_STRONG)
        
        return {
            "signal_count": len(signals),
            "avg_confidence": sum(s.confidence for s in signals) / len(signals),
            "avg_risk_reward": sum(s.risk_reward_ratio for s in signals) / len(signals),
            "avg_position_size": sum(s.position_size_pct for s in signals) / len(signals),
            "strong_signals": strong_count,
            "very_strong_signals": very_strong_count,
            "signal_type": signal_type
        }
    
    def _calculate_improvements(
        self,
        baseline: Dict[str, Any],
        ai: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate improvements from baseline to AI
        
        Args:
            baseline: Baseline metrics
            ai: AI metrics
        
        Returns:
            Improvements dictionary
        """
        improvements = {}
        
        # Confidence improvement
        if baseline["avg_confidence"] > 0:
            confidence_delta = ai["avg_confidence"] - baseline["avg_confidence"]
            confidence_pct = (confidence_delta / baseline["avg_confidence"]) * 100
            improvements["confidence"] = {
                "delta": confidence_delta,
                "percent_change": confidence_pct
            }
        
        # Risk/reward improvement
        if baseline["avg_risk_reward"] > 0:
            rr_delta = ai["avg_risk_reward"] - baseline["avg_risk_reward"]
            rr_pct = (rr_delta / baseline["avg_risk_reward"]) * 100
            improvements["risk_reward"] = {
                "delta": rr_delta,
                "percent_change": rr_pct
            }
        
        # Signal quality improvement
        if baseline["signal_count"] > 0:
            strong_delta = ai["strong_signals"] - baseline["strong_signals"]
            very_strong_delta = ai["very_strong_signals"] - baseline["very_strong_signals"]
            improvements["signal_quality"] = {
                "strong_signals_delta": strong_delta,
                "very_strong_signals_delta": very_strong_delta
            }
        
        return improvements
    
    def _generate_summary(
        self,
        baseline: Dict[str, Any],
        ai: Dict[str, Any],
        improvements: Dict[str, Any]
    ) -> str:
        """
        Generate summary text
        
        Args:
            baseline: Baseline metrics
            ai: AI metrics
            improvements: Improvements dictionary
        
        Returns:
            Summary string
        """
        summary_parts = []
        
        # Signal count
        summary_parts.append(
            f"Baseline: {baseline['signal_count']} signals, "
            f"AI: {ai['signal_count']} signals"
        )
        
        # Confidence
        if "confidence" in improvements:
            conf_imp = improvements["confidence"]
            summary_parts.append(
                f"Confidence: {conf_imp['percent_change']:+.1f}% "
                f"({baseline['avg_confidence']:.2f} → {ai['avg_confidence']:.2f})"
            )
        
        # Risk/reward
        if "risk_reward" in improvements:
            rr_imp = improvements["risk_reward"]
            summary_parts.append(
                f"Risk/Reward: {rr_imp['percent_change']:+.1f}% "
                f"({baseline['avg_risk_reward']:.2f} → {ai['avg_risk_reward']:.2f})"
            )
        
        # Signal quality
        if "signal_quality" in improvements:
            sq_imp = improvements["signal_quality"]
            summary_parts.append(
                f"Strong signals: {sq_imp['strong_signals_delta']:+d}, "
                f"Very strong: {sq_imp['very_strong_signals_delta']:+d}"
            )
        
        return ". ".join(summary_parts)
    
    async def generate_performance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        category: TradeCategory = TradeCategory.SWING,
        symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        
        Args:
            start_date: Start date
            end_date: End date
            category: Trade category
            symbols: Optional symbols
        
        Returns:
            Performance report
        """
        comparison = await self.compare_baseline_vs_ai(
            start_date, end_date, category, symbols
        )
        
        # Add recommendations
        recommendations = self._generate_recommendations(comparison)
        
        return {
            **comparison,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }
    
    def _generate_recommendations(
        self,
        comparison: Dict[str, Any]
    ) -> List[str]:
        """
        Generate recommendations based on comparison
        
        Args:
            comparison: Comparison results
        
        Returns:
            List of recommendations
        """
        recommendations = []
        improvements = comparison.get("improvements", {})
        
        # Confidence recommendations
        if "confidence" in improvements:
            conf_imp = improvements["confidence"]
            if conf_imp["percent_change"] > 10:
                recommendations.append(
                    f"AI significantly improves confidence (+{conf_imp['percent_change']:.1f}%) - "
                    "consider using AI-enhanced signals"
                )
            elif conf_imp["percent_change"] < -5:
                recommendations.append(
                    f"AI reduces confidence ({conf_imp['percent_change']:.1f}%) - "
                    "review AI integration or use baseline signals"
                )
        
        # Risk/reward recommendations
        if "risk_reward" in improvements:
            rr_imp = improvements["risk_reward"]
            if rr_imp["percent_change"] > 5:
                recommendations.append(
                    f"AI improves risk/reward ratio (+{rr_imp['percent_change']:.1f}%) - "
                    "AI-enhanced signals show better risk management"
                )
        
        # Signal quality recommendations
        if "signal_quality" in improvements:
            sq_imp = improvements["signal_quality"]
            if sq_imp["very_strong_signals_delta"] > 0:
                recommendations.append(
                    f"AI generates {sq_imp['very_strong_signals_delta']} more very strong signals - "
                    "AI helps identify high-quality opportunities"
                )
        
        if not recommendations:
            recommendations.append("AI and baseline signals show similar performance - continue monitoring")
        
        return recommendations

