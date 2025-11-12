"""
Conditional Value at Risk (CVaR) Calculation
Measures expected loss beyond VaR threshold
"""
from typing import Optional
import numpy as np
import pandas as pd
from scipy import stats
from loguru import logger


class CVaRCalculator:
    """Calculate CVaR (Expected Shortfall) for portfolio risk management"""
    
    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize CVaR calculator
        
        Args:
            confidence_level: Confidence level (e.g., 0.95 for 95%)
        """
        if not 0 < confidence_level < 1:
            raise ValueError(f"Confidence level must be between 0 and 1, got {confidence_level}")
        
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level  # Tail probability
        self.logger = logger
    
    def calculate_historical_cvar(self, returns: pd.Series) -> float:
        """
        Calculate CVaR using historical method
        
        Args:
            returns: Series of portfolio returns
        
        Returns:
            CVaR value (negative number representing expected loss)
        """
        if returns.empty:
            raise ValueError("Returns series is empty")
        
        # Calculate VaR (Value at Risk)
        var = np.percentile(returns, self.alpha * 100)
        
        # CVaR is the mean of returns below VaR threshold
        tail_returns = returns[returns <= var]
        
        if len(tail_returns) == 0:
            self.logger.warning("No returns below VaR threshold, using VaR as CVaR")
            return var
        
        cvar = tail_returns.mean()
        
        self.logger.info(
            f"CVaR ({self.confidence_level*100:.0f}%): {cvar:.4f} "
            f"(VaR: {var:.4f}, Tail observations: {len(tail_returns)})"
        )
        
        return float(cvar)
    
    def calculate_parametric_cvar(self, returns: pd.Series) -> float:
        """
        Calculate CVaR using parametric method (assumes normal distribution)
        
        Args:
            returns: Series of portfolio returns
        
        Returns:
            CVaR value
        """
        if returns.empty:
            raise ValueError("Returns series is empty")
        
        mean = returns.mean()
        std = returns.std()
        
        # VaR for normal distribution
        z_score = stats.norm.ppf(self.alpha)
        var = mean + z_score * std
        
        # CVaR for normal distribution
        # CVaR = mean - std * (phi(z_alpha) / alpha)
        # where phi is standard normal PDF
        phi_z = stats.norm.pdf(z_score)
        cvar = mean - std * (phi_z / self.alpha)
        
        self.logger.info(
            f"Parametric CVaR ({self.confidence_level*100:.0f}%): {cvar:.4f} "
            f"(VaR: {var:.4f}, Mean: {mean:.4f}, Std: {std:.4f})"
        )
        
        return float(cvar)
    
    def calculate_monte_carlo_cvar(
        self,
        returns: pd.Series,
        n_simulations: int = 10000
    ) -> float:
        """
        Calculate CVaR using Monte Carlo simulation
        
        Args:
            returns: Series of historical returns
            n_simulations: Number of Monte Carlo simulations
        
        Returns:
            CVaR value
        """
        if returns.empty:
            raise ValueError("Returns series is empty")
        
        # Fit distribution parameters
        mean = returns.mean()
        std = returns.std()
        
        # Generate random returns
        np.random.seed(42)  # For reproducibility
        simulated_returns = np.random.normal(mean, std, n_simulations)
        
        # Calculate VaR
        var = np.percentile(simulated_returns, self.alpha * 100)
        
        # CVaR is mean of returns below VaR
        tail_returns = simulated_returns[simulated_returns <= var]
        cvar = tail_returns.mean()
        
        self.logger.info(
            f"Monte Carlo CVaR ({self.confidence_level*100:.0f}%): {cvar:.4f} "
            f"(VaR: {var:.4f}, Simulations: {n_simulations})"
        )
        
        return float(cvar)
    
    def calculate_portfolio_cvar(
        self,
        portfolio_returns: pd.Series,
        method: str = "historical"
    ) -> float:
        """
        Calculate CVaR for portfolio returns
        
        Args:
            portfolio_returns: Series of portfolio returns
            method: Calculation method ("historical", "parametric", "monte_carlo")
        
        Returns:
            CVaR value
        """
        if method == "historical":
            return self.calculate_historical_cvar(portfolio_returns)
        elif method == "parametric":
            return self.calculate_parametric_cvar(portfolio_returns)
        elif method == "monte_carlo":
            return self.calculate_monte_carlo_cvar(portfolio_returns)
        else:
            raise ValueError(f"Unknown method: {method}. Use 'historical', 'parametric', or 'monte_carlo'")


def calculate_max_drawdown(returns: pd.Series) -> float:
    """
    Calculate maximum drawdown from returns
    
    Args:
        returns: Series of returns
    
    Returns:
        Maximum drawdown (negative number)
    """
    if returns.empty:
        return 0.0
    
    # Calculate cumulative returns
    cumulative = (1 + returns).cumprod()
    
    # Calculate running maximum
    running_max = cumulative.expanding().max()
    
    # Calculate drawdown
    drawdown = (cumulative - running_max) / running_max
    
    max_drawdown = drawdown.min()
    
    return float(max_drawdown)


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio
    
    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate
    
    Returns:
        Sharpe ratio
    """
    if returns.empty or returns.std() == 0:
        return 0.0
    
    # Annualize returns and risk-free rate
    # Assuming daily returns
    annualized_return = returns.mean() * 252
    annualized_std = returns.std() * np.sqrt(252)
    annualized_rf = risk_free_rate
    
    sharpe = (annualized_return - annualized_rf) / annualized_std
    
    return float(sharpe)

