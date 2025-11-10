"""
CoinMarketCap (CMC) data adapter
Free tier: 333 calls/day, 10,000 credits/month
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


class CoinMarketCapAdapter(BaseDataAdapter):
    """CoinMarketCap adapter for cryptocurrency data"""
    
    BASE_URL = "https://pro-api.coinmarketcap.com/v1"
    
    # Common crypto symbols
    CRYPTO_SYMBOLS = [
        "BTC", "ETH", "BNB", "SOL", "ADA", "XRP", "DOGE", "DOT",
        "MATIC", "AVAX", "LINK", "UNI", "ATOM", "ALGO", "LTC", "SHIB"
    ]
    
    def __init__(self, api_key: Optional[str] = None, rate_limit_per_minute: int = 10):
        """
        Initialize CoinMarketCap adapter
        
        Args:
            api_key: CMC API key (required)
            rate_limit_per_minute: Rate limit (10 for free tier)
        """
        super().__init__("CoinMarketCap", rate_limit_per_minute)
        self.api_key = api_key or os.getenv("COINMARKETCAP_API_KEY")
        if not self.api_key:
            self.logger.warning("CoinMarketCap API key not found. Set COINMARKETCAP_API_KEY in .env")
        self.logger = logger.bind(adapter="CoinMarketCap")
        self._symbol_to_id_map = None
    
    def _make_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make API request with authentication"""
        if not self.api_key:
            self.logger.error("API key required for CoinMarketCap")
            return None
        
        try:
            self._check_rate_limit()
            url = f"{self.BASE_URL}{endpoint}"
            headers = {
                "X-CMC_PRO_API_KEY": self.api_key,
                "Accept": "application/json"
            }
            params = params or {}
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check for errors
            if "status" in data and data["status"].get("error_code") != 0:
                error_msg = data["status"].get("error_message", "Unknown error")
                self.logger.error(f"CoinMarketCap API error: {error_msg}")
                return None
            
            return data
        except Exception as e:
            self.logger.error(f"CoinMarketCap API error: {e}")
            return None
    
    def _get_symbol_id_map(self) -> dict:
        """Get mapping from symbol to CMC ID"""
        if self._symbol_to_id_map is not None:
            return self._symbol_to_id_map
        
        try:
            endpoint = "/cryptocurrency/map"
            params = {"listing_status": "active", "limit": 5000}
            data = self._make_request(endpoint, params)
            
            if not data or "data" not in data:
                return {}
            
            symbol_map = {}
            for coin in data["data"]:
                symbol = coin.get("symbol", "").upper()
                if symbol:
                    symbol_map[symbol] = coin["id"]
            
            self._symbol_to_id_map = symbol_map
            return symbol_map
        except Exception as e:
            self.logger.error(f"Error fetching symbol map: {e}")
            return {}
    
    def fetch_price(self, symbol: str, timestamp: Optional[datetime] = None) -> Optional[float]:
        """Fetch current or historical price"""
        if not self.api_key:
            return None
        
        try:
            symbol_map = self._get_symbol_id_map()
            coin_id = symbol_map.get(symbol.upper())
            
            if not coin_id:
                self.logger.warning(f"Symbol {symbol} not found in CoinMarketCap")
                return None
            
            if timestamp:
                # Historical price (requires different endpoint or historical data)
                # CMC free tier doesn't support historical quotes easily
                # Would need to use quotes/historical endpoint (paid feature)
                self.logger.warning("Historical prices require paid CMC plan")
                return None
            else:
                # Current price
                endpoint = "/cryptocurrency/quotes/latest"
                params = {"id": coin_id}
                data = self._make_request(endpoint, params)
                
                if data and "data" in data and str(coin_id) in data["data"]:
                    quote = data["data"][str(coin_id)]["quote"]["USD"]
                    return float(quote["price"])
            
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
            symbol_map = self._get_symbol_id_map()
            coin_id = symbol_map.get(symbol.upper())
            
            if not coin_id:
                return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            
            # CMC historical endpoint (may require paid plan)
            endpoint = "/cryptocurrency/quotes/historical"
            params = {
                "id": coin_id,
                "time_start": start_date.isoformat(),
                "time_end": end_date.isoformat(),
                "interval": interval  # "hourly", "daily"
            }
            
            data = self._make_request(endpoint, params)
            
            if not data or "data" not in data:
                self.logger.warning("Historical data may require paid CMC plan")
                return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            
            # Parse response (structure depends on CMC API version)
            # This is a placeholder - actual implementation depends on CMC API response format
            records = []
            # ... parse data ...
            
            df = pd.DataFrame(records)
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        return self.CRYPTO_SYMBOLS.copy()

