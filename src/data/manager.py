"""
Unified data manager that coordinates adapters, caching, and storage
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from .adapters import (
    BaseDataAdapter,
    YahooFinanceAdapter,
    CoinGeckoAdapter,
    PolygonAdapter,
    AlphaVantageAdapter,
    BinanceAdapter,
    CoinMarketCapAdapter
)
from .cache import DataCache
from .storage import DataStorage


class DataManager:
    """Unified data manager for fetching and storing price data"""
    
    def __init__(
        self,
        cache_dir: Optional[str] = "data/cache",
        db_path: Optional[str] = "data/historical/portfolio.db",
        enable_cache: bool = True,
        enable_storage: bool = True
    ):
        """
        Initialize data manager
        
        Args:
            cache_dir: Directory for cache files
            db_path: Path to SQLite database
            enable_cache: Enable caching layer
            enable_storage: Enable database storage
        """
        self.logger = logger.bind(component="DataManager")
        
        # Initialize adapters
        self.adapters: Dict[str, BaseDataAdapter] = {
            "yahoofinance": YahooFinanceAdapter(),
            "coingecko": CoinGeckoAdapter(),
            "binance": BinanceAdapter(),
            "polygon": PolygonAdapter(),
            "alphavantage": AlphaVantageAdapter(),
            "coinmarketcap": CoinMarketCapAdapter()
        }
        
        # Initialize cache and storage
        self.cache = DataCache(cache_dir=cache_dir, ttl_seconds=300) if enable_cache else None
        self.storage = DataStorage(db_path=db_path) if enable_storage else None
    
    def _select_adapter(self, symbol: str, preferred_adapters: Optional[List[str]] = None) -> Optional[BaseDataAdapter]:
        """
        Select appropriate adapter for symbol
        
        Args:
            symbol: Asset symbol
            preferred_adapters: Optional list of preferred adapter names in order
        
        Returns:
            Best available adapter
        """
        # Try preferred adapters first
        if preferred_adapters:
            for adapter_name in preferred_adapters:
                adapter = self.adapters.get(adapter_name)
                if adapter and adapter.is_symbol_supported(symbol):
                    return adapter
        
        # Auto-select based on symbol type
        crypto_symbols = ["BTC", "ETH", "SOL", "BNB", "ADA", "AVAX", "MATIC", "DOT", "LINK", "UNI", "XRP", "DOGE"]
        symbol_upper = symbol.upper()
        
        if symbol_upper in crypto_symbols:
            # Try crypto adapters in order of preference
            for adapter_name in ["binance", "coingecko", "coinmarketcap"]:
                adapter = self.adapters.get(adapter_name)
                if adapter and adapter.is_symbol_supported(symbol):
                    return adapter
        
        # Default to Yahoo Finance for stocks
        return self.adapters.get("yahoofinance")
    
    def fetch_price(
        self,
        symbol: str,
        timestamp: Optional[datetime] = None,
        use_cache: bool = True,
        preferred_adapters: Optional[List[str]] = None
    ) -> Optional[float]:
        """
        Fetch price for symbol
        
        Args:
            symbol: Asset symbol
            timestamp: Optional timestamp for historical price
            use_cache: Use cache if available
            preferred_adapters: Optional list of preferred adapter names
        
        Returns:
            Price or None
        """
        adapter = self._select_adapter(symbol, preferred_adapters)
        if not adapter:
            self.logger.error(f"No adapter available for {symbol}")
            return None
        
        # Check cache first
        if use_cache and self.cache:
            cached_price = self.cache.get(adapter.name, symbol, timestamp)
            if cached_price is not None:
                self.logger.debug(f"Cache hit for {symbol}")
                return cached_price
        
        # Fetch from adapter
        try:
            price = adapter.fetch_price(symbol, timestamp)
            
            # Cache result
            if price is not None and use_cache and self.cache:
                self.cache.set(adapter.name, symbol, price, timestamp)
            
            return price
        except Exception as e:
            self.logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def fetch_historical_prices(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "daily",
        use_cache: bool = True,
        use_storage: bool = True,
        preferred_adapters: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Fetch historical prices
        
        Args:
            symbol: Asset symbol
            start_date: Start date
            end_date: End date
            interval: Data interval ("daily", "hourly", "minute")
            use_cache: Use cache if available
            use_storage: Check database storage first
            preferred_adapters: Optional list of preferred adapter names
        
        Returns:
            DataFrame with historical prices
        """
        adapter = self._select_adapter(symbol, preferred_adapters)
        if not adapter:
            self.logger.error(f"No adapter available for {symbol}")
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        
        # Check storage first
        if use_storage and self.storage:
            stored_data = self.storage.get_prices(symbol, start_date, end_date)
            if not stored_data.empty:
                self.logger.info(f"Retrieved {len(stored_data)} records from storage for {symbol}")
                # Check if we have complete data
                date_range = pd.date_range(start_date, end_date, freq='D')
                if len(stored_data) >= len(date_range) * 0.8:  # 80% coverage
                    return stored_data
        
        # Fetch from adapter
        try:
            prices_df = adapter.fetch_historical_prices(symbol, start_date, end_date, interval)
            
            # Store in database
            if not prices_df.empty and use_storage and self.storage:
                self.storage.store_prices(symbol, prices_df, adapter.name)
            
            return prices_df
        except Exception as e:
            self.logger.error(f"Error fetching historical prices for {symbol}: {e}")
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    
    def fetch_multiple_prices(
        self,
        symbols: List[str],
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Optional[float]]:
        """
        Fetch prices for multiple symbols
        
        Args:
            symbols: List of asset symbols
            timestamp: Optional timestamp
        
        Returns:
            Dictionary mapping symbol to price
        """
        results = {}
        for symbol in symbols:
            price = self.fetch_price(symbol, timestamp)
            results[symbol] = price
        return results
    
    def get_supported_symbols(self) -> List[str]:
        """Get all supported symbols from all adapters"""
        symbols = set()
        for adapter in self.adapters.values():
            symbols.update(adapter.get_supported_symbols())
        return sorted(list(symbols))

