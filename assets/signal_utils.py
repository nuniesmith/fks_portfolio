"""
Signal Utilities - Lot size calculation and entry price management
Handles lot size calculations for crypto and traditional markets
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import pytz

from .registry import Asset, AssetCategory, get_asset


@dataclass
class LotSizeCalculation:
    """Lot size calculation result"""
    symbol: str
    entry_price: float
    risk_amount_usd: float  # Risk amount in USD
    position_size_usd: float  # Total position size in USD
    position_size_tokens: Optional[float] = None  # For crypto: number of tokens
    position_size_units: Optional[float] = None  # For forex/futures: number of units
    lot_size: Optional[float] = None  # Standard lot size if applicable
    leverage: Optional[float] = None  # Leverage if applicable
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "entry_price": self.entry_price,
            "risk_amount_usd": self.risk_amount_usd,
            "position_size_usd": self.position_size_usd,
            "position_size_tokens": self.position_size_tokens,
            "position_size_units": self.position_size_units,
            "lot_size": self.lot_size,
            "leverage": self.leverage
        }


class SignalLotSizeCalculator:
    """Calculate lot sizes for trading signals"""
    
    def __init__(self, account_balance_usd: float = 10000.0, risk_per_trade_pct: float = 1.0):
        """
        Initialize calculator
        
        Args:
            account_balance_usd: Account balance in USD
            risk_per_trade_pct: Risk per trade as percentage (default: 1%)
        """
        self.account_balance_usd = account_balance_usd
        self.risk_per_trade_pct = risk_per_trade_pct
    
    def calculate_lot_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        signal_type: str = "BUY"
    ) -> LotSizeCalculation:
        """
        Calculate lot size for a signal
        
        Args:
            symbol: Asset symbol (e.g., BTCUSDT, EURUSD)
            entry_price: Entry price
            stop_loss: Stop loss price
            signal_type: BUY or SELL
        
        Returns:
            LotSizeCalculation with position sizes
        """
        # Get asset info
        asset = get_asset(symbol)
        if not asset:
            # Default to crypto if not found
            asset = Asset(
                symbol=symbol,
                name=symbol,
                category=AssetCategory.CRYPTO,
                asset_type=None,  # Will be determined
                exchange="unknown"
            )
        
        # Calculate risk amount
        risk_amount_usd = self.account_balance_usd * (self.risk_per_trade_pct / 100)
        
        # Calculate price difference (risk per unit)
        if signal_type.upper() == "BUY":
            price_diff = abs(entry_price - stop_loss)
        else:  # SELL
            price_diff = abs(stop_loss - entry_price)
        
        if price_diff == 0:
            price_diff = entry_price * 0.01  # Default 1% if no stop loss
        
        # Calculate position size
        if asset.category == AssetCategory.CRYPTO:
            # Crypto: calculate number of tokens
            position_size_tokens = risk_amount_usd / price_diff
            position_size_usd = position_size_tokens * entry_price
            
            return LotSizeCalculation(
                symbol=symbol,
                entry_price=entry_price,
                risk_amount_usd=risk_amount_usd,
                position_size_usd=position_size_usd,
                position_size_tokens=position_size_tokens,
                position_size_units=None,
                lot_size=None,
                leverage=None
            )
        
        elif asset.category == AssetCategory.FOREX:
            # Forex: calculate lot size
            # Standard lot = 100,000 units
            # Mini lot = 10,000 units
            # Micro lot = 1,000 units
            
            # Calculate units based on risk
            units = risk_amount_usd / price_diff
            
            # Determine lot size (prefer micro lots for smaller accounts)
            if units >= 100000:
                lot_size = units / 100000  # Standard lots
            elif units >= 10000:
                lot_size = units / 10000  # Mini lots
            else:
                lot_size = units / 1000  # Micro lots
            
            position_size_usd = units * entry_price
            
            return LotSizeCalculation(
                symbol=symbol,
                entry_price=entry_price,
                risk_amount_usd=risk_amount_usd,
                position_size_usd=position_size_usd,
                position_size_tokens=None,
                position_size_units=units,
                lot_size=lot_size,
                leverage=None
            )
        
        else:  # FUTURES or other
            # Futures: similar to forex but with contract multipliers
            # For now, treat similar to forex
            units = risk_amount_usd / price_diff
            position_size_usd = units * entry_price
            
            return LotSizeCalculation(
                symbol=symbol,
                entry_price=entry_price,
                risk_amount_usd=risk_amount_usd,
                position_size_usd=position_size_usd,
                position_size_tokens=None,
                position_size_units=units,
                lot_size=None,
                leverage=None
            )
    
    def calculate_for_signal(self, signal: Dict[str, Any]) -> LotSizeCalculation:
        """
        Calculate lot size from a signal dictionary
        
        Args:
            signal: Signal dictionary with entry_price, stop_loss, symbol, signal_type
        
        Returns:
            LotSizeCalculation
        """
        return self.calculate_lot_size(
            symbol=signal.get("symbol"),
            entry_price=signal.get("entry_price"),
            stop_loss=signal.get("stop_loss"),
            signal_type=signal.get("signal_type", "BUY")
        )


class EntryPriceManager:
    """Manage entry prices for next trading day"""
    
    def __init__(self, market_timezone: str = "America/New_York"):
        """
        Initialize entry price manager
        
        Args:
            market_timezone: Timezone for market hours (default: US Eastern)
        """
        self.market_tz = pytz.timezone(market_timezone)
        self.crypto_tz = pytz.UTC  # Crypto is 24/7
    
    def get_next_trading_day(self, asset_category: AssetCategory) -> datetime:
        """
        Get next trading day datetime
        
        Args:
            asset_category: Asset category (crypto, forex, futures)
        
        Returns:
            Next trading day datetime
        """
        now = datetime.now(pytz.UTC)
        
        if asset_category == AssetCategory.CRYPTO:
            # Crypto: next day is just +1 day (24/7)
            next_day = now + timedelta(days=1)
            # Set to market open time (00:00 UTC or preferred time)
            return next_day.replace(hour=0, minute=0, second=0, microsecond=0)
        
        else:
            # Traditional markets: next business day at market open
            # Market opens at 9:30 AM ET (13:30 UTC during EST, 14:30 UTC during EDT)
            next_day = now.astimezone(self.market_tz)
            
            # If it's after market close (4:00 PM ET), move to next day
            if next_day.hour >= 16:
                next_day += timedelta(days=1)
            
            # Skip weekends
            while next_day.weekday() >= 5:  # Saturday = 5, Sunday = 6
                next_day += timedelta(days=1)
            
            # Set to market open (9:30 AM ET)
            next_day = next_day.replace(hour=9, minute=30, second=0, microsecond=0)
            
            # Convert back to UTC
            return next_day.astimezone(pytz.UTC)
    
    def calculate_entry_price_for_next_day(
        self,
        current_price: float,
        signal: Dict[str, Any],
        asset_category: AssetCategory
    ) -> Dict[str, Any]:
        """
        Calculate entry price for next trading day
        
        Args:
            current_price: Current market price
            signal: Signal dictionary
            asset_category: Asset category
        
        Returns:
            Dictionary with entry price info for next day
        """
        next_trading_day = self.get_next_trading_day(asset_category)
        
        # For crypto: entry price is current price (can enter anytime)
        # For traditional markets: might want to use pre-market or limit order
        
        if asset_category == AssetCategory.CRYPTO:
            # Crypto: use current price, but note it's 24/7
            entry_price = current_price
            entry_strategy = "market"  # Can enter immediately
            entry_note = "Crypto markets are 24/7 - can enter at any time"
        else:
            # Traditional markets: use current price but plan for market open
            entry_price = current_price
            entry_strategy = "limit"  # Recommend limit order
            entry_note = f"Place limit order before market open at {next_trading_day.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        
        return {
            "current_price": current_price,
            "entry_price": entry_price,
            "next_trading_day": next_trading_day.isoformat(),
            "entry_strategy": entry_strategy,
            "entry_note": entry_note,
            "time_until_open": str(next_trading_day - datetime.now(pytz.UTC)) if asset_category != AssetCategory.CRYPTO else "N/A (24/7)"
        }
    
    def should_wait_for_market_open(
        self,
        asset_category: AssetCategory
    ) -> bool:
        """
        Check if we should wait for market open
        
        Args:
            asset_category: Asset category
        
        Returns:
            True if should wait, False if can enter now
        """
        if asset_category == AssetCategory.CRYPTO:
            return False  # Crypto is 24/7
        
        # For traditional markets, check if market is open
        now = datetime.now(self.market_tz)
        
        # Market hours: 9:30 AM - 4:00 PM ET, Monday-Friday
        if now.weekday() >= 5:  # Weekend
            return True
        
        if now.hour < 9 or (now.hour == 9 and now.minute < 30):
            return True  # Before market open
        
        if now.hour >= 16:
            return True  # After market close
        
        return False  # Market is open

