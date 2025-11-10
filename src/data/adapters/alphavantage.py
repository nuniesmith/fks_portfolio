"""
Alpha Vantage data adapter
Free tier: 5 calls/minute, 500 calls/day
"""
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import requests
from loguru import logger
import os
from dotenv import load_dotenv
import time

from .base import BaseDataAdapter

load_dotenv()


class AlphaVantageAdapter(BaseDataAdapter):
    """Alpha Vantage adapter for stocks and forex"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    # Supported symbols
    STOCK_SYMBOLS = [
        "SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
        "NVDA", "META", "NFLX", "DIS", "JPM", "V", "MA", "WMT"
    ]
    
    def __init__(self, api_key: Optional[str] = None, rate_limit_per_minute: int = 5):
        """
        Initialize Alpha Vantage adapter
        
        Args:
            api_key: Alpha Vantage API key (required)
            rate_limit_per_minute: Rate limit (5 for free tier)
        """
        super().__init__("AlphaVantage", rate_limit_per_minute)
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            self.logger.warning("Alpha Vantage API key not found. Set ALPHA_VANTAGE_API_KEY in .env")
        self.logger = logger.bind(adapter="AlphaVantage")
        self._last_request_time = None
        self._min_request_interval = 12  # 5 calls/minute = 12 seconds between calls
    
    def _make_request(self, params: dict) -> Optional[dict]:
        """Make API request with rate limiting"""
        if not self.api_key:
            self.logger.error("API key required for Alpha Vantage")
            return None
        
        # Enforce minimum interval between requests
        if self._last_request_time:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_request_interval:
                wait_time = self._min_request_interval - elapsed
                self.logger.debug(f"Rate limiting: waiting {wait_time:.1f} seconds")
                time.sleep(wait_time)
        
        try:
            self._check_rate_limit()
            params["apikey"] = self.api_key
            
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            self._last_request_time = time.time()
            
            # Check for API errors
            if "Error Message" in data:
                self.logger.error(f"Alpha Vantage error: {data['Error Message']}")
                return None
            if "Note" in data:
                self.logger.warning(f"Alpha Vantage note: {data['Note']}")
                return None
            
            return data
        except Exception as e:
            self.logger.error(f"Alpha Vantage API error: {e}")
            return None
    
    def fetch_price(self, symbol: str, timestamp: Optional[datetime] = None) -> Optional[float]:
        """Fetch current price"""
        if not self.api_key:
            return None
        
        try:
            # Use TIME_SERIES_DAILY for historical or current
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": "compact"  # Last 100 data points
            }
            
            data = self._make_request(params)
            if not data or "Time Series (Daily)" not in data:
                return None
            
            time_series = data["Time Series (Daily)"]
            
            if timestamp:
                # Get price for specific date
                date_str = timestamp.strftime("%Y-%m-%d")
                if date_str in time_series:
                    return float(time_series[date_str]["4. close"])
            else:
                # Get latest price
                latest_date = max(time_series.keys())
                return float(time_series[latest_date]["4. close"])
            
            return None
        except Exception as e:
            self.logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def fetch_historical_prices(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "daily"
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data"""
        if not self.api_key:
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        
        try:
            # Alpha Vantage only supports daily for free tier
            if interval != "daily":
                self.logger.warning("Alpha Vantage free tier only supports daily data")
                interval = "daily"
            
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": "full"  # Full historical data
            }
            
            data = self._make_request(params)
            if not data or "Time Series (Daily)" not in data:
                return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            
            time_series = data["Time Series (Daily)"]
            records = []
            
            for date_str, values in time_series.items():
                date = pd.to_datetime(date_str)
                if start_date <= date <= end_date:
                    records.append({
                        "date": date,
                        "open": float(values["1. open"]),
                        "high": float(values["2. high"]),
                        "low": float(values["3. low"]),
                        "close": float(values["4. close"]),
                        "volume": float(values["5. volume"])
                    })
            
            df = pd.DataFrame(records)
            df = df.sort_values("date")
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        return self.STOCK_SYMBOLS.copy()

