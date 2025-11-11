"""
Tests for Risk Management components
"""
import pytest
import pandas as pd
import numpy as np
from src.risk.cvar import CVaRCalculator, calculate_max_drawdown, calculate_sharpe_ratio
from src.risk.bias_detection import BiasDetector, BiasType, BiasFlag
from src.risk.report import RiskReportGenerator


class TestCVaR:
    """Test CVaR calculations"""
    
    def test_historical_cvar(self):
        """Test historical CVaR calculation"""
        # Create sample returns
        returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.02, -0.03, 0.01, -0.015])
        
        calc = CVaRCalculator(confidence_level=0.95)
        cvar = calc.calculate_historical_cvar(returns)
        
        assert cvar < 0  # CVaR should be negative (loss)
        assert isinstance(cvar, float)
    
    def test_parametric_cvar(self):
        """Test parametric CVaR calculation"""
        returns = pd.Series(np.random.normal(0.001, 0.02, 100))
        
        calc = CVaRCalculator(confidence_level=0.95)
        cvar = calc.calculate_parametric_cvar(returns)
        
        assert isinstance(cvar, float)
    
    def test_monte_carlo_cvar(self):
        """Test Monte Carlo CVaR calculation"""
        returns = pd.Series(np.random.normal(0.001, 0.02, 100))
        
        calc = CVaRCalculator(confidence_level=0.95)
        cvar = calc.calculate_monte_carlo_cvar(returns, n_simulations=1000)
        
        assert isinstance(cvar, float)
    
    def test_cvar_empty_returns(self):
        """Test CVaR with empty returns"""
        returns = pd.Series([])
        calc = CVaRCalculator()
        
        with pytest.raises(ValueError):
            calc.calculate_historical_cvar(returns)
    
    def test_max_drawdown(self):
        """Test max drawdown calculation"""
        returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.02, -0.03, 0.01])
        max_dd = calculate_max_drawdown(returns)
        
        assert max_dd <= 0  # Drawdown should be negative or zero
        assert isinstance(max_dd, float)
    
    def test_sharpe_ratio(self):
        """Test Sharpe ratio calculation"""
        returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.01])
        sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.02)
        
        assert isinstance(sharpe, float)


class TestBiasDetection:
    """Test bias detection"""
    
    def test_loss_aversion_detection(self):
        """Test loss aversion bias detection"""
        detector = BiasDetector()
        
        # No bias
        bias = detector.check_recent_loss_aversion(0.01, "BUY")
        assert bias is None
        
        # Bias detected
        bias = detector.check_recent_loss_aversion(0.03, "BUY")
        assert bias is not None
        assert bias.bias_type == BiasType.RECENT_LOSS_AVERSION
        assert bias.severity in ["medium", "high"]
        assert "AVOID_TRADING" in bias.recommendation
    
    def test_overconfidence_detection(self):
        """Test overconfidence bias detection"""
        detector = BiasDetector()
        
        # No bias
        bias = detector.check_overconfidence(3, 0.6)
        assert bias is None
        
        # Bias detected
        bias = detector.check_overconfidence(6, 0.7)
        assert bias is not None
        assert bias.bias_type == BiasType.OVERCONFIDENCE
    
    def test_position_sizing_detection(self):
        """Test position sizing bias detection"""
        detector = BiasDetector()
        
        # No bias
        bias = detector.check_position_sizing(0.15, 0.15)
        assert bias is None
        
        # Too large position
        bias = detector.check_position_sizing(0.25, 0.20)
        assert bias is not None
        assert bias.severity == "high"
    
    def test_detect_all_biases(self):
        """Test detecting all biases"""
        detector = BiasDetector()
        
        biases = detector.detect_all_biases(
            recent_losses=0.03,
            recent_wins=6,
            win_rate=0.7,
            current_allocation=0.25,
            recommended_allocation=0.15
        )
        
        assert len(biases) >= 2  # Should detect multiple biases
    
    def test_bias_recommendation(self):
        """Test bias recommendation logic"""
        detector = BiasDetector()
        
        # No biases
        biases = []
        rec = detector.get_bias_recommendation(biases)
        assert rec == "OK"
        
        # High severity bias
        high_bias = BiasFlag(
            bias_type=BiasType.RECENT_LOSS_AVERSION,
            severity="high",
            message="Test",
            recommendation="AVOID_TRADING"
        )
        rec = detector.get_bias_recommendation([high_bias])
        assert rec == "AVOID_TRADING"


class TestRiskReport:
    """Test risk report generation"""
    
    def test_generate_report(self):
        """Test risk report generation"""
        returns = pd.Series(np.random.normal(0.001, 0.02, 100))
        
        generator = RiskReportGenerator()
        report = generator.generate_report(returns)
        
        assert "risk_metrics" in report
        assert "bias_flags" in report
        assert "overall_recommendation" in report
        assert report["risk_metrics"]["cvar_95"] is not None
    
    def test_generate_minimal_report(self):
        """Test minimal report for empty data"""
        returns = pd.Series([])
        
        generator = RiskReportGenerator()
        report = generator.generate_report(returns)
        
        assert report["overall_recommendation"] == "INSUFFICIENT_DATA"
        assert report["risk_metrics"]["cvar_95"] is None

