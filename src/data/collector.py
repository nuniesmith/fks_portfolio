"""
Background data collection service
Periodically collects data for enabled assets
"""
from typing import List, Optional
from datetime import datetime, timedelta
import time
import threading
from loguru import logger

from .manager import DataManager
from .asset_config import AssetConfigManager, AssetConfig


class DataCollector:
    """Background service for collecting data over time"""
    
    def __init__(
        self,
        data_manager: Optional[DataManager] = None,
        config_manager: Optional[AssetConfigManager] = None,
        collection_interval_hours: int = 24,
        enabled: bool = True
    ):
        """
        Initialize data collector
        
        Args:
            data_manager: DataManager instance (creates new if None)
            config_manager: AssetConfigManager instance (creates new if None)
            collection_interval_hours: Hours between collection runs
            enabled: Start collection immediately
        """
        self.data_manager = data_manager or DataManager()
        self.config_manager = config_manager or AssetConfigManager()
        self.collection_interval_hours = collection_interval_hours
        self.enabled = enabled
        self.logger = logger.bind(component="DataCollector")
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start background collection thread"""
        if self._running:
            self.logger.warning("Collector already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._collection_loop, daemon=True)
        self._thread.start()
        self.logger.info("Data collector started")
    
    def stop(self):
        """Stop background collection"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self.logger.info("Data collector stopped")
    
    def _collection_loop(self):
        """Main collection loop"""
        while self._running:
            try:
                self._collect_all_enabled()
                
                # Wait for next collection interval
                wait_seconds = self.collection_interval_hours * 3600
                for _ in range(wait_seconds):
                    if not self._running:
                        break
                    time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in collection loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _collect_all_enabled(self):
        """Collect data for all enabled assets"""
        assets = self.config_manager.get_enabled_assets()
        self.logger.info(f"Starting collection for {len(assets)} enabled assets")
        
        for asset_config in assets:
            if not self._running:
                break
            
            try:
                self._collect_asset(asset_config)
            except Exception as e:
                self.logger.error(f"Error collecting {asset_config.symbol}: {e}")
    
    def _collect_asset(self, asset_config: AssetConfig):
        """Collect data for a single asset"""
        symbol = asset_config.symbol
        self.logger.info(f"Collecting data for {symbol}")
        
        # Determine date range
        end_date = datetime.now()
        
        # If we have last_collected, start from there
        if asset_config.last_collected:
            start_date = asset_config.last_collected
        else:
            # First collection: get 1 year of history
            start_date = end_date - timedelta(days=365)
        
        # Fetch historical data
        historical_data = self.data_manager.fetch_historical_prices(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=asset_config.collection_interval,
            use_cache=False,  # Always fetch fresh data
            use_storage=True  # Store in database
        )
        
        if not historical_data.empty:
            self.logger.success(
                f"Collected {len(historical_data)} records for {symbol} "
                f"({start_date.date()} to {end_date.date()})"
            )
            # Update last collected timestamp
            self.config_manager.update_last_collected(symbol, end_date)
        else:
            self.logger.warning(f"No data collected for {symbol}")
    
    def collect_now(self, symbols: Optional[List[str]] = None):
        """
        Trigger immediate collection
        
        Args:
            symbols: Optional list of symbols to collect (all enabled if None)
        """
        if symbols:
            assets = [
                self.config_manager.get_asset_config(s) 
                for s in symbols 
                if self.config_manager.get_asset_config(s) and self.config_manager.get_asset_config(s).enabled
            ]
        else:
            assets = self.config_manager.get_enabled_assets()
        
        self.logger.info(f"Manual collection triggered for {len(assets)} assets")
        for asset_config in assets:
            try:
                self._collect_asset(asset_config)
            except Exception as e:
                self.logger.error(f"Error collecting {asset_config.symbol}: {e}")
    
    def get_collection_status(self) -> dict:
        """Get status of data collection"""
        assets = self.config_manager.get_enabled_assets()
        status = {
            "running": self._running,
            "enabled_assets": len(assets),
            "collection_interval_hours": self.collection_interval_hours,
            "assets": []
        }
        
        for asset_config in assets:
            status["assets"].append({
                "symbol": asset_config.symbol,
                "priority": asset_config.priority,
                "last_collected": asset_config.last_collected.isoformat() if asset_config.last_collected else None,
                "adapters": asset_config.adapters
            })
        
        return status

