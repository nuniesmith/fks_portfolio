"""
Tests for diversification and rebalancing
"""
import pytest
from src.portfolio.asset_categories import AssetCategorizer, AssetCategory
from src.optimization.correlation import CorrelationAnalyzer
from src.portfolio.rebalancing import PortfolioRebalancer
from src.portfolio.portfolio import Portfolio
from src.portfolio.asset import CryptoAsset, StockAsset


class TestAssetCategorizer:
    """Test asset categorizer"""
    
    def test_get_category(self):
        """Test getting category for symbol"""
        cat = AssetCategorizer()
        categories = cat.get_category("BTC")
        assert AssetCategory.STABLE_CRYPTO in categories
    
    def test_get_symbols_in_category(self):
        """Test getting symbols in category"""
        cat = AssetCategorizer()
        symbols = cat.get_symbols_in_category(AssetCategory.STABLE_CRYPTO)
        assert "BTC" in symbols
        assert "ETH" in symbols
    
    def test_is_diversified(self):
        """Test diversification check"""
        cat = AssetCategorizer()
        # Diversified portfolio
        assert cat.is_diversified(["BTC", "ETH", "SPY", "GLD"])
        # Not diversified (all crypto)
        assert not cat.is_diversified(["BTC", "ETH", "SOL"])
    
    def test_get_diversification_score(self):
        """Test diversification score"""
        cat = AssetCategorizer()
        score = cat.get_diversification_score(["BTC", "ETH", "SPY", "GLD"])
        assert 0 <= score <= 1
    
    def test_suggest_diversification(self):
        """Test diversification suggestions"""
        cat = AssetCategorizer()
        suggestions = cat.suggest_diversification(["BTC", "ETH"])
        assert len(suggestions) > 0
        assert "SPY" in suggestions or "GLD" in suggestions


class TestCorrelationAnalyzer:
    """Test correlation analyzer"""
    
    def test_analyzer_creation(self):
        """Test creating analyzer"""
        analyzer = CorrelationAnalyzer()
        assert analyzer is not None
    
    def test_calculate_correlation_matrix(self):
        """Test calculating correlation matrix"""
        analyzer = CorrelationAnalyzer()
        symbols = ["BTC", "ETH", "SPY"]
        matrix = analyzer.calculate_correlation_matrix(symbols, lookback_days=30)
        
        # Should return DataFrame (may be empty if no data)
        assert isinstance(matrix, type(analyzer.data_manager.fetch_historical_prices("BTC", analyzer.data_manager, analyzer.data_manager)))
    
    def test_calculate_btc_correlations(self):
        """Test calculating BTC correlations"""
        analyzer = CorrelationAnalyzer()
        symbols = ["ETH", "SPY"]
        corrs = analyzer.calculate_btc_correlations(symbols, lookback_days=30)
        
        # Should return dict
        assert isinstance(corrs, dict)


class TestPortfolioRebalancer:
    """Test portfolio rebalancer"""
    
    @pytest.fixture
    def sample_portfolio(self):
        """Create sample portfolio"""
        portfolio = Portfolio()
        portfolio.add_asset(
            CryptoAsset("BTC", volatility=0.6, correlation_to_btc=1.0),
            allocation=0.4
        )
        portfolio.add_asset(
            CryptoAsset("ETH", volatility=0.7, correlation_to_btc=0.8),
            allocation=0.3
        )
        portfolio.add_asset(
            StockAsset("SPY", sector="Diversified", volatility=0.2, correlation_to_btc=0.3),
            allocation=0.3
        )
        return portfolio
    
    def test_rebalancer_creation(self, sample_portfolio):
        """Test creating rebalancer"""
        rebalancer = PortfolioRebalancer(sample_portfolio, target_btc_pct=0.5)
        assert rebalancer is not None
    
    def test_get_current_btc_allocation(self, sample_portfolio):
        """Test getting current BTC allocation"""
        rebalancer = PortfolioRebalancer(sample_portfolio, target_btc_pct=0.5)
        allocation = rebalancer.get_current_btc_allocation()
        
        # Should be between 0 and 1
        assert 0 <= allocation <= 1

