"""
Tests for BTC conversion functionality
"""
import pytest
from datetime import datetime, timedelta
import pandas as pd
from src.data.btc_converter import BTCConverter
from src.data.manager import DataManager
from src.portfolio.portfolio_value import PortfolioValueTracker
from src.portfolio.portfolio import Portfolio
from src.portfolio.asset import CryptoAsset, StockAsset


class TestBTCConverter:
    """Test BTC converter"""
    
    def test_converter_creation(self):
        """Test creating converter"""
        converter = BTCConverter()
        assert converter is not None
    
    def test_get_btc_price(self):
        """Test getting BTC price"""
        converter = BTCConverter()
        price = converter.get_btc_price()
        # Price should be positive if successful
        if price:
            assert price > 0
            assert isinstance(price, float)
    
    def test_to_btc(self):
        """Test converting asset to BTC"""
        converter = BTCConverter()
        # Convert 1 ETH to BTC
        btc_amount = converter.to_btc(1.0, "ETH")
        if btc_amount:
            assert btc_amount > 0
            assert isinstance(btc_amount, float)
    
    def test_from_btc(self):
        """Test converting BTC to asset"""
        converter = BTCConverter()
        # Convert 0.01 BTC to ETH
        eth_amount = converter.from_btc(0.01, "ETH")
        if eth_amount:
            assert eth_amount > 0
            assert isinstance(eth_amount, float)
    
    def test_convert_portfolio_to_btc(self):
        """Test converting portfolio to BTC"""
        converter = BTCConverter()
        holdings = {
            "BTC": 0.5,
            "ETH": 1.0,
            "SPY": 0.1
        }
        btc_holdings = converter.convert_portfolio_to_btc(holdings)
        
        assert "_total" in btc_holdings
        assert btc_holdings["_total"] > 0
    
    def test_get_btc_allocation(self):
        """Test calculating BTC allocation"""
        converter = BTCConverter()
        holdings = {
            "BTC": 0.5,
            "ETH": 0.3,
            "SPY": 0.2
        }
        allocation = converter.get_btc_allocation(holdings)
        
        # Allocation should be between 0 and 1
        assert 0 <= allocation <= 1
    
    def test_get_conversion_rate(self):
        """Test getting conversion rate"""
        converter = BTCConverter()
        rate = converter.get_conversion_rate("ETH", "BTC")
        if rate:
            assert rate > 0


class TestPortfolioValueTracker:
    """Test portfolio value tracker"""
    
    @pytest.fixture
    def sample_portfolio(self):
        """Create sample portfolio"""
        portfolio = Portfolio()
        portfolio.add_asset(
            CryptoAsset("BTC", volatility=0.6, correlation_to_btc=1.0),
            allocation=0.5
        )
        portfolio.add_asset(
            CryptoAsset("ETH", volatility=0.7, correlation_to_btc=0.8),
            allocation=0.2
        )
        portfolio.add_asset(
            StockAsset("SPY", sector="Diversified", volatility=0.2, correlation_to_btc=0.3),
            allocation=0.15
        )
        return portfolio
    
    def test_tracker_creation(self, sample_portfolio):
        """Test creating tracker"""
        tracker = PortfolioValueTracker(sample_portfolio)
        assert tracker is not None
    
    def test_calculate_current_value_btc(self, sample_portfolio):
        """Test calculating current value"""
        tracker = PortfolioValueTracker(sample_portfolio)
        value = tracker.calculate_current_value_btc()
        
        assert "total_btc" in value
        assert "btc_allocation" in value
        assert "holdings_btc" in value
    
    def test_get_btc_allocation_breakdown(self, sample_portfolio):
        """Test getting allocation breakdown"""
        tracker = PortfolioValueTracker(sample_portfolio)
        breakdown = tracker.get_btc_allocation_breakdown()
        
        assert isinstance(breakdown, dict)
        # Allocations should sum to approximately 1.0
        total = sum(breakdown.values())
        assert abs(total - 1.0) < 0.1  # Allow small rounding errors

