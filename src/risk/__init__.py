"""
Risk Analysis and Reporting Module

Provides comprehensive risk analysis including:
- Risk reports and metrics
- CVaR calculations
- Bias detection
- Factor analysis (Statsmodels integration)
"""
from .cvar import CVaRCalculator, calculate_max_drawdown, calculate_sharpe_ratio
from .bias_detection import BiasDetector, BiasType, BiasFlag
from .report import RiskReportGenerator

# Optional factor analysis support
try:
    from .factor_analysis import (
        FactorAnalyzer,
        analyze_portfolio_factors,
    )
    FACTOR_ANALYSIS_AVAILABLE = True
except ImportError:
    FACTOR_ANALYSIS_AVAILABLE = False

__all__ = [
    "CVaRCalculator",
    "calculate_max_drawdown",
    "calculate_sharpe_ratio",
    "BiasDetector",
    "BiasType",
    "BiasFlag",
    "RiskReportGenerator",
]

if FACTOR_ANALYSIS_AVAILABLE:
    __all__.extend([
        "FactorAnalyzer",
        "analyze_portfolio_factors",
    ])

