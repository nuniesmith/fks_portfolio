"""
Data Fetchers for Portfolio Platform
Fetches price data from various sources (CoinGecko, Yahoo Finance, etc.)
"""
import os
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from loguru import logger
from dotenv import load_dotenv

load_dotenv()


class PriceFetcher:
    """Base class for fetching price data"""
    
    def __init__(self):
        self.logger = logger
    
    def fetch_price(self, symbol: str) -> Optional[float]:
        """Fetch current price for a symbol"""
        raise NotImplementedError
    
    def fetch_historical(self, symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
        """Fetch historical price data"""
        raise NotImplementedError


class YahooFinanceFetcher(PriceFetcher):
    """Fetch data from Yahoo Finance (free, no API key needed)"""
    
    def fetch_price(self, symbol: str) -> Optional[float]:
        """Fetch current price"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                return float(data['Close'].iloc[-1])
            return None
        except Exception as e:
            self.logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def fetch_historical(self, symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
        """Fetch historical OHLCV data"""
        try:
            ticker = yf.Ticker(symbol)
            period = "1y" if days >= 365 else f"{days}d"
            data = ticker.history(period=period)
            
            if data.empty:
                self.logger.warning(f"No data returned for {symbol}")
                return None
            
            # Rename columns to standard format
            data.columns = [col.lower() for col in data.columns]
            return data
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None


class CryptoFetcher(PriceFetcher):
    """Fetch crypto data (using Yahoo Finance for now, can extend to CoinGecko)"""
    
    def fetch_price(self, symbol: str) -> Optional[float]:
        """Fetch crypto price (e.g., BTC-USD)"""
        # Yahoo Finance uses format like BTC-USD for crypto
        yahoo_symbol = f"{symbol}-USD" if not symbol.endswith("-USD") else symbol
        fetcher = YahooFinanceFetcher()
        return fetcher.fetch_price(yahoo_symbol)
    
    def fetch_historical(self, symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
        """Fetch historical crypto data"""
        yahoo_symbol = f"{symbol}-USD" if not symbol.endswith("-USD") else symbol
        fetcher = YahooFinanceFetcher()
        return fetcher.fetch_historical(yahoo_symbol, days)


def get_fetcher(asset_type: str = "stock") -> PriceFetcher:
    """Factory function to get appropriate fetcher"""
    if asset_type.lower() in ["crypto", "cryptocurrency"]:
        return CryptoFetcher()
    else:
        return YahooFinanceFetcher()


# Test function
if __name__ == "__main__":
    logger.info("Testing data fetchers...")
    
    # Test BTC price fetch
    btc_fetcher = CryptoFetcher()
    btc_price = btc_fetcher.fetch_price("BTC")
    logger.info(f"BTC Price: ${btc_price:,.2f}" if btc_price else "Failed to fetch BTC price")
    
    # Test stock price fetch
    stock_fetcher = YahooFinanceFetcher()
    spy_price = stock_fetcher.fetch_price("SPY")
    logger.info(f"SPY Price: ${spy_price:,.2f}" if spy_price else "Failed to fetch SPY price")

