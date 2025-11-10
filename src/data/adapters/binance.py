"""
Binance data adapter
Free public API, no key required for market data
"""
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import requests
from loguru import logger

from .base import BaseDataAdapter


class BinanceAdapter(BaseDataAdapter):
    """Binance adapter for cryptocurrency data"""
    
    BASE_URL = "https://api.binance.com/api/v3"
    
    # Common crypto symbols (Binance uses base/quote pairs)
    CRYPTO_SYMBOLS = [
        "BTC", "ETH", "BNB", "SOL", "ADA", "XRP", "DOGE", "DOT",
        "MATIC", "AVAX", "LINK", "UNI", "ATOM", "ALGO", "LTC"
    ]
    
    def __init__(self, rate_limit_per_minute: int = 1200):
        """
        Initialize Binance adapter
        
        Args:
            rate_limit_per_minute: Rate limit (1200 for public API)
        """
        super().__init__("Binance", rate_limit_per_minute)
        self.logger = logger.bind(adapter="Binance")
        self._symbol_map = {}  # Map symbol to Binance pair (e.g., BTC -> BTCUSDT)
    
    def _get_pair(self, symbol: str) -> str:
        """Convert symbol to Binance trading pair"""
        if symbol in self._symbol_map:
            return self._symbol_map[symbol]
        
        # Default: append USDT
        pair = f"{symbol}USDT"
        self._symbol_map[symbol] = pair
        return pair
    
    def fetch_price(self, symbol: str, timestamp: Optional[datetime] = None) -> Optional[float]:
        """Fetch current or historical price"""
        try:
            self._check_rate_limit()
            pair = self._get_pair(symbol)
            
            if timestamp:
                # Fetch historical price using klines
                start_time = int(timestamp.timestamp() * 1000)
                url = f"{self.BASE_URL}/klines"
                params = {
                    "symbol": pair,
                    "interval": "1d",
                    "startTime": start_time,
                    "limit": 1
                }
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data and len(data) > 0:
                    return float(data[0][4])  # Close price
            else:
                # Fetch current price
                url = f"{self.BASE_URL}/ticker/price"
                params = {"symbol": pair}
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if "price" in data:
                    return float(data["price"])
            
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
        try:
            self._check_rate_limit()
            pair = self._get_pair(symbol)
            
            # Map interval to Binance format
            interval_map = {
                "daily": "1d",
                "hourly": "1h",
                "minute": "1m"
            }
            binance_interval = interval_map.get(interval, "1d")
            
            # Binance limits to 1000 klines per request
            start_time = int(start_date.timestamp() * 1000)
            end_time = int(end_date.timestamp() * 1000)
            
            all_klines = []
            current_start = start_time
            
            while current_start < end_time:
                url = f"{self.BASE_URL}/klines"
                params = {
                    "symbol": pair,
                    "interval": binance_interval,
                    "startTime": current_start,
                    "endTime": end_time,
                    "limit": 1000
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                klines = response.json()
                
                if not klines:
                    break
                
                all_klines.extend(klines)
                
                # Update start time for next batch
                last_time = klines[-1][0]  # Open time of last kline
                if last_time >= end_time:
                    break
                current_start = last_time + 1
                
                # Rate limit between batches
                import time
                time.sleep(0.1)
            
            if not all_klines:
                return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            
            # Parse klines: [open_time, open, high, low, close, volume, ...]
            records = []
            for kline in all_klines:
                records.append({
                    "date": pd.to_datetime(kline[0], unit="ms"),
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5])
                })
            
            df = pd.DataFrame(records)
            # Filter by date range
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        return self.CRYPTO_SYMBOLS.copy()

