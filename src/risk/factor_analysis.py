"""
Factor Analysis with Statsmodels

Provides factor model analysis for portfolio performance including:
- Multi-factor regression (Fama-French style)
- Factor exposure analysis
- Factor attribution
- Factor risk decomposition
"""

import logging
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

try:
    import statsmodels.api as sm
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    sm = None

from loguru import logger


class FactorAnalyzer:
    """
    Analyze portfolio returns using factor models.
    
    Supports multi-factor regression to decompose portfolio returns
    into factor exposures and alpha.
    """
    
    def __init__(self, risk_free_rate: float = 0.0):
        """
        Initialize factor analyzer.
        
        Args:
            risk_free_rate: Risk-free rate for excess return calculation (default 0%)
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError(
                "statsmodels is not installed. Install it with: "
                "pip install statsmodels>=0.14.0"
            )
        
        self.risk_free_rate = risk_free_rate
        self.logger = logger
    
    def analyze_factor_exposure(
        self,
        portfolio_returns: pd.Series,
        factor_returns: pd.DataFrame,
        risk_free_rate: Optional[float] = None,
    ) -> Dict:
        """
        Analyze portfolio exposure to factors using multi-factor regression.
        
        Runs regression: portfolio_return = alpha + Σ(β_i * factor_i) + epsilon
        
        Args:
            portfolio_returns: Series of portfolio returns (daily)
            factor_returns: DataFrame with factor returns (columns = factors, index = dates)
            risk_free_rate: Optional risk-free rate (overrides instance default)
        
        Returns:
            Dictionary with factor exposure analysis results
        """
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        # Align data
        aligned = pd.DataFrame({
            "portfolio": portfolio_returns,
            **{col: factor_returns[col] for col in factor_returns.columns},
        }).dropna()
        
        if len(aligned) < 30:
            raise ValueError(
                f"Insufficient data: need at least 30 observations, got {len(aligned)}"
            )
        
        portfolio = aligned["portfolio"]
        factors = aligned.drop(columns=["portfolio"])
        
        # Calculate excess returns if risk-free rate provided
        if risk_free_rate > 0:
            portfolio_excess = portfolio - risk_free_rate / 252  # Daily
            factors_excess = factors.subtract(risk_free_rate / 252, axis=0)
        else:
            portfolio_excess = portfolio
            factors_excess = factors
        
        # Prepare regression
        X = sm.add_constant(factors_excess)  # Add intercept (alpha)
        y = portfolio_excess
        
        # Fit model
        model = sm.OLS(y, X).fit()
        
        # Extract results
        factor_exposures = {
            factor: {
                "beta": float(model.params[factor]),
                "pvalue": float(model.pvalues[factor]),
                "significant": model.pvalues[factor] < 0.05,
                "tstat": float(model.tvalues[factor]),
            }
            for factor in factors.columns
        }
        
        alpha = {
            "alpha": float(model.params["const"]),
            "alpha_annualized": float(model.params["const"] * 252 * 100),  # %
            "pvalue": float(model.pvalues["const"]),
            "significant": model.pvalues["const"] < 0.05,
            "tstat": float(model.tvalues["const"]),
        }
        
        results = {
            "alpha": alpha,
            "factor_exposures": factor_exposures,
            "model_fit": {
                "r_squared": float(model.rsquared),
                "adjusted_r_squared": float(model.rsquared_adj),
                "f_statistic": float(model.fvalue),
                "f_pvalue": float(model.f_pvalue),
                "aic": float(model.aic),
                "bic": float(model.bic),
            },
            "residuals": {
                "mean": float(model.resid.mean()),
                "std": float(model.resid.std()),
                "skewness": float(model.resid.skew()),
                "kurtosis": float(model.resid.kurtosis()),
            },
            "summary": str(model.summary()),
        }
        
        self.logger.info(
            f"Factor analysis: α={alpha['alpha_annualized']:.2f}%, "
            f"R²={results['model_fit']['r_squared']:.3f}, "
            f"factors={list(factors.columns)}"
        )
        
        return results
    
    def calculate_factor_attribution(
        self,
        portfolio_returns: pd.Series,
        factor_returns: pd.DataFrame,
        risk_free_rate: Optional[float] = None,
    ) -> pd.DataFrame:
        """
        Calculate factor attribution (contribution of each factor to returns).
        
        Args:
            portfolio_returns: Series of portfolio returns
            factor_returns: DataFrame with factor returns
            risk_free_rate: Optional risk-free rate
        
        Returns:
            DataFrame with factor attribution over time
        """
        # Get factor exposures
        analysis = self.analyze_factor_exposure(
            portfolio_returns=portfolio_returns,
            factor_returns=factor_returns,
            risk_free_rate=risk_free_rate,
        )
        
        # Align data
        aligned = pd.DataFrame({
            "portfolio": portfolio_returns,
            **{col: factor_returns[col] for col in factor_returns.columns},
        }).dropna()
        
        portfolio = aligned["portfolio"]
        factors = aligned.drop(columns=["portfolio"])
        
        # Calculate factor contributions
        attribution = pd.DataFrame(index=aligned.index)
        attribution["alpha"] = analysis["alpha"]["alpha"]
        
        for factor in factors.columns:
            beta = analysis["factor_exposures"][factor]["beta"]
            attribution[f"{factor}_contribution"] = factors[factor] * beta
        
        attribution["total_explained"] = attribution.sum(axis=1)
        attribution["residual"] = portfolio - attribution["total_explained"]
        
        return attribution
    
    def decompose_factor_risk(
        self,
        portfolio_returns: pd.Series,
        factor_returns: pd.DataFrame,
        factor_covariance: Optional[pd.DataFrame] = None,
        risk_free_rate: Optional[float] = None,
    ) -> Dict:
        """
        Decompose portfolio risk into factor contributions.
        
        Args:
            portfolio_returns: Series of portfolio returns
            factor_returns: DataFrame with factor returns
            factor_covariance: Optional factor covariance matrix (if None, estimated from data)
            risk_free_rate: Optional risk-free rate
        
        Returns:
            Dictionary with risk decomposition
        """
        # Get factor exposures
        analysis = self.analyze_factor_exposure(
            portfolio_returns=portfolio_returns,
            factor_returns=factor_returns,
            risk_free_rate=risk_free_rate,
        )
        
        # Calculate or use provided factor covariance
        if factor_covariance is None:
            aligned = pd.DataFrame({
                "portfolio": portfolio_returns,
                **{col: factor_returns[col] for col in factor_returns.columns},
            }).dropna()
            factors = aligned.drop(columns=["portfolio"])
            factor_covariance = factors.cov() * 252  # Annualized
        
        # Extract factor betas
        factor_betas = pd.Series({
            factor: analysis["factor_exposures"][factor]["beta"]
            for factor in factor_returns.columns
        })
        
        # Calculate portfolio variance from factors
        portfolio_variance = factor_betas @ factor_covariance @ factor_betas
        
        # Calculate factor risk contributions
        factor_risk_contributions = {}
        for factor in factor_returns.columns:
            # Marginal contribution of factor to portfolio variance
            marginal_contribution = (
                factor_betas[factor] * (factor_covariance.loc[factor] @ factor_betas)
            )
            factor_risk_contributions[factor] = {
                "marginal_contribution": float(marginal_contribution),
                "percentage": float(marginal_contribution / portfolio_variance * 100),
            }
        
        # Residual risk (unexplained by factors)
        portfolio_vol = portfolio_returns.std() * np.sqrt(252)  # Annualized
        factor_vol = np.sqrt(portfolio_variance)
        residual_vol = np.sqrt(max(0, portfolio_vol**2 - factor_vol**2))
        
        results = {
            "portfolio_volatility": float(portfolio_vol),
            "factor_volatility": float(factor_vol),
            "residual_volatility": float(residual_vol),
            "factor_explained_ratio": float((factor_vol / portfolio_vol) ** 2) if portfolio_vol > 0 else 0.0,
            "factor_risk_contributions": factor_risk_contributions,
            "factor_covariance_matrix": factor_covariance.to_dict(),
        }
        
        self.logger.info(
            f"Risk decomposition: Factor vol={factor_vol:.2%}, "
            f"Residual vol={residual_vol:.2%}, "
            f"Explained={(factor_vol/portfolio_vol)**2:.1%}"
        )
        
        return results


def analyze_portfolio_factors(
    portfolio_returns: pd.Series,
    factor_returns: pd.DataFrame,
    risk_free_rate: float = 0.0,
) -> Dict:
    """
    Convenience function to analyze portfolio factor exposure.
    
    Args:
        portfolio_returns: Series of portfolio returns
        factor_returns: DataFrame with factor returns
        risk_free_rate: Risk-free rate (default 0%)
    
    Returns:
        Dictionary with factor analysis results
    """
    analyzer = FactorAnalyzer(risk_free_rate=risk_free_rate)
    return analyzer.analyze_factor_exposure(
        portfolio_returns=portfolio_returns,
        factor_returns=factor_returns,
    )
