"""
Tests for Portfolio and Asset classes
"""
import pytest
from src.portfolio.portfolio import Portfolio
from src.portfolio.asset import CryptoAsset, StockAsset, CashAsset, AssetType


class TestAsset:
    """Test asset classes"""
    
    def test_crypto_asset_creation(self):
        """Test creating a crypto asset"""
        btc = CryptoAsset(
            symbol="BTC",
            volatility=0.60,
            correlation_to_btc=1.0,
            expected_return=0.15
        )
        assert btc.symbol == "BTC"
        assert btc.asset_type == AssetType.CRYPTO
        assert btc.volatility == 0.60
        assert btc.correlation_to_btc == 1.0
    
    def test_stock_asset_creation(self):
        """Test creating a stock asset"""
        spy = StockAsset(
            symbol="SPY",
            sector="Diversified",
            volatility=0.20,
            correlation_to_btc=0.30,
            expected_return=0.10
        )
        assert spy.symbol == "SPY"
        assert spy.asset_type == AssetType.STOCK
        assert spy.sector == "Diversified"
    
    def test_cash_asset_creation(self):
        """Test creating a cash asset"""
        cash = CashAsset()
        assert cash.symbol == "USD"
        assert cash.asset_type == AssetType.CASH
        assert cash.volatility == 0.0
        assert cash.current_price == 1.0
    
    def test_asset_validation(self):
        """Test asset validation"""
        # Invalid volatility
        with pytest.raises(ValueError):
            CryptoAsset(symbol="BTC", volatility=-0.1)
        
        # Invalid correlation
        with pytest.raises(ValueError):
            CryptoAsset(symbol="BTC", correlation_to_btc=1.5)
        
        # Empty symbol
        with pytest.raises(ValueError):
            CryptoAsset(symbol="")


class TestPortfolio:
    """Test Portfolio class"""
    
    def test_create_empty_portfolio(self):
        """Test creating an empty portfolio"""
        portfolio = Portfolio()
        assert len(portfolio.assets) == 0
        assert len(portfolio.allocations) == 0
    
    def test_add_asset(self):
        """Test adding assets to portfolio"""
        portfolio = Portfolio()
        btc = CryptoAsset(symbol="BTC", volatility=0.60, correlation_to_btc=1.0)
        
        portfolio.add_asset(btc, allocation=0.5)
        assert len(portfolio.assets) == 1
        assert portfolio.get_allocation("BTC") == 0.5
    
    def test_set_allocation(self):
        """Test setting allocation"""
        portfolio = Portfolio()
        btc = CryptoAsset(symbol="BTC", volatility=0.60, correlation_to_btc=1.0)
        portfolio.add_asset(btc, allocation=0.4)
        
        portfolio.set_allocation("BTC", 0.55)
        assert portfolio.get_allocation("BTC") == 0.55
    
    def test_validate_allocations(self):
        """Test allocation validation"""
        portfolio = Portfolio()
        btc = CryptoAsset(symbol="BTC", volatility=0.60, correlation_to_btc=1.0)
        eth = CryptoAsset(symbol="ETH", volatility=0.70, correlation_to_btc=0.80)
        
        portfolio.add_asset(btc, allocation=0.5)
        portfolio.add_asset(eth, allocation=0.5)
        
        valid, error = portfolio.validate_allocations()
        assert valid is True
        assert error is None
    
    def test_validate_allocations_invalid(self):
        """Test invalid allocation validation"""
        portfolio = Portfolio()
        btc = CryptoAsset(symbol="BTC", volatility=0.60, correlation_to_btc=1.0)
        portfolio.add_asset(btc, allocation=0.5)
        
        valid, error = portfolio.validate_allocations()
        assert valid is False
        assert "50.00%" in error
    
    def test_btc_constraints(self):
        """Test BTC constraint checking"""
        portfolio = Portfolio()
        btc = CryptoAsset(symbol="BTC", volatility=0.60, correlation_to_btc=1.0)
        
        # Test valid BTC allocation (50%)
        portfolio.add_asset(btc, allocation=0.5)
        valid, error = portfolio.check_btc_constraints()
        assert valid is True
        
        # Test below minimum (40%)
        portfolio.set_allocation("BTC", 0.4)
        valid, error = portfolio.check_btc_constraints()
        assert valid is False
        assert "below minimum" in error
        
        # Test above maximum (70%)
        portfolio.set_allocation("BTC", 0.7)
        valid, error = portfolio.check_btc_constraints()
        assert valid is False
        assert "exceeds maximum" in error
    
    def test_get_portfolio_summary(self):
        """Test portfolio summary generation"""
        portfolio = Portfolio()
        btc = CryptoAsset(symbol="BTC", volatility=0.60, correlation_to_btc=1.0)
        eth = CryptoAsset(symbol="ETH", volatility=0.70, correlation_to_btc=0.80)
        
        portfolio.add_asset(btc, allocation=0.5)
        portfolio.add_asset(eth, allocation=0.5)
        
        summary = portfolio.get_portfolio_summary()
        assert summary["total_assets"] == 2
        assert summary["btc_allocation"] == 0.5
        assert summary["allocations_valid"] is True
        assert summary["btc_constraints_met"] is True

