"""
AI Signal Refiner
Refines trading signals using AI analysis
"""
from typing import Dict, Any, Optional
from loguru import logger

from .client import AIServiceClient
from ..signals.trading_signal import TradingSignal, SignalStrength, SignalType
from ..signals.trade_categories import TradeCategory


class AISignalRefiner:
    """Refines signals using AI analysis"""
    
    def __init__(self, ai_client: Optional[AIServiceClient] = None):
        """
        Initialize AI signal refiner
        
        Args:
            ai_client: Optional AI service client (creates new if not provided)
        """
        self.ai_client = ai_client or AIServiceClient()
        self.logger = logger.bind(component="AISignalRefiner")
    
    async def refine_signal(
        self,
        signal: TradingSignal,
        market_data: Optional[Dict[str, Any]] = None
    ) -> TradingSignal:
        """
        Refine signal using AI analysis
        
        Args:
            signal: Baseline trading signal
            market_data: Optional market data
        
        Returns:
            Refined signal with AI enhancements
        """
        try:
            # Get AI analysis
            analysis = await self.ai_client.analyze_symbol(
                signal.symbol,
                market_data or {}
            )
            
            # Get debate perspectives
            debate = await self.ai_client.debate_signal(signal.to_dict())
            
            # Apply AI insights to refine signal
            refined_signal = self._apply_ai_insights(signal, analysis, debate)
            
            self.logger.info(
                f"Refined signal for {signal.symbol}: "
                f"confidence {signal.confidence:.2f} -> {refined_signal.confidence:.2f}"
            )
            
            return refined_signal
            
        except Exception as e:
            self.logger.error(f"Error refining signal: {e}")
            # Return original signal if AI fails
            return signal
    
    def _apply_ai_insights(
        self,
        signal: TradingSignal,
        analysis: Dict[str, Any],
        debate: Dict[str, Any]
    ) -> TradingSignal:
        """
        Apply AI insights to refine signal
        
        Args:
            signal: Original signal
            analysis: AI analysis response
            debate: Debate response
        
        Returns:
            Refined signal
        """
        # Extract AI confidence
        ai_confidence = analysis.get("confidence", signal.confidence)
        
        # Extract debate consensus (handle different response formats)
        debate_output = debate.get("debate_output", {})
        bull_consensus = debate_output.get("bull", debate.get("bull_consensus", 0.5))
        bear_consensus = debate_output.get("bear", debate.get("bear_consensus", 0.5))
        
        # Normalize consensus values (they might be strings or numbers)
        if isinstance(bull_consensus, str):
            # Try to extract numeric value from string
            try:
                bull_consensus = float(bull_consensus.split(":")[-1].strip()) if ":" in bull_consensus else 0.5
            except:
                bull_consensus = 0.5
        
        if isinstance(bear_consensus, str):
            try:
                bear_consensus = float(bear_consensus.split(":")[-1].strip()) if ":" in bear_consensus else 0.5
            except:
                bear_consensus = 0.5
        
        # Ensure values are between 0 and 1
        bull_consensus = max(0.0, min(1.0, float(bull_consensus)))
        bear_consensus = max(0.0, min(1.0, float(bear_consensus)))
        
        # Calculate consensus strength
        consensus_strength = abs(bull_consensus - bear_consensus)
        
        # Adjust confidence based on AI and consensus
        if consensus_strength > 0.3:
            # Strong consensus - boost confidence
            adjusted_confidence = min(1.0, signal.confidence * 1.1)
        elif consensus_strength < 0.1:
            # Weak consensus - reduce confidence
            adjusted_confidence = max(0.0, signal.confidence * 0.9)
        else:
            adjusted_confidence = signal.confidence
        
        # Blend with AI confidence
        final_confidence = (adjusted_confidence * 0.6) + (ai_confidence * 0.4)
        
        # Adjust signal strength based on AI
        if final_confidence >= 0.8:
            strength = SignalStrength.VERY_STRONG
        elif final_confidence >= 0.65:
            strength = SignalStrength.STRONG
        elif final_confidence >= 0.5:
            strength = SignalStrength.MODERATE
        else:
            strength = SignalStrength.WEAK
        
        # Extract summaries
        analysis_summary = analysis.get("summary", analysis.get("final_decision", ""))
        debate_summary = debate.get("summary", debate.get("debate_summary", ""))
        
        # Create refined signal
        refined_signal = TradingSignal(
            symbol=signal.symbol,
            signal_type=signal.signal_type,
            category=signal.category,
            entry_price=signal.entry_price,
            take_profit=signal.take_profit,
            stop_loss=signal.stop_loss,
            take_profit_pct=signal.take_profit_pct,
            stop_loss_pct=signal.stop_loss_pct,
            risk_reward_ratio=signal.risk_reward_ratio,
            position_size_pct=signal.position_size_pct,
            timestamp=signal.timestamp,
            strength=strength,
            confidence=final_confidence,
            bias_flags=signal.bias_flags,
            ai_enhancements={
                "ai_confidence": ai_confidence,
                "bull_consensus": bull_consensus,
                "bear_consensus": bear_consensus,
                "consensus_strength": consensus_strength,
                "analysis_summary": analysis_summary,
                "debate_summary": debate_summary,
                "final_decision": analysis.get("final_decision", "HOLD")
            }
        )
        
        return refined_signal
    
    async def refine_signals(
        self,
        signals: list[TradingSignal],
        market_data: Optional[Dict[str, Any]] = None
    ) -> list[TradingSignal]:
        """
        Refine multiple signals
        
        Args:
            signals: List of baseline signals
            market_data: Optional market data
        
        Returns:
            List of refined signals
        """
        refined = []
        for signal in signals:
            try:
                refined_signal = await self.refine_signal(signal, market_data)
                refined.append(refined_signal)
            except Exception as e:
                self.logger.error(f"Error refining signal {signal.symbol}: {e}")
                # Include original signal if refinement fails
                refined.append(signal)
        
        return refined

