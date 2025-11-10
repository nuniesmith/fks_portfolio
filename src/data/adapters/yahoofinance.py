"""
Yahoo Finance data adapter
Free, no API key required
"""
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from loguru import logger

from .base import BaseDataAdapter


class YahooFinanceAdapter(BaseDataAdapter):
    """Yahoo Finance adapter for stocks and some crypto"""
    
    # Supported symbols (stocks and ETFs)
    STOCK_SYMBOLS = [
        "SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
        "NVDA", "META", "NFLX", "DIS", "JPM", "V", "MA", "WMT"
    ]
    
    # Some crypto symbols available on Yahoo Finance
    CRYPTO_SYMBOLS = [
        "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "ADA-USD"
    ]
    
    def __init__(self, rate_limit_per_minute: int = 200):
        """
        Initialize Yahoo Finance adapter
        
        Args:
            rate_limit_per_minute: Rate limit (Yahoo Finance is lenient, default 200)
        """
        super().__init__("YahooFinance", rate_limit_per_minute)
        self.logger = logger.bind(adapter="YahooFinance")
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for Yahoo Finance (add -USD for crypto if needed)"""
        # If it's a known crypto symbol without suffix, add -USD
        crypto_symbols = ["BTC", "ETH", "SOL", "BNB", "ADA"]
        if symbol in crypto_symbols:
            return f"{symbol}-USD"
        return symbol
    
    def fetch_price(self, symbol: str, timestamp: Optional[datetime] = None) -> Optional[float]:
        """Fetch current or historical price"""
        try:
            self._check_rate_limit()
            normalized_symbol = self._normalize_symbol(symbol)
            ticker = yf.Ticker(normalized_symbol)
            
            if timestamp:
                # Fetch historical price at specific date
                hist = ticker.history(start=timestamp - timedelta(days=1), end=timestamp + timedelta(days=1))
                if not hist.empty:
                    return float(hist['Close'].iloc[0])
            else:
                # Fetch current price
                info = ticker.info
                if 'currentPrice' in info:
                    return float(info['currentPrice'])
                elif 'regularMarketPrice' in info:
                    return float(info['regularMarketPrice'])
                elif 'previousClose' in info:
                    return float(info['previousClose'])
            
            # Fallback: use history
            hist = ticker.history(period="1d")
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
            
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
            normalized_symbol = self._normalize_symbol(symbol)
            ticker = yf.Ticker(normalized_symbol)
            
            # Map interval to yfinance format
            interval_map = {
                "daily": "1d",
                "hourly": "1h",
                "minute": "1m"
            }
            yf_interval = interval_map.get(interval, "1d")
            
            # Fetch data
            hist = ticker.history(
                start=start_date,
                end=end_date,
                interval=yf_interval
            )
            
            if hist.empty:
                self.logger.warning(f"No data found for {symbol} from {start_date} to {end_date}")
                return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            
            # Normalize column names
            hist = hist.reset_index()
            hist.columns = [col.lower().replace(' ', '_') for col in hist.columns]
            
            # Rename date column
            if 'date' in hist.columns:
                hist = hist.rename(columns={'date': 'date'})
            elif 'datetime' in hist.columns:
                hist = hist.rename(columns={'datetime': 'date'})
            
            # Ensure we have required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in hist.columns:
                    if col == 'volume':
                        hist[col] = 0
                    else:
                        hist[col] = hist.get('close', 0)
            
            # Select and reorder columns
            result = hist[['date'] + required_cols].copy()
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        # Return base symbols (without -USD suffix for crypto)
        crypto_base = [s.replace("-USD", "") for s in self.CRYPTO_SYMBOLS]
        return self.STOCK_SYMBOLS + crypto_base

