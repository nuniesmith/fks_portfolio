"""
Polygon.io data adapter
Free tier: 5 calls/minute, historical data via S3
"""
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import requests
from loguru import logger
import os
from dotenv import load_dotenv

from .base import BaseDataAdapter

load_dotenv()


class PolygonAdapter(BaseDataAdapter):
    """Polygon.io adapter for stocks, options, and crypto"""
    
    BASE_URL = "https://api.polygon.io"
    
    # Supported stock symbols
    STOCK_SYMBOLS = [
        "SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
        "NVDA", "META", "NFLX", "DIS", "JPM", "V", "MA", "WMT"
    ]
    
    def __init__(self, api_key: Optional[str] = None, rate_limit_per_minute: int = 5):
        """
        Initialize Polygon adapter
        
        Args:
            api_key: Polygon API key (required)
            rate_limit_per_minute: Rate limit (5 for free tier)
        """
        super().__init__("Polygon", rate_limit_per_minute)
        self.api_key = api_key or os.getenv("POLYGON_API_KEY")
        if not self.api_key:
            self.logger.warning("Polygon API key not found. Set POLYGON_API_KEY in .env")
        self.logger = logger.bind(adapter="Polygon")
    
    def _make_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make API request with authentication"""
        if not self.api_key:
            self.logger.error("API key required for Polygon")
            return None
        
        try:
            self._check_rate_limit()
            url = f"{self.BASE_URL}{endpoint}"
            params = params or {}
            params["apiKey"] = self.api_key
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Polygon API error: {e}")
            return None
    
    def fetch_price(self, symbol: str, timestamp: Optional[datetime] = None) -> Optional[float]:
        """Fetch current or historical price"""
        if not self.api_key:
            return None
        
        try:
            if timestamp:
                # Fetch historical price
                date_str = timestamp.strftime("%Y-%m-%d")
                endpoint = f"/v2/aggs/ticker/{symbol}/range/1/day/{date_str}/{date_str}"
                data = self._make_request(endpoint)
                
                if data and "results" in data and len(data["results"]) > 0:
                    return float(data["results"][0]["c"])  # Close price
            else:
                # Fetch current price (last trade)
                endpoint = f"/v2/last/trade/{symbol}"
                data = self._make_request(endpoint)
                
                if data and "results" in data:
                    return float(data["results"]["p"])  # Price
                
                # Fallback: use aggregates for today
                today = datetime.now().strftime("%Y-%m-%d")
                endpoint = f"/v2/aggs/ticker/{symbol}/range/1/day/{today}/{today}"
                data = self._make_request(endpoint)
                
                if data and "results" in data and len(data["results"]) > 0:
                    return float(data["results"][0]["c"])
            
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
            # Map interval to Polygon format
            interval_map = {
                "daily": "1",
                "hourly": "1",
                "minute": "1"
            }
            timespan_map = {
                "daily": "day",
                "hourly": "hour",
                "minute": "minute"
            }
            
            timespan = timespan_map.get(interval, "day")
            multiplier = interval_map.get(interval, "1")
            
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            
            endpoint = f"/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start_str}/{end_str}"
            data = self._make_request(endpoint)
            
            if not data or "results" not in data:
                return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            
            # Parse results
            results = data["results"]
            records = []
            for item in results:
                records.append({
                    "date": pd.to_datetime(item["t"], unit="ms"),
                    "open": item["o"],
                    "high": item["h"],
                    "low": item["l"],
                    "close": item["c"],
                    "volume": item.get("v", 0)
                })
            
            df = pd.DataFrame(records)
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        return self.STOCK_SYMBOLS.copy()
    
    def fetch_from_s3(self, symbol: str, date: datetime) -> Optional[pd.DataFrame]:
        """
        Fetch data from Polygon S3 (for bulk historical data)
        Note: This requires S3 access credentials
        """
        # Polygon S3 structure: s3://polygon-market-data/ticker/{symbol}/{date}/
        # This would require boto3 and S3 credentials
        self.logger.info(f"S3 fetch not yet implemented for {symbol} on {date}")
        return None

