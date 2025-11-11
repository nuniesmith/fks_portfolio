"""
Pytest configuration and fixtures
"""
import pytest
import pandas as pd
import numpy as np
from src.portfolio.portfolio import Portfolio
from src.portfolio.asset import CryptoAsset, StockAsset, CashAsset


@pytest.fixture
def sample_portfolio():
    """Create a sample portfolio for testing"""
    portfolio = Portfolio()
    
    btc = CryptoAsset(
        symbol="BTC",
        volatility=0.60,
        correlation_to_btc=1.0,
        expected_return=0.15
    )
    portfolio.add_asset(btc, allocation=0.5)
    
    eth = CryptoAsset(
        symbol="ETH",
        volatility=0.70,
        correlation_to_btc=0.80,
        expected_return=0.18
    )
    portfolio.add_asset(eth, allocation=0.2)
    
    spy = StockAsset(
        symbol="SPY",
        sector="Diversified",
        volatility=0.20,
        correlation_to_btc=0.30,
        expected_return=0.10
    )
    portfolio.add_asset(spy, allocation=0.15)
    
    cash = CashAsset()
    portfolio.add_asset(cash, allocation=0.15)
    
    return portfolio


@pytest.fixture
def sample_returns():
    """Create sample returns for testing"""
    np.random.seed(42)
    return pd.Series(np.random.normal(0.001, 0.02, 100))


@pytest.fixture
def sample_historical_prices():
    """Create sample historical prices"""
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
    np.random.seed(42)
    
    data = {
        'BTC': 40000 + np.cumsum(np.random.normal(100, 500, len(dates))),
        'ETH': 2500 + np.cumsum(np.random.normal(10, 50, len(dates))),
        'SPY': 400 + np.cumsum(np.random.normal(0.5, 2, len(dates)))
    }
    
    return pd.DataFrame(data, index=dates)

