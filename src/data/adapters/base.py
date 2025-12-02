"""
Base data adapter interface
All data adapters should inherit from this class
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger


class BaseDataAdapter(ABC):
    """Base class for all data adapters"""
    
    def __init__(self, name: str, rate_limit_per_minute: int = 60):
        """
        Initialize base adapter
        
        Args:
            name: Adapter name (e.g., "YahooFinance", "CoinGecko")
            rate_limit_per_minute: Maximum requests per minute
        """
        self.name = name
        self.rate_limit_per_minute = rate_limit_per_minute
        self.logger = logger.bind(adapter=name)
        self._last_request_time = None
        self._request_count = 0
        self._request_window_start = datetime.now()
    
    def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = datetime.now()
        
        # Reset counter if window expired
        if (now - self._request_window_start).seconds >= 60:
            self._request_count = 0
            self._request_window_start = now
        
        # Check if we've exceeded rate limit
        if self._request_count >= self.rate_limit_per_minute:
            wait_time = 60 - (now - self._request_window_start).seconds
            if wait_time > 0:
                self.logger.warning(f"Rate limit reached. Waiting {wait_time} seconds...")
                import time
                time.sleep(wait_time)
                self._request_count = 0
                self._request_window_start = datetime.now()
        
        self._request_count += 1
        self._last_request_time = now
    
    @abstractmethod
    def fetch_price(self, symbol: str, timestamp: Optional[datetime] = None) -> Optional[float]:
        """
        Fetch current or historical price for a symbol
        
        Args:
            symbol: Asset symbol (e.g., "BTC", "SPY")
            timestamp: Optional timestamp for historical price
        
        Returns:
            Price as float, or None if not found
        """
        pass
    
    @abstractmethod
    def fetch_historical_prices(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "daily"
    ) -> pd.DataFrame:
        """
        Fetch historical price data
        
        Args:
            symbol: Asset symbol
            start_date: Start date
            end_date: End date
            interval: Data interval ("daily", "hourly", "minute")
        
        Returns:
            DataFrame with columns: ['date', 'open', 'high', 'low', 'close', 'volume']
        """
        pass
    
    @abstractmethod
    def get_supported_symbols(self) -> List[str]:
        """
        Get list of supported symbols for this adapter
        
        Returns:
            List of supported symbols
        """
        pass
    
    def fetch_multiple_prices(
        self,
        symbols: List[str],
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Optional[float]]:
        """
        Fetch prices for multiple symbols
        
        Args:
            symbols: List of asset symbols
            timestamp: Optional timestamp for historical prices
        
        Returns:
            Dictionary mapping symbol to price
        """
        results = {}
        for symbol in symbols:
            try:
                self._check_rate_limit()
                price = self.fetch_price(symbol, timestamp)
                results[symbol] = price
            except Exception as e:
                self.logger.error(f"Error fetching price for {symbol}: {e}")
                results[symbol] = None
        return results
    
    def is_symbol_supported(self, symbol: str) -> bool:
        """Check if symbol is supported by this adapter"""
        return symbol in self.get_supported_symbols()

