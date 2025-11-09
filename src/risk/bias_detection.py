"""
Bias Detection for Emotion-Free Trading
Detects emotional biases that could lead to poor decisions
"""
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
from loguru import logger


class BiasType(Enum):
    """Types of emotional biases"""
    RECENT_LOSS_AVERSION = "recent_loss_aversion"
    OVERCONFIDENCE = "overconfidence"
    ANCHORING = "anchoring"
    CONFIRMATION_BIAS = "confirmation_bias"
    HERD_BEHAVIOR = "herd_behavior"
    NONE = "none"


@dataclass
class BiasFlag:
    """Bias detection flag"""
    bias_type: BiasType
    severity: str  # "low", "medium", "high"
    message: str
    recommendation: str


class BiasDetector:
    """Detect emotional biases in trading decisions"""
    
    # Thresholds
    RECENT_LOSS_THRESHOLD = 0.02  # 2% loss triggers avoidance
    OVERCONFIDENCE_WIN_STREAK = 5  # 5+ wins in a row
    MAX_POSITION_SIZE = 0.20  # 20% max per position
    
    def __init__(self):
        self.logger = logger
    
    def check_recent_loss_aversion(
        self,
        recent_losses: float,
        current_signal: Optional[str] = None
    ) -> Optional[BiasFlag]:
        """
        Check for loss aversion bias (avoiding trading after losses)
        
        Args:
            recent_losses: Recent loss percentage (e.g., 0.02 for 2%)
            current_signal: Current trading signal (optional)
        
        Returns:
            BiasFlag if bias detected, None otherwise
        """
        if recent_losses > self.RECENT_LOSS_THRESHOLD:
            severity = "high" if recent_losses > 0.05 else "medium"
            return BiasFlag(
                bias_type=BiasType.RECENT_LOSS_AVERSION,
                severity=severity,
                message=f"Recent losses ({recent_losses*100:.2f}%) exceed threshold ({self.RECENT_LOSS_THRESHOLD*100:.2f}%)",
                recommendation="AVOID_TRADING - Wait for recovery or reduce position size"
            )
        return None
    
    def check_overconfidence(
        self,
        recent_wins: int,
        win_rate: float
    ) -> Optional[BiasFlag]:
        """
        Check for overconfidence bias (too many wins in a row)
        
        Args:
            recent_wins: Number of recent wins
            win_rate: Overall win rate
        
        Returns:
            BiasFlag if bias detected, None otherwise
        """
        if recent_wins >= self.OVERCONFIDENCE_WIN_STREAK:
            severity = "medium" if recent_wins < 8 else "high"
            return BiasFlag(
                bias_type=BiasType.OVERCONFIDENCE,
                severity=severity,
                message=f"Win streak of {recent_wins} may indicate overconfidence",
                recommendation="REDUCE_POSITION_SIZE - Maintain discipline despite wins"
            )
        return None
    
    def check_position_sizing(
        self,
        current_allocation: float,
        recommended_allocation: float
    ) -> Optional[BiasFlag]:
        """
        Check for position sizing bias (too large positions)
        
        Args:
            current_allocation: Current position allocation
            recommended_allocation: Recommended allocation
        
        Returns:
            BiasFlag if bias detected, None otherwise
        """
        if current_allocation > self.MAX_POSITION_SIZE:
            return BiasFlag(
                bias_type=BiasType.ANCHORING,
                severity="high",
                message=f"Position size ({current_allocation*100:.2f}%) exceeds maximum ({self.MAX_POSITION_SIZE*100:.2f}%)",
                recommendation="REDUCE_POSITION - Risk management violation"
            )
        
        if current_allocation > recommended_allocation * 1.5:
            return BiasFlag(
                bias_type=BiasType.OVERCONFIDENCE,
                severity="medium",
                message=f"Position size ({current_allocation*100:.2f}%) significantly exceeds recommendation ({recommended_allocation*100:.2f}%)",
                recommendation="REDUCE_POSITION - Consider recommended allocation"
            )
        
        return None
    
    def detect_all_biases(
        self,
        recent_losses: float = 0.0,
        recent_wins: int = 0,
        win_rate: float = 0.0,
        current_allocation: float = 0.0,
        recommended_allocation: float = 0.0,
        current_signal: Optional[str] = None
    ) -> List[BiasFlag]:
        """
        Run all bias detection checks
        
        Returns:
            List of detected bias flags
        """
        biases = []
        
        # Check loss aversion
        loss_bias = self.check_recent_loss_aversion(recent_losses, current_signal)
        if loss_bias:
            biases.append(loss_bias)
        
        # Check overconfidence
        overconfidence_bias = self.check_overconfidence(recent_wins, win_rate)
        if overconfidence_bias:
            biases.append(overconfidence_bias)
        
        # Check position sizing
        position_bias = self.check_position_sizing(current_allocation, recommended_allocation)
        if position_bias:
            biases.append(position_bias)
        
        return biases
    
    def get_bias_recommendation(self, biases: List[BiasFlag]) -> str:
        """
        Get overall recommendation based on detected biases
        
        Args:
            biases: List of detected bias flags
        
        Returns:
            Overall recommendation
        """
        if not biases:
            return "OK"
        
        # Check for high severity biases
        high_severity = [b for b in biases if b.severity == "high"]
        if high_severity:
            return "AVOID_TRADING"
        
        # Check for medium severity biases
        medium_severity = [b for b in biases if b.severity == "medium"]
        if medium_severity:
            return "REDUCE_POSITION_SIZE"
        
        return "CAUTION"

