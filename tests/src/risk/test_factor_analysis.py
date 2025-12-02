"""
Tests for Factor Analysis Module

Tests multi-factor regression and risk decomposition for portfolios.
"""

import pytest
import pandas as pd
import numpy as np

try:
    from src.risk.factor_analysis import (
        FactorAnalyzer,
        analyze_portfolio_factors,
    )
    FACTOR_ANALYSIS_AVAILABLE = True
except ImportError:
    FACTOR_ANALYSIS_AVAILABLE = False


@pytest.mark.skipif(not FACTOR_ANALYSIS_AVAILABLE, reason="Factor analysis not available")
class TestFactorAnalyzer:
    """Tests for FactorAnalyzer class"""

    @pytest.fixture
    def sample_portfolio_returns(self):
        """Create sample portfolio returns"""
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        returns = pd.Series(
            np.random.normal(0.001, 0.02, 100),
            index=dates,
        )
        return returns

    @pytest.fixture
    def sample_factor_returns(self):
        """Create sample factor returns"""
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        factors = pd.DataFrame({
            "market": np.random.normal(0.0008, 0.018, 100),
            "size": np.random.normal(0.0002, 0.01, 100),
            "value": np.random.normal(0.0001, 0.01, 100),
        }, index=dates)
        return factors

    @pytest.fixture
    def analyzer(self):
        """Create FactorAnalyzer instance"""
        return FactorAnalyzer(risk_free_rate=0.02)

    def test_analyzer_creation(self):
        """Test FactorAnalyzer can be created"""
        analyzer = FactorAnalyzer(risk_free_rate=0.02)
        assert analyzer is not None
        assert analyzer.risk_free_rate == 0.02

    def test_analyze_factor_exposure(self, analyzer, sample_portfolio_returns, sample_factor_returns):
        """Test factor exposure analysis"""
        results = analyzer.analyze_factor_exposure(
            portfolio_returns=sample_portfolio_returns,
            factor_returns=sample_factor_returns,
        )
        
        assert isinstance(results, dict)
        assert "alpha" in results
        assert "factor_exposures" in results
        assert "model_fit" in results
        assert "residuals" in results
        
        # Check alpha
        assert "alpha" in results["alpha"]
        assert "alpha_annualized" in results["alpha"]
        assert "pvalue" in results["alpha"]
        assert "significant" in results["alpha"]
        
        # Check factor exposures
        assert "market" in results["factor_exposures"]
        assert "size" in results["factor_exposures"]
        assert "value" in results["factor_exposures"]
        
        # Check model fit
        assert "r_squared" in results["model_fit"]
        assert 0 <= results["model_fit"]["r_squared"] <= 1

    def test_analyze_factor_exposure_insufficient_data(self, analyzer):
        """Test with insufficient data"""
        dates = pd.date_range(start="2024-01-01", periods=10, freq="D")
        portfolio_returns = pd.Series(0.001, index=dates)
        factor_returns = pd.DataFrame({
            "market": pd.Series(0.0008, index=dates),
        })
        
        with pytest.raises(ValueError, match="Insufficient data"):
            analyzer.analyze_factor_exposure(
                portfolio_returns=portfolio_returns,
                factor_returns=factor_returns,
            )

    def test_analyze_factor_exposure_with_risk_free_rate(self, analyzer, sample_portfolio_returns, sample_factor_returns):
        """Test factor analysis with risk-free rate"""
        results = analyzer.analyze_factor_exposure(
            portfolio_returns=sample_portfolio_returns,
            factor_returns=sample_factor_returns,
            risk_free_rate=0.03,  # Override default
        )
        
        assert results is not None
        assert "alpha" in results

    def test_calculate_factor_attribution(self, analyzer, sample_portfolio_returns, sample_factor_returns):
        """Test factor attribution calculation"""
        attribution = analyzer.calculate_factor_attribution(
            portfolio_returns=sample_portfolio_returns,
            factor_returns=sample_factor_returns,
        )
        
        assert isinstance(attribution, pd.DataFrame)
        assert "alpha" in attribution.columns
        assert "market_contribution" in attribution.columns
        assert "size_contribution" in attribution.columns
        assert "value_contribution" in attribution.columns
        assert "total_explained" in attribution.columns
        assert "residual" in attribution.columns

    def test_decompose_factor_risk(self, analyzer, sample_portfolio_returns, sample_factor_returns):
        """Test factor risk decomposition"""
        risk_decomp = analyzer.decompose_factor_risk(
            portfolio_returns=sample_portfolio_returns,
            factor_returns=sample_factor_returns,
        )
        
        assert isinstance(risk_decomp, dict)
        assert "portfolio_volatility" in risk_decomp
        assert "factor_volatility" in risk_decomp
        assert "residual_volatility" in risk_decomp
        assert "factor_explained_ratio" in risk_decomp
        assert "factor_risk_contributions" in risk_decomp
        
        # Check volatility values are positive
        assert risk_decomp["portfolio_volatility"] > 0
        assert risk_decomp["factor_volatility"] >= 0
        assert risk_decomp["residual_volatility"] >= 0
        
        # Check explained ratio is between 0 and 1
        assert 0 <= risk_decomp["factor_explained_ratio"] <= 1
        
        # Check factor risk contributions
        assert "market" in risk_decomp["factor_risk_contributions"]
        assert "size" in risk_decomp["factor_risk_contributions"]
        assert "value" in risk_decomp["factor_risk_contributions"]

    def test_decompose_factor_risk_with_covariance(self, analyzer, sample_portfolio_returns, sample_factor_returns):
        """Test risk decomposition with provided covariance matrix"""
        # Create custom covariance matrix
        factor_cov = sample_factor_returns.cov() * 252  # Annualized
        
        risk_decomp = analyzer.decompose_factor_risk(
            portfolio_returns=sample_portfolio_returns,
            factor_returns=sample_factor_returns,
            factor_covariance=factor_cov,
        )
        
        assert risk_decomp is not None
        assert "factor_covariance_matrix" in risk_decomp


@pytest.mark.skipif(not FACTOR_ANALYSIS_AVAILABLE, reason="Factor analysis not available")
class TestConvenienceFunction:
    """Tests for convenience function"""

    def test_analyze_portfolio_factors(self):
        """Test convenience function"""
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        portfolio_returns = pd.Series(
            np.random.normal(0.001, 0.02, 100),
            index=dates,
        )
        factor_returns = pd.DataFrame({
            "market": np.random.normal(0.0008, 0.018, 100),
            "size": np.random.normal(0.0002, 0.01, 100),
        }, index=dates)
        
        results = analyze_portfolio_factors(
            portfolio_returns=portfolio_returns,
            factor_returns=factor_returns,
            risk_free_rate=0.02,
        )
        
        assert isinstance(results, dict)
        assert "alpha" in results
        assert "factor_exposures" in results


@pytest.mark.skipif(not FACTOR_ANALYSIS_AVAILABLE, reason="Factor analysis not available")
class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_returns(self):
        """Test with empty returns"""
        analyzer = FactorAnalyzer()
        empty_returns = pd.Series([], dtype=float)
        empty_factors = pd.DataFrame()
        
        with pytest.raises(ValueError):
            analyzer.analyze_factor_exposure(
                portfolio_returns=empty_returns,
                factor_returns=empty_factors,
            )

    def test_mismatched_dates(self):
        """Test with non-overlapping dates"""
        analyzer = FactorAnalyzer()
        dates1 = pd.date_range(start="2024-01-01", periods=50, freq="D")
        dates2 = pd.date_range(start="2025-01-01", periods=50, freq="D")
        
        portfolio_returns = pd.Series(0.001, index=dates1)
        factor_returns = pd.DataFrame({
            "market": pd.Series(0.0008, index=dates2),
        })
        
        with pytest.raises(ValueError, match="Insufficient data"):
            analyzer.analyze_factor_exposure(
                portfolio_returns=portfolio_returns,
                factor_returns=factor_returns,
            )

    def test_single_factor(self):
        """Test with single factor"""
        analyzer = FactorAnalyzer()
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        
        portfolio_returns = pd.Series(
            np.random.normal(0.001, 0.02, 100),
            index=dates,
        )
        factor_returns = pd.DataFrame({
            "market": np.random.normal(0.0008, 0.018, 100),
        }, index=dates)
        
        results = analyzer.analyze_factor_exposure(
            portfolio_returns=portfolio_returns,
            factor_returns=factor_returns,
        )
        
        assert "market" in results["factor_exposures"]
        assert len(results["factor_exposures"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
