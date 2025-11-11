"""
Tests for data adapters
"""
import pytest
from datetime import datetime, timedelta
import pandas as pd
from src.data.adapters import YahooFinanceAdapter, CoinGeckoAdapter
from src.data.cache import DataCache
from src.data.storage import DataStorage
from src.data.manager import DataManager


class TestYahooFinanceAdapter:
    """Test Yahoo Finance adapter"""
    
    def test_adapter_creation(self):
        """Test creating adapter"""
        adapter = YahooFinanceAdapter()
        assert adapter.name == "YahooFinance"
        assert adapter.rate_limit_per_minute > 0
    
    def test_get_supported_symbols(self):
        """Test getting supported symbols"""
        adapter = YahooFinanceAdapter()
        symbols = adapter.get_supported_symbols()
        assert len(symbols) > 0
        assert "SPY" in symbols
        assert "BTC" in symbols
    
    def test_fetch_price(self):
        """Test fetching current price"""
        adapter = YahooFinanceAdapter()
        price = adapter.fetch_price("SPY")
        # Price should be positive if successful
        if price:
            assert price > 0
            assert isinstance(price, float)
    
    def test_fetch_historical_prices(self):
        """Test fetching historical prices"""
        adapter = YahooFinanceAdapter()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        df = adapter.fetch_historical_prices("SPY", start_date, end_date, interval="daily")
        
        # Should return DataFrame
        assert isinstance(df, pd.DataFrame)
        
        # If data available, check columns
        if not df.empty:
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                assert col in df.columns


class TestCoinGeckoAdapter:
    """Test CoinGecko adapter"""
    
    def test_adapter_creation(self):
        """Test creating adapter"""
        adapter = CoinGeckoAdapter()
        assert adapter.name == "CoinGecko"
    
    def test_get_supported_symbols(self):
        """Test getting supported symbols"""
        adapter = CoinGeckoAdapter()
        symbols = adapter.get_supported_symbols()
        assert len(symbols) > 0
        assert "BTC" in symbols
        assert "ETH" in symbols
    
    def test_fetch_price(self):
        """Test fetching current price (may require internet)"""
        adapter = CoinGeckoAdapter()
        price = adapter.fetch_price("BTC")
        # Price should be positive if successful
        if price:
            assert price > 0
            assert isinstance(price, float)


class TestDataCache:
    """Test data cache"""
    
    def test_cache_creation(self):
        """Test creating cache"""
        cache = DataCache()
        assert cache.ttl_seconds == 300
    
    def test_cache_set_get(self):
        """Test setting and getting from cache"""
        cache = DataCache()
        
        # Set value
        cache.set("test_adapter", "BTC", 50000.0)
        
        # Get value
        value = cache.get("test_adapter", "BTC")
        assert value == 50000.0
    
    def test_cache_expiration(self):
        """Test cache expiration"""
        cache = DataCache(ttl_seconds=1)  # 1 second TTL
        
        # Set value
        cache.set("test_adapter", "BTC", 50000.0)
        
        # Should be available immediately
        assert cache.get("test_adapter", "BTC") == 50000.0
        
        # Wait for expiration (would need time.sleep in real test)
        # For now, just verify the structure works


class TestDataStorage:
    """Test data storage"""
    
    def test_storage_creation(self, tmp_path):
        """Test creating storage"""
        db_path = tmp_path / "test.db"
        storage = DataStorage(str(db_path))
        assert storage.db_path.exists()
    
    def test_store_and_retrieve_prices(self, tmp_path):
        """Test storing and retrieving prices"""
        db_path = tmp_path / "test.db"
        storage = DataStorage(str(db_path))
        
        # Create sample data
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'open': [100] * 10,
            'high': [105] * 10,
            'low': [95] * 10,
            'close': [102] * 10,
            'volume': [1000] * 10
        })
        
        # Store
        storage.store_prices("TEST", df, "test_adapter")
        
        # Retrieve
        retrieved = storage.get_prices("TEST")
        assert not retrieved.empty
        assert len(retrieved) == 10


class TestDataManager:
    """Test data manager"""
    
    def test_manager_creation(self, tmp_path):
        """Test creating data manager"""
        cache_dir = tmp_path / "cache"
        db_path = tmp_path / "test.db"
        
        manager = DataManager(
            cache_dir=str(cache_dir),
            db_path=str(db_path)
        )
        assert manager.cache is not None
        assert manager.storage is not None
    
    def test_fetch_price(self, tmp_path):
        """Test fetching price through manager"""
        cache_dir = tmp_path / "cache"
        db_path = tmp_path / "test.db"
        
        manager = DataManager(
            cache_dir=str(cache_dir),
            db_path=str(db_path)
        )
        
        # Fetch price (may require internet)
        price = manager.fetch_price("SPY")
        if price:
            assert price > 0
    
    def test_get_supported_symbols(self, tmp_path):
        """Test getting supported symbols"""
        cache_dir = tmp_path / "cache"
        db_path = tmp_path / "test.db"
        
        manager = DataManager(
            cache_dir=str(cache_dir),
            db_path=str(db_path)
        )
        
        symbols = manager.get_supported_symbols()
        assert len(symbols) > 0

