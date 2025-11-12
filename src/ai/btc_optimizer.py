"""
BTC AI Optimizer
AI-powered BTC allocation optimization
"""
from typing import Dict, Any, Optional
from loguru import logger

from .client import AIServiceClient
from ..portfolio.portfolio import Portfolio


class BTCAIOptimizer:
    """AI-powered BTC allocation optimizer"""
    
    def __init__(self, ai_client: Optional[AIServiceClient] = None):
        """
        Initialize BTC AI optimizer
        
        Args:
            ai_client: Optional AI service client
        """
        self.ai_client = ai_client or AIServiceClient()
        self.logger = logger.bind(component="BTCAIOptimizer")
    
    async def optimize_btc_allocation(
        self,
        portfolio: Portfolio,
        market_state: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Optimize BTC allocation using AI
        
        Args:
            portfolio: Current portfolio
            market_state: Optional market state data
        
        Returns:
            Optimal BTC allocation (0.0 to 1.0)
        """
        try:
            # Get BTC analysis from AI
            btc_analysis = await self.ai_client.analyze_symbol(
                "BTC",
                market_state or {}
            )
            
            # Extract AI confidence and decision
            ai_confidence = btc_analysis.get("confidence", 0.5)
            final_decision = btc_analysis.get("final_decision", "HOLD")
            
            # Determine optimal allocation based on AI
            if final_decision == "BUY" and ai_confidence > 0.7:
                # Strong bullish - increase BTC allocation
                target_btc = 0.60
                self.logger.info(f"AI strongly bullish on BTC - target allocation: {target_btc:.0%}")
            elif final_decision == "BUY" and ai_confidence > 0.5:
                # Moderate bullish - maintain upper range
                target_btc = 0.55
                self.logger.info(f"AI moderately bullish on BTC - target allocation: {target_btc:.0%}")
            elif final_decision == "SELL" and ai_confidence > 0.7:
                # Strong bearish - maintain minimum
                target_btc = 0.50
                self.logger.info(f"AI bearish on BTC - maintaining minimum allocation: {target_btc:.0%}")
            else:
                # Neutral or uncertain - maintain current or default
                current_btc = self._get_current_btc_allocation(portfolio)
                target_btc = max(0.50, min(0.60, current_btc))
                self.logger.info(f"AI neutral on BTC - maintaining allocation: {target_btc:.0%}")
            
            # Ensure within constraints (50-60%)
            target_btc = max(0.50, min(0.60, target_btc))
            
            return target_btc
            
        except Exception as e:
            self.logger.error(f"Error optimizing BTC allocation: {e}")
            # Fallback to default allocation
            return 0.55
    
    def _get_current_btc_allocation(self, portfolio: Portfolio) -> float:
        """
        Get current BTC allocation from portfolio
        
        Args:
            portfolio: Portfolio instance
        
        Returns:
            Current BTC allocation (0.0 to 1.0)
        """
        try:
            # Get portfolio weights
            weights = portfolio.get_weights()
            btc_weight = weights.get("BTC", 0.0)
            return btc_weight
        except Exception as e:
            self.logger.warning(f"Error getting current BTC allocation: {e}")
            return 0.55
    
    async def get_btc_rebalancing_recommendation(
        self,
        portfolio: Portfolio,
        market_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get BTC rebalancing recommendation
        
        Args:
            portfolio: Current portfolio
            market_state: Optional market state
        
        Returns:
            Rebalancing recommendation
        """
        try:
            current_btc = self._get_current_btc_allocation(portfolio)
            target_btc = await self.optimize_btc_allocation(portfolio, market_state)
            
            difference = target_btc - current_btc
            
            if abs(difference) < 0.01:  # Less than 1% difference
                return {
                    "action": "HOLD",
                    "current_allocation": current_btc,
                    "target_allocation": target_btc,
                    "difference": difference,
                    "rationale": "Current allocation is optimal"
                }
            elif difference > 0:
                return {
                    "action": "INCREASE_BTC",
                    "current_allocation": current_btc,
                    "target_allocation": target_btc,
                    "difference": difference,
                    "rationale": f"Increase BTC allocation by {difference:.1%} based on AI analysis"
                }
            else:
                return {
                    "action": "DECREASE_BTC",
                    "current_allocation": current_btc,
                    "target_allocation": target_btc,
                    "difference": abs(difference),
                    "rationale": f"Decrease BTC allocation by {abs(difference):.1%} based on AI analysis"
                }
                
        except Exception as e:
            self.logger.error(f"Error getting rebalancing recommendation: {e}")
            return {
                "action": "ERROR",
                "rationale": f"Error generating recommendation: {e}"
            }

