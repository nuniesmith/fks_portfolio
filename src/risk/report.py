"""
Risk Report Generator
Generates comprehensive risk reports for portfolio
"""
from typing import Dict, Optional
import pandas as pd
import json
from loguru import logger

from .cvar import CVaRCalculator, calculate_max_drawdown, calculate_sharpe_ratio
from .bias_detection import BiasDetector, BiasType


class RiskReportGenerator:
    """Generate comprehensive risk reports"""
    
    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize risk report generator
        
        Args:
            confidence_level: Confidence level for CVaR (default 95%)
        """
        self.cvar_calc = CVaRCalculator(confidence_level=confidence_level)
        self.bias_detector = BiasDetector()
        self.logger = logger
    
    def generate_report(
        self,
        portfolio_returns: pd.Series,
        recent_losses: float = 0.0,
        recent_wins: int = 0,
        win_rate: float = 0.0,
        current_allocations: Optional[Dict[str, float]] = None,
        risk_free_rate: float = 0.02
    ) -> Dict:
        """
        Generate comprehensive risk report
        
        Args:
            portfolio_returns: Series of portfolio returns
            recent_losses: Recent loss percentage
            recent_wins: Number of recent wins
            win_rate: Overall win rate
            current_allocations: Current portfolio allocations
            risk_free_rate: Risk-free rate for Sharpe ratio
        
        Returns:
            Dictionary with risk metrics and recommendations
        """
        if portfolio_returns.empty:
            self.logger.warning("Empty returns series, generating minimal report")
            return self._generate_minimal_report()
        
        # Calculate CVaR
        cvar_95 = self.cvar_calc.calculate_portfolio_cvar(
            portfolio_returns,
            method="historical"
        )
        
        # Calculate other risk metrics
        max_dd = calculate_max_drawdown(portfolio_returns)
        sharpe = calculate_sharpe_ratio(portfolio_returns, risk_free_rate)
        
        # Calculate additional metrics
        volatility = portfolio_returns.std() * (252 ** 0.5)  # Annualized
        mean_return = portfolio_returns.mean() * 252  # Annualized
        
        # Detect biases
        biases = []
        if current_allocations:
            max_allocation = max(current_allocations.values()) if current_allocations else 0.0
            biases = self.bias_detector.detect_all_biases(
                recent_losses=recent_losses,
                recent_wins=recent_wins,
                win_rate=win_rate,
                current_allocation=max_allocation,
                recommended_allocation=0.20  # 20% max
            )
        
        # Get bias recommendation
        bias_recommendation = self.bias_detector.get_bias_recommendation(biases)
        
        # Overall recommendation
        overall_recommendation = self._get_overall_recommendation(
            cvar_95, max_dd, sharpe, bias_recommendation
        )
        
        report = {
            "risk_metrics": {
                "cvar_95": float(cvar_95),
                "max_drawdown": float(max_dd),
                "sharpe_ratio": float(sharpe),
                "volatility": float(volatility),
                "expected_return": float(mean_return),
            },
            "bias_flags": [
                {
                    "type": bias.bias_type.value,
                    "severity": bias.severity,
                    "message": bias.message,
                    "recommendation": bias.recommendation
                }
                for bias in biases
            ],
            "bias_recommendation": bias_recommendation,
            "overall_recommendation": overall_recommendation,
            "thresholds": {
                "cvar_95_threshold": -0.05,  # 5% max expected loss
                "max_drawdown_threshold": -0.10,  # 10% max drawdown
                "sharpe_minimum": 0.5
            }
        }
        
        return report
    
    def _get_overall_recommendation(
        self,
        cvar_95: float,
        max_dd: float,
        sharpe: float,
        bias_recommendation: str
    ) -> str:
        """Get overall portfolio recommendation"""
        # Check CVaR threshold
        if cvar_95 < -0.05:  # More than 5% expected loss
            return "REDUCE_RISK"
        
        # Check drawdown threshold
        if max_dd < -0.10:  # More than 10% drawdown
            return "REDUCE_RISK"
        
        # Check Sharpe ratio
        if sharpe < 0.5:
            return "IMPROVE_EFFICIENCY"
        
        # Check bias recommendation
        if bias_recommendation == "AVOID_TRADING":
            return "AVOID_TRADING"
        elif bias_recommendation == "REDUCE_POSITION_SIZE":
            return "CAUTION"
        
        return "HOLD"
    
    def _generate_minimal_report(self) -> Dict:
        """Generate minimal report when no data available"""
        return {
            "risk_metrics": {
                "cvar_95": None,
                "max_drawdown": None,
                "sharpe_ratio": None,
                "volatility": None,
                "expected_return": None,
            },
            "bias_flags": [],
            "bias_recommendation": "OK",
            "overall_recommendation": "INSUFFICIENT_DATA",
            "thresholds": {
                "cvar_95_threshold": -0.05,
                "max_drawdown_threshold": -0.10,
                "sharpe_minimum": 0.5
            }
        }
    
    def print_report(self, report: Dict):
        """Print formatted risk report"""
        print("\n" + "="*60)
        print("RISK REPORT")
        print("="*60)
        
        metrics = report["risk_metrics"]
        print("\nRisk Metrics:")
        print(f"  CVaR (95%):        {metrics['cvar_95']:.4f}" if metrics['cvar_95'] else "  CVaR (95%):        N/A")
        print(f"  Max Drawdown:      {metrics['max_drawdown']:.4f}" if metrics['max_drawdown'] else "  Max Drawdown:      N/A")
        print(f"  Sharpe Ratio:      {metrics['sharpe_ratio']:.2f}" if metrics['sharpe_ratio'] else "  Sharpe Ratio:      N/A")
        print(f"  Volatility:        {metrics['volatility']:.4f}" if metrics['volatility'] else "  Volatility:        N/A")
        print(f"  Expected Return:   {metrics['expected_return']:.4f}" if metrics['expected_return'] else "  Expected Return:   N/A")
        
        print("\nBias Flags:")
        if report["bias_flags"]:
            for flag in report["bias_flags"]:
                print(f"  [{flag['severity'].upper()}] {flag['type']}: {flag['message']}")
                print(f"    Recommendation: {flag['recommendation']}")
        else:
            print("  No biases detected")
        
        print(f"\nBias Recommendation: {report['bias_recommendation']}")
        print(f"Overall Recommendation: {report['overall_recommendation']}")
        print("="*60 + "\n")
    
    def save_report(self, report: Dict, filepath: str):
        """Save risk report to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        self.logger.info(f"Risk report saved to {filepath}")

