"""
Decision Support Module
Provides guidance and recommendations for trading decisions
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from ..signals.trading_signal import TradingSignal
from ..portfolio.portfolio import Portfolio
from ..risk.bias_detection import BiasDetector
from ..data.btc_converter import BTCConverter


class RecommendationType(Enum):
    """Recommendation type"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    AVOID = "avoid"


@dataclass
class DecisionRecommendation:
    """Decision recommendation with rationale"""
    recommendation: RecommendationType
    signal: Optional[TradingSignal]
    rationale: str
    confidence: float
    risk_level: str  # "low", "medium", "high"
    bias_warnings: List[str]
    alternatives: List[str]
    timestamp: datetime
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "recommendation": self.recommendation.value,
            "signal": self.signal.to_dict() if self.signal else None,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "bias_warnings": self.bias_warnings,
            "alternatives": self.alternatives,
            "timestamp": self.timestamp.isoformat()
        }


class DecisionSupport:
    """Provides decision support and guidance"""
    
    def __init__(
        self,
        portfolio: Optional[Portfolio] = None,
        btc_converter: Optional[BTCConverter] = None
    ):
        """
        Initialize decision support
        
        Args:
            portfolio: Portfolio instance
            btc_converter: BTCConverter instance
        """
        self.portfolio = portfolio
        self.btc_converter = btc_converter or BTCConverter()
        self.bias_detector = BiasDetector()
        self.logger = logger.bind(component="DecisionSupport")
    
    def analyze_signal(
        self,
        signal: TradingSignal,
        current_portfolio: Optional[Dict[str, float]] = None
    ) -> DecisionRecommendation:
        """
        Analyze signal and provide recommendation
        
        Args:
            signal: Trading signal to analyze
            current_portfolio: Current portfolio holdings
        
        Returns:
            Decision recommendation
        """
        # Check signal validity
        if not signal.is_valid():
            return DecisionRecommendation(
                recommendation=RecommendationType.AVOID,
                signal=signal,
                rationale="Signal is not valid (expired, low R/R, or invalid position size)",
                confidence=0.0,
                risk_level="high",
                bias_warnings=["Invalid signal"],
                alternatives=[],
                timestamp=datetime.now()
            )
        
        # Check biases
        bias_warnings = []
        if signal.bias_flags:
            for bias in signal.bias_flags:
                if hasattr(bias, 'message'):
                    bias_warnings.append(bias.message)
        
        # Analyze risk level
        risk_level = self._assess_risk_level(signal)
        
        # Determine recommendation
        recommendation = self._determine_recommendation(signal, risk_level, bias_warnings)
        
        # Generate rationale
        rationale = self._generate_rationale(signal, recommendation, risk_level, bias_warnings)
        
        # Calculate confidence
        confidence = self._calculate_confidence(signal, risk_level, bias_warnings)
        
        # Suggest alternatives
        alternatives = self._suggest_alternatives(signal, current_portfolio)
        
        return DecisionRecommendation(
            recommendation=recommendation,
            signal=signal,
            rationale=rationale,
            confidence=confidence,
            risk_level=risk_level,
            bias_warnings=bias_warnings,
            alternatives=alternatives,
            timestamp=datetime.now()
        )
    
    def _assess_risk_level(self, signal: TradingSignal) -> str:
        """Assess risk level of signal"""
        # Risk factors
        risk_score = 0
        
        # Position size risk
        if signal.position_size_pct > 0.02:
            risk_score += 2
        elif signal.position_size_pct > 0.015:
            risk_score += 1
        
        # Risk/reward risk
        if signal.risk_reward_ratio < 1.5:
            risk_score += 2
        elif signal.risk_reward_ratio < 2.0:
            risk_score += 1
        
        # Stop loss risk
        if signal.stop_loss_pct > 5.0:
            risk_score += 1
        
        # Category risk
        if signal.category.value == "scalp":
            risk_score += 2
        elif signal.category.value == "intraday":
            risk_score += 1
        
        # Confidence risk
        if signal.confidence < 0.5:
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 5:
            return "high"
        elif risk_score >= 3:
            return "medium"
        else:
            return "low"
    
    def _determine_recommendation(
        self,
        signal: TradingSignal,
        risk_level: str,
        bias_warnings: List[str]
    ) -> RecommendationType:
        """Determine recommendation based on signal"""
        # High bias warnings = avoid
        if len(bias_warnings) >= 2:
            return RecommendationType.AVOID
        
        # High risk = avoid or hold
        if risk_level == "high":
            if signal.confidence < 0.6:
                return RecommendationType.AVOID
            else:
                return RecommendationType.HOLD
        
        # Strong signals = strong buy
        if signal.strength.value == "very_strong" and signal.confidence >= 0.8:
            return RecommendationType.STRONG_BUY
        
        # Good signals = buy
        if signal.strength.value in ["strong", "very_strong"] and signal.confidence >= 0.6:
            return RecommendationType.BUY
        
        # Moderate signals = hold
        if signal.strength.value == "moderate":
            return RecommendationType.HOLD
        
        # Weak signals = avoid
        return RecommendationType.AVOID
    
    def _generate_rationale(
        self,
        signal: TradingSignal,
        recommendation: RecommendationType,
        risk_level: str,
        bias_warnings: List[str]
    ) -> str:
        """Generate rationale for recommendation"""
        rationale_parts = []
        
        # Signal strength
        rationale_parts.append(f"Signal strength: {signal.strength.value}")
        rationale_parts.append(f"Confidence: {signal.confidence:.0%}")
        
        # Risk/reward
        rationale_parts.append(f"Risk/reward ratio: {signal.risk_reward_ratio:.2f}")
        
        # Risk level
        rationale_parts.append(f"Risk level: {risk_level}")
        
        # Category
        rationale_parts.append(f"Trade category: {signal.category.value}")
        
        # Bias warnings
        if bias_warnings:
            rationale_parts.append(f"⚠ Bias warnings: {len(bias_warnings)}")
        
        # Recommendation
        if recommendation == RecommendationType.STRONG_BUY:
            rationale_parts.append("Strong buy recommendation - high confidence signal")
        elif recommendation == RecommendationType.BUY:
            rationale_parts.append("Buy recommendation - good signal with acceptable risk")
        elif recommendation == RecommendationType.HOLD:
            rationale_parts.append("Hold recommendation - wait for better entry or confirmation")
        elif recommendation == RecommendationType.AVOID:
            rationale_parts.append("Avoid recommendation - high risk or bias detected")
        
        return ". ".join(rationale_parts)
    
    def _calculate_confidence(
        self,
        signal: TradingSignal,
        risk_level: str,
        bias_warnings: List[str]
    ) -> float:
        """Calculate overall confidence in recommendation"""
        confidence = signal.confidence
        
        # Adjust for risk level
        if risk_level == "high":
            confidence *= 0.7
        elif risk_level == "medium":
            confidence *= 0.9
        
        # Adjust for bias warnings
        confidence *= (1.0 - len(bias_warnings) * 0.1)
        
        # Ensure within bounds
        return max(0.0, min(1.0, confidence))
    
    def _suggest_alternatives(
        self,
        signal: TradingSignal,
        current_portfolio: Optional[Dict[str, float]]
    ) -> List[str]:
        """Suggest alternative actions"""
        alternatives = []
        
        # If high risk, suggest waiting
        if signal.stop_loss_pct > 5.0:
            alternatives.append("Wait for better entry with tighter stop loss")
        
        # If low confidence, suggest smaller position
        if signal.confidence < 0.6:
            alternatives.append("Consider smaller position size")
        
        # If bias warnings, suggest review
        if signal.bias_flags:
            alternatives.append("Review bias warnings before trading")
        
        # Suggest diversification
        if current_portfolio:
            btc_allocation = self.btc_converter.get_btc_allocation(current_portfolio)
            if btc_allocation > 0.7:
                alternatives.append("Consider diversifying - BTC allocation high")
        
        return alternatives
    
    def get_decision_guidance(
        self,
        signals: List[TradingSignal],
        current_portfolio: Optional[Dict[str, float]] = None
    ) -> List[DecisionRecommendation]:
        """
        Get decision guidance for multiple signals
        
        Args:
            signals: List of trading signals
            current_portfolio: Current portfolio holdings
        
        Returns:
            List of decision recommendations (sorted by confidence)
        """
        recommendations = []
        
        for signal in signals:
            recommendation = self.analyze_signal(signal, current_portfolio)
            recommendations.append(recommendation)
        
        # Sort by confidence (highest first)
        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        
        return recommendations
    
    def print_recommendation(self, recommendation: DecisionRecommendation):
        """Print formatted recommendation"""
        print("\n" + "="*80)
        print("DECISION RECOMMENDATION")
        print("="*80)
        print(f"Recommendation: {recommendation.recommendation.value.upper()}")
        print(f"Confidence: {recommendation.confidence:.0%}")
        print(f"Risk Level: {recommendation.risk_level.upper()}")
        print(f"\nRationale: {recommendation.rationale}")
        
        if recommendation.signal:
            signal = recommendation.signal
            print(f"\nSignal Details:")
            print(f"  Symbol: {signal.symbol}")
            print(f"  Type: {signal.signal_type.value.upper()}")
            print(f"  Entry: ${signal.entry_price:.2f}")
            print(f"  TP: ${signal.take_profit:.2f} (+{signal.take_profit_pct:.2f}%)")
            print(f"  SL: ${signal.stop_loss:.2f} (-{signal.stop_loss_pct:.2f}%)")
            print(f"  R/R: {signal.risk_reward_ratio:.2f}")
        
        if recommendation.bias_warnings:
            print(f"\n⚠ Bias Warnings:")
            for warning in recommendation.bias_warnings:
                print(f"  - {warning}")
        
        if recommendation.alternatives:
            print(f"\nAlternatives:")
            for alt in recommendation.alternatives:
                print(f"  - {alt}")
        
        print("="*80)

