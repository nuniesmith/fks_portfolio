"""
Signal Service - Ingests and processes signals from signals directory
Integrates with portfolio service and provides signal management
"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from ...assets.registry import AssetCategory, get_asset
from ...assets.signal_utils import SignalLotSizeCalculator, EntryPriceManager, LotSizeCalculation


class SignalService:
    """Service for managing and processing trading signals"""
    
    def __init__(
        self,
        signals_dir: str = "/home/jordan/Nextcloud/code/repos/fks/signals",
        account_balance_usd: float = 10000.0,
        risk_per_trade_pct: float = 1.0
    ):
        """
        Initialize signal service
        
        Args:
            signals_dir: Directory containing signal JSON files
            account_balance_usd: Account balance for lot size calculations
            risk_per_trade_pct: Risk per trade percentage
        """
        self.signals_dir = Path(signals_dir)
        self.lot_calculator = SignalLotSizeCalculator(
            account_balance_usd=account_balance_usd,
            risk_per_trade_pct=risk_per_trade_pct
        )
        self.entry_manager = EntryPriceManager()
        self.logger = logger.bind(component="SignalService")
    
    def load_signals_for_date(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Load signals for a specific date
        
        Args:
            date: Date string in format YYYYMMDD (default: today)
        
        Returns:
            Dictionary with signals by category
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        
        signals = {
            "scalp": [],
            "swing": [],
            "long_term": [],
            "date": date
        }
        
        # Load category-specific signal files
        for category in ["scalp", "swing", "long_term"]:
            signal_file = self.signals_dir / f"signals_{category}_{date}.json"
            
            if signal_file.exists():
                try:
                    with open(signal_file, 'r') as f:
                        category_signals = json.load(f)
                        # Handle both single signal and list of signals
                        if isinstance(category_signals, list):
                            signals[category] = category_signals
                        else:
                            signals[category] = [category_signals]
                except Exception as e:
                    self.logger.error(f"Error loading {signal_file}: {e}")
        
        return signals
    
    def load_daily_summary(self, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Load daily signals summary
        
        Args:
            date: Date string in format YYYYMMDD (default: today)
        
        Returns:
            Summary dictionary or None
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        
        summary_file = self.signals_dir / f"daily_signals_summary_{date}.json"
        
        if summary_file.exists():
            try:
                with open(summary_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading summary: {e}")
        
        return None
    
    def load_performance(self, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Load performance data
        
        Args:
            date: Date string in format YYYYMMDD (default: today)
        
        Returns:
            Performance dictionary or None
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        
        perf_file = self.signals_dir / "performance" / f"performance_{date}.json"
        
        if perf_file.exists():
            try:
                with open(perf_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading performance: {e}")
        
        return None
    
    def enrich_signal_with_lot_size(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich signal with lot size calculations
        
        Args:
            signal: Signal dictionary
        
        Returns:
            Enriched signal dictionary
        """
        try:
            # Calculate lot size
            lot_calc = self.lot_calculator.calculate_for_signal(signal)
            
            # Get asset info
            asset = get_asset(signal.get("symbol", ""))
            asset_category = asset.category if asset else AssetCategory.CRYPTO
            
            # Calculate entry price info for next day
            entry_info = self.entry_manager.calculate_entry_price_for_next_day(
                current_price=signal.get("entry_price", 0),
                signal=signal,
                asset_category=asset_category
            )
            
            # Add lot size and entry info to signal
            signal["lot_size"] = lot_calc.to_dict()
            signal["entry_planning"] = entry_info
            signal["asset_category"] = asset_category.value if asset else "crypto"
            signal["is_crypto"] = asset_category == AssetCategory.CRYPTO if asset else True
            
            return signal
        
        except Exception as e:
            self.logger.error(f"Error enriching signal: {e}")
            return signal
    
    def get_trading_day_signals(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all signals for trading day planning
        
        Args:
            date: Date string in format YYYYMMDD (default: today)
        
        Returns:
            Dictionary with enriched signals ready for trading day
        """
        signals = self.load_signals_for_date(date)
        summary = self.load_daily_summary(date)
        performance = self.load_performance(date)
        
        # Enrich all signals with lot sizes and entry planning
        enriched_signals = {}
        for category, category_signals in signals.items():
            if category == "date":
                continue
            
            enriched_signals[category] = [
                self.enrich_signal_with_lot_size(signal)
                for signal in category_signals
            ]
        
        return {
            "date": signals.get("date", date),
            "signals": enriched_signals,
            "summary": summary,
            "performance": performance,
            "generated_at": datetime.now().isoformat()
        }
    
    def get_signal_by_id(
        self,
        signal_id: str,
        date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific signal by ID (symbol + category + timestamp)
        
        Args:
            signal_id: Signal identifier
            date: Date string (default: today)
        
        Returns:
            Signal dictionary or None
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        
        signals = self.load_signals_for_date(date)
        
        # Search through all categories
        for category, category_signals in signals.items():
            if category == "date":
                continue
            
            for signal in category_signals:
                # Create ID from symbol + category + timestamp
                sig_id = f"{signal.get('symbol')}_{category}_{signal.get('timestamp', '')}"
                if sig_id == signal_id:
                    return self.enrich_signal_with_lot_size(signal)
        
        return None
    
    def get_signals_by_symbol(
        self,
        symbol: str,
        date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all signals for a specific symbol
        
        Args:
            symbol: Asset symbol
            date: Date string (default: today)
        
        Returns:
            List of signal dictionaries
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        
        signals = self.load_signals_for_date(date)
        matching_signals = []
        
        for category, category_signals in signals.items():
            if category == "date":
                continue
            
            for signal in category_signals:
                if signal.get("symbol", "").upper() == symbol.upper():
                    matching_signals.append(
                        self.enrich_signal_with_lot_size(signal)
                    )
        
        return matching_signals

