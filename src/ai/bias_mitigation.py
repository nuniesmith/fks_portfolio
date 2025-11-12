"""
AI Bias Mitigation
Advanced bias detection and mitigation using AI
"""
from typing import Dict, Any, Optional
from loguru import logger

from .client import AIServiceClient
from ..signals.trading_signal import TradingSignal
from ..risk.bias_detection import BiasDetector


class AIBiasMitigator:
    """Advanced bias mitigation using AI"""
    
    def __init__(self, ai_client: Optional[AIServiceClient] = None):
        """
        Initialize AI bias mitigator
        
        Args:
            ai_client: Optional AI service client
        """
        self.ai_client = ai_client or AIServiceClient()
        self.bias_detector = BiasDetector()
        self.logger = logger.bind(component="AIBiasMitigator")
    
    async def detect_and_mitigate(
        self,
        signal: TradingSignal
    ) -> Dict[str, Any]:
        """
        Detect bias using AI and provide mitigation
        
        Args:
            signal: Trading signal to analyze
        
        Returns:
            Bias detection and mitigation response
        """
        try:
            # Get AI bias analysis
            ai_bias = await self.ai_client.detect_bias(signal.to_dict())
            
            # Combine with rule-based detection
            rule_bias = self.bias_detector.detect_bias(signal)
            
            # Provide mitigation suggestions
            mitigation = self._suggest_mitigation(ai_bias, rule_bias)
            
            return {
                "bias_detected": ai_bias.get("bias_detected", False) or len(rule_bias) > 0,
                "bias_type": ai_bias.get("bias_type") or (rule_bias[0].bias_type if rule_bias else None),
                "ai_confidence": ai_bias.get("confidence", 0.0),
                "rule_based_flags": len(rule_bias),
                "mitigation": mitigation,
                "recommendation": self._generate_recommendation(ai_bias, rule_bias)
            }
            
        except Exception as e:
            self.logger.error(f"Error in bias detection: {e}")
            # Fallback to rule-based only
            rule_bias = self.bias_detector.detect_bias(signal)
            return {
                "bias_detected": len(rule_bias) > 0,
                "bias_type": rule_bias[0].bias_type if rule_bias else None,
                "ai_confidence": 0.0,
                "rule_based_flags": len(rule_bias),
                "mitigation": self._suggest_mitigation({}, rule_bias),
                "recommendation": "AI bias detection unavailable, using rule-based detection"
            }
    
    def _suggest_mitigation(
        self,
        ai_bias: Dict[str, Any],
        rule_bias: list
    ) -> Dict[str, Any]:
        """
        Suggest mitigation strategies
        
        Args:
            ai_bias: AI bias detection results
            rule_bias: Rule-based bias flags
        
        Returns:
            Mitigation suggestions
        """
        mitigations = []
        
        # AI-based mitigations
        if ai_bias.get("bias_detected"):
            bias_type = ai_bias.get("bias_type", "unknown")
            if bias_type == "overconfidence":
                mitigations.append({
                    "type": "reduce_position_size",
                    "suggestion": "Reduce position size by 25% due to overconfidence bias",
                    "severity": "high"
                })
            elif bias_type == "loss_aversion":
                mitigations.append({
                    "type": "review_stop_loss",
                    "suggestion": "Review stop loss placement - may be too tight due to loss aversion",
                    "severity": "medium"
                })
        
        # Rule-based mitigations
        for bias_flag in rule_bias:
            if bias_flag.severity == "high":
                mitigations.append({
                    "type": "filter_signal",
                    "suggestion": f"Filter signal due to {bias_flag.bias_type}: {bias_flag.message}",
                    "severity": "high"
                })
        
        return {
            "suggestions": mitigations,
            "action_required": len([m for m in mitigations if m["severity"] == "high"]) > 0
        }
    
    def _generate_recommendation(
        self,
        ai_bias: Dict[str, Any],
        rule_bias: list
    ) -> str:
        """
        Generate recommendation based on bias detection
        
        Args:
            ai_bias: AI bias results
            rule_bias: Rule-based bias flags
        
        Returns:
            Recommendation string
        """
        if ai_bias.get("bias_detected") and len(rule_bias) > 0:
            return "Both AI and rule-based detection found bias. Consider filtering this signal."
        elif ai_bias.get("bias_detected"):
            return f"AI detected {ai_bias.get('bias_type')} bias. Proceed with caution."
        elif len(rule_bias) > 0:
            return f"Rule-based detection found {len(rule_bias)} bias flags. Review before trading."
        else:
            return "No significant bias detected. Signal appears valid."

