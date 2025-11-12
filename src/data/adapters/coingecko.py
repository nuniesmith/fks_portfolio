"""
CoinGecko data adapter
Free tier: 10-50 calls/minute
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


class CoinGeckoAdapter(BaseDataAdapter):
    """CoinGecko adapter for cryptocurrency data"""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    # Common crypto symbols
    CRYPTO_SYMBOLS = [
        "BTC", "ETH", "SOL", "BNB", "ADA", "AVAX", "MATIC", "DOT",
        "LINK", "UNI", "ATOM", "ALGO", "XRP", "DOGE", "SHIB"
    ]
    
    def __init__(self, api_key: Optional[str] = None, rate_limit_per_minute: int = 30):
        """
        Initialize CoinGecko adapter
        
        Args:
            api_key: Optional API key (free tier works without key, but has lower limits)
            rate_limit_per_minute: Rate limit (30 for free tier, 50+ with API key)
        """
        super().__init__("CoinGecko", rate_limit_per_minute)
        self.api_key = api_key or os.getenv("COINGECKO_API_KEY")
        self.logger = logger.bind(adapter="CoinGecko")
        self._symbol_to_id_map = None
    
    def _get_symbol_id_map(self) -> dict:
        """Get mapping from symbol to CoinGecko ID"""
        if self._symbol_to_id_map is not None:
            return self._symbol_to_id_map
        
        try:
            self._check_rate_limit()
            url = f"{self.BASE_URL}/coins/list"
            headers = {}
            if self.api_key:
                headers["x-cg-demo-api-key"] = self.api_key
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            coins = response.json()
            symbol_map = {}
            for coin in coins:
                symbol = coin.get("symbol", "").upper()
                if symbol:
                    symbol_map[symbol] = coin["id"]
            
            self._symbol_to_id_map = symbol_map
            return symbol_map
        except Exception as e:
            self.logger.error(f"Error fetching symbol map: {e}")
            # Return common mappings
            return {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana",
                "BNB": "binancecoin",
                "ADA": "cardano",
                "AVAX": "avalanche-2",
                "MATIC": "matic-network",
                "DOT": "polkadot",
                "LINK": "chainlink",
                "UNI": "uniswap",
                "ATOM": "cosmos",
                "ALGO": "algorand",
                "XRP": "ripple",
                "DOGE": "dogecoin",
                "SHIB": "shiba-inu"
            }
    
    def _symbol_to_id(self, symbol: str) -> Optional[str]:
        """Convert symbol to CoinGecko ID"""
        symbol_map = self._get_symbol_id_map()
        return symbol_map.get(symbol.upper())
    
    def fetch_price(self, symbol: str, timestamp: Optional[datetime] = None) -> Optional[float]:
        """Fetch current or historical price"""
        try:
            self._check_rate_limit()
            coin_id = self._symbol_to_id(symbol)
            if not coin_id:
                self.logger.warning(f"Symbol {symbol} not found in CoinGecko")
                return None
            
            headers = {}
            if self.api_key:
                headers["x-cg-demo-api-key"] = self.api_key
            
            if timestamp:
                # Fetch historical price
                url = f"{self.BASE_URL}/coins/{coin_id}/history"
                params = {"date": timestamp.strftime("%d-%m-%Y")}
                response = requests.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if "market_data" in data and "current_price" in data["market_data"]:
                    usd_price = data["market_data"]["current_price"].get("usd")
                    return float(usd_price) if usd_price else None
            else:
                # Fetch current price
                url = f"{self.BASE_URL}/simple/price"
                params = {"ids": coin_id, "vs_currencies": "usd"}
                response = requests.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if coin_id in data and "usd" in data[coin_id]:
                    return float(data[coin_id]["usd"])
            
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
            coin_id = self._symbol_to_id(symbol)
            if not coin_id:
                self.logger.warning(f"Symbol {symbol} not found in CoinGecko")
                return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            
            headers = {}
            if self.api_key:
                headers["x-cg-demo-api-key"] = self.api_key
            
            # Calculate days
            days = (end_date - start_date).days
            if days > 365:
                # CoinGecko free tier limits to 365 days
                days = 365
                start_date = end_date - timedelta(days=365)
            
            # Map interval
            if interval == "daily":
                url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
                params = {
                    "vs_currency": "usd",
                    "days": days,
                    "interval": "daily"
                }
            elif interval == "hourly":
                # For hourly, we need to use ohlc endpoint
                url = f"{self.BASE_URL}/coins/{coin_id}/ohlc"
                params = {
                    "vs_currency": "usd",
                    "days": min(days, 90)  # Max 90 days for hourly
                }
            else:
                # Default to daily
                url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
                params = {
                    "vs_currency": "usd",
                    "days": days,
                    "interval": "daily"
                }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Parse response based on endpoint
            if "prices" in data:
                # Market chart format
                prices = data["prices"]
                df = pd.DataFrame(prices, columns=["timestamp", "close"])
                df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
                df["open"] = df["close"]  # Approximate
                df["high"] = df["close"]
                df["low"] = df["close"]
                df["volume"] = data.get("total_volumes", [[0, 0]])[-1][1] if "total_volumes" in data else 0
            elif isinstance(data, list):
                # OHLC format: [[timestamp, open, high, low, close], ...]
                df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close"])
                df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
                df["volume"] = 0  # OHLC doesn't include volume
            else:
                return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            
            # Filter by date range
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
            
            # Select and reorder columns
            result = df[['date', 'open', 'high', 'low', 'close', 'volume']].copy()
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        return self.CRYPTO_SYMBOLS.copy()

