"""
Portfolio Optimization Constraints
Defines constraints for mean-variance optimization
"""
from typing import List, Dict, Optional
from pypfopt import EfficientFrontier
from pypfopt import risk_models, expected_returns
import pandas as pd
from loguru import logger


class PortfolioConstraints:
    """Portfolio optimization constraints"""
    
    # BTC constraints
    BTC_MIN_WEIGHT = 0.50  # 50% minimum
    BTC_MAX_WEIGHT = 0.60  # 60% maximum
    
    # Individual asset constraints
    MAX_INDIVIDUAL_WEIGHT = 0.20  # 20% maximum per asset
    
    def __init__(self):
        self.logger = logger
    
    def get_btc_constraints(self, symbols: List[str]) -> Dict:
        """Get BTC weight constraints"""
        if "BTC" not in symbols:
            raise ValueError("BTC must be in symbols list")
        
        btc_index = symbols.index("BTC")
        
        return {
            "type": "eq",  # Equality constraint
            "fun": lambda w: w[btc_index] - self.BTC_MIN_WEIGHT,  # BTC >= 50%
        }
    
    def get_weight_bounds(self, symbols: List[str]) -> List[tuple]:
        """Get weight bounds for each asset"""
        bounds = []
        for symbol in symbols:
            if symbol == "BTC":
                bounds.append((self.BTC_MIN_WEIGHT, self.BTC_MAX_WEIGHT))
            else:
                bounds.append((0.0, self.MAX_INDIVIDUAL_WEIGHT))
        return bounds
    
    def validate_weights(self, weights: Dict[str, float]) -> tuple[bool, Optional[str]]:
        """Validate optimized weights meet constraints"""
        # Check total sums to 1
        total = sum(weights.values())
        if abs(total - 1.0) > 0.001:
            return False, f"Weights sum to {total:.4f}, expected 1.0"
        
        # Check BTC constraints
        btc_weight = weights.get("BTC", 0.0)
        if btc_weight < self.BTC_MIN_WEIGHT:
            return False, f"BTC weight {btc_weight:.4f} below minimum {self.BTC_MIN_WEIGHT}"
        if btc_weight > self.BTC_MAX_WEIGHT:
            return False, f"BTC weight {btc_weight:.4f} above maximum {self.BTC_MAX_WEIGHT}"
        
        # Check individual asset constraints
        for symbol, weight in weights.items():
            if symbol != "BTC" and weight > self.MAX_INDIVIDUAL_WEIGHT:
                return False, f"{symbol} weight {weight:.4f} exceeds maximum {self.MAX_INDIVIDUAL_WEIGHT}"
        
        return True, None

