"""
BTC Conversion Service
Converts all asset values to BTC equivalents for unified tracking
"""
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from .manager import DataManager
from .cache import DataCache


class BTCConverter:
    """Converts asset values to/from BTC"""
    
    def __init__(
        self,
        data_manager: Optional[DataManager] = None,
        cache: Optional[DataCache] = None
    ):
        """
        Initialize BTC converter
        
        Args:
            data_manager: DataManager instance for fetching BTC prices
            cache: Optional cache for BTC prices
        """
        self.data_manager = data_manager or DataManager()
        self.cache = cache or DataCache(ttl_seconds=300)  # 5 minute cache for BTC prices
        self.logger = logger.bind(component="BTCConverter")
        self._btc_symbol = "BTC"
    
    def get_btc_price(
        self,
        timestamp: Optional[datetime] = None,
        use_cache: bool = True
    ) -> Optional[float]:
        """
        Get BTC price in USD
        
        Args:
            timestamp: Optional timestamp for historical price
            use_cache: Use cache if available
        
        Returns:
            BTC price in USD or None
        """
        # Check cache first
        if use_cache:
            cached_price = self.cache.get("btc_converter", "BTC_USD", timestamp)
            if cached_price is not None:
                return cached_price
        
        # Fetch from data manager (prefer Binance - free, no key needed)
        try:
            price = self.data_manager.fetch_price(
                self._btc_symbol,
                timestamp,
                preferred_adapters=["binance", "coingecko", "yahoofinance"]
            )
            
            if price is not None and use_cache:
                self.cache.set("btc_converter", "BTC_USD", price, timestamp)
            
            return price
        except Exception as e:
            self.logger.error(f"Error fetching BTC price: {e}")
            return None
    
    def to_btc(
        self,
        amount: float,
        asset_symbol: str,
        timestamp: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Convert asset amount to BTC
        
        Args:
            amount: Amount of asset
            asset_symbol: Asset symbol (e.g., "ETH", "SPY")
            timestamp: Optional timestamp for historical conversion
        
        Returns:
            Amount in BTC or None
        """
        if asset_symbol.upper() == "BTC":
            return amount
        
        # Get asset price in USD
        asset_price = self.data_manager.fetch_price(asset_symbol, timestamp)
        if asset_price is None:
            self.logger.warning(f"Could not fetch price for {asset_symbol}")
            return None
        
        # Get BTC price in USD
        btc_price = self.get_btc_price(timestamp)
        if btc_price is None:
            self.logger.warning("Could not fetch BTC price")
            return None
        
        # Convert: (amount * asset_price) / btc_price
        usd_value = amount * asset_price
        btc_value = usd_value / btc_price
        
        return btc_value
    
    def from_btc(
        self,
        btc_amount: float,
        target_symbol: str,
        timestamp: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Convert BTC amount to target asset
        
        Args:
            btc_amount: Amount in BTC
            target_symbol: Target asset symbol
            timestamp: Optional timestamp for historical conversion
        
        Returns:
            Amount of target asset or None
        """
        if target_symbol.upper() == "BTC":
            return btc_amount
        
        # Get BTC price in USD
        btc_price = self.get_btc_price(timestamp)
        if btc_price is None:
            self.logger.warning("Could not fetch BTC price")
            return None
        
        # Get target asset price in USD
        target_price = self.data_manager.fetch_price(target_symbol, timestamp)
        if target_price is None:
            self.logger.warning(f"Could not fetch price for {target_symbol}")
            return None
        
        # Convert: (btc_amount * btc_price) / target_price
        usd_value = btc_amount * btc_price
        target_amount = usd_value / target_price
        
        return target_amount
    
    def convert_portfolio_to_btc(
        self,
        holdings: Dict[str, float],
        timestamp: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Convert entire portfolio holdings to BTC
        
        Args:
            holdings: Dictionary mapping symbol to amount (e.g., {"BTC": 1.5, "ETH": 10})
            timestamp: Optional timestamp for historical conversion
        
        Returns:
            Dictionary mapping symbol to BTC value
        """
        btc_holdings = {}
        total_btc = 0.0
        
        for symbol, amount in holdings.items():
            btc_value = self.to_btc(amount, symbol, timestamp)
            if btc_value is not None:
                btc_holdings[symbol] = btc_value
                total_btc += btc_value
            else:
                self.logger.warning(f"Could not convert {symbol} to BTC")
                btc_holdings[symbol] = 0.0
        
        btc_holdings["_total"] = total_btc
        return btc_holdings
    
    def get_btc_allocation(
        self,
        holdings: Dict[str, float],
        timestamp: Optional[datetime] = None
    ) -> float:
        """
        Calculate BTC allocation percentage
        
        Args:
            holdings: Dictionary mapping symbol to amount
            timestamp: Optional timestamp
        
        Returns:
            BTC allocation as decimal (0.0 to 1.0)
        """
        btc_holdings = self.convert_portfolio_to_btc(holdings, timestamp)
        total_btc = btc_holdings.get("_total", 0.0)
        
        if total_btc == 0:
            return 0.0
        
        btc_amount = holdings.get("BTC", 0.0)
        btc_value = self.to_btc(btc_amount, "BTC", timestamp) if btc_amount > 0 else 0.0
        
        if btc_value is None:
            btc_value = btc_amount  # BTC is already in BTC
        
        return btc_value / total_btc if total_btc > 0 else 0.0
    
    def calculate_portfolio_value_btc(
        self,
        holdings: Dict[str, float],
        timestamp: Optional[datetime] = None
    ) -> float:
        """
        Calculate total portfolio value in BTC
        
        Args:
            holdings: Dictionary mapping symbol to amount
            timestamp: Optional timestamp
        
        Returns:
            Total portfolio value in BTC
        """
        btc_holdings = self.convert_portfolio_to_btc(holdings, timestamp)
        return btc_holdings.get("_total", 0.0)
    
    def get_btc_denominated_returns(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.Series:
        """
        Calculate asset returns denominated in BTC
        
        Args:
            symbol: Asset symbol
            start_date: Start date
            end_date: End date
        
        Returns:
            Series of BTC-denominated returns
        """
        # Fetch asset prices
        asset_prices = self.data_manager.fetch_historical_prices(
            symbol, start_date, end_date, interval="daily"
        )
        
        if asset_prices.empty:
            return pd.Series()
        
        # Fetch BTC prices for same period
        btc_prices = self.data_manager.fetch_historical_prices(
            "BTC", start_date, end_date, interval="daily"
        )
        
        if btc_prices.empty:
            return pd.Series()
        
        # Align dates
        common_dates = asset_prices["date"].intersection(btc_prices["date"])
        if len(common_dates) == 0:
            return pd.Series()
        
        # Calculate BTC-denominated prices
        asset_close = asset_prices.set_index("date")["close"]
        btc_close = btc_prices.set_index("date")["close"]
        
        # Convert asset prices to BTC terms
        btc_denominated = asset_close / btc_close
        
        # Calculate returns
        returns = btc_denominated.pct_change().dropna()
        
        return returns
    
    def get_conversion_rate(
        self,
        from_symbol: str,
        to_symbol: str,
        timestamp: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Get conversion rate between two assets
        
        Args:
            from_symbol: Source asset symbol
            to_symbol: Target asset symbol
            timestamp: Optional timestamp
        
        Returns:
            Conversion rate (how many 'to' per 1 'from')
        """
        if from_symbol.upper() == to_symbol.upper():
            return 1.0
        
        # Convert through BTC
        btc_amount = self.to_btc(1.0, from_symbol, timestamp)
        if btc_amount is None:
            return None
        
        target_amount = self.from_btc(btc_amount, to_symbol, timestamp)
        return target_amount

