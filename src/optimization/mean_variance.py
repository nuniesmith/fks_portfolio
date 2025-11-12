"""
Mean-Variance Portfolio Optimization
Uses PyPortfolioOpt for efficient frontier optimization
"""
from typing import Dict, Optional, List
import pandas as pd
import numpy as np
from pypfopt import EfficientFrontier, risk_models, expected_returns
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
from loguru import logger
from .constraints import PortfolioConstraints


class MeanVarianceOptimizer:
    """Mean-variance portfolio optimizer with BTC constraints"""
    
    def __init__(self):
        self.logger = logger
        self.constraints = PortfolioConstraints()
    
    def optimize(
        self,
        historical_returns: pd.DataFrame,
        method: str = "max_sharpe",
        risk_free_rate: float = 0.02
    ) -> Dict:
        """
        Optimize portfolio allocation
        
        Args:
            historical_returns: DataFrame with historical returns (columns = symbols, index = dates)
            method: Optimization method ("max_sharpe", "min_volatility", "efficient_risk", "efficient_return")
            risk_free_rate: Risk-free rate for Sharpe ratio calculation
        
        Returns:
            Dictionary with optimized weights and metrics
        """
        if historical_returns.empty:
            raise ValueError("Historical returns DataFrame is empty")
        
        if "BTC" not in historical_returns.columns:
            raise ValueError("BTC must be in historical returns")
        
        symbols = list(historical_returns.columns)
        
        # Calculate expected returns and covariance matrix
        mu = expected_returns.mean_historical_return(historical_returns)
        S = risk_models.sample_cov(historical_returns)
        
        # Get bounds for all assets
        bounds = self.constraints.get_weight_bounds(symbols)
        
        # Create efficient frontier with bounds
        ef = EfficientFrontier(mu, S, weight_bounds=bounds)
        
        # Note: Bounds enforce 50-60% for BTC and 0-20% for other assets
        
        # Optimize based on method
        if method == "max_sharpe":
            weights = ef.max_sharpe(risk_free_rate=risk_free_rate)
        elif method == "min_volatility":
            weights = ef.min_volatility()
        elif method == "efficient_risk":
            # Target volatility (e.g., 20%)
            weights = ef.efficient_risk(target_volatility=0.20)
        elif method == "efficient_return":
            # Target return (e.g., 15%)
            weights = ef.efficient_return(target_return=0.15)
        else:
            raise ValueError(f"Unknown optimization method: {method}")
        
        # Clean weights (remove near-zero allocations)
        cleaned_weights = ef.clean_weights()
        
        # Convert to dictionary - clean_weights() returns a dict already
        if isinstance(cleaned_weights, dict):
            weights_dict = cleaned_weights
        else:
            # Fallback: if it's an array/list, convert to dict
            weights_dict = {symbol: cleaned_weights[i] for i, symbol in enumerate(symbols)}
        
        # Calculate portfolio metrics
        performance = ef.portfolio_performance(verbose=False, risk_free_rate=risk_free_rate)
        
        # Validate constraints
        valid, error = self.constraints.validate_weights(weights_dict)
        if not valid:
            self.logger.warning(f"Optimized weights don't meet constraints: {error}")
        
        result = {
            "weights": weights_dict,
            "expected_return": performance[0],
            "volatility": performance[1],
            "sharpe_ratio": performance[2],
            "method": method,
            "constraints_met": valid,
            "constraints_error": error
        }
        
        self.logger.info(f"Optimization complete: Sharpe={performance[2]:.2f}, Return={performance[0]:.2%}, Vol={performance[1]:.2%}")
        
        return result
    
    def calculate_expected_returns(self, historical_returns: pd.DataFrame) -> pd.Series:
        """Calculate expected returns from historical data"""
        return expected_returns.mean_historical_return(historical_returns)
    
    def calculate_covariance(self, historical_returns: pd.DataFrame) -> pd.DataFrame:
        """Calculate covariance matrix from historical returns"""
        return risk_models.sample_cov(historical_returns)

