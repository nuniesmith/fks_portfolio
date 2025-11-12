"""
Asset configuration and enablement
Manages which assets are enabled for data collection
"""
from typing import List, Dict, Optional, Set
from datetime import datetime
import json
from pathlib import Path
from loguru import logger
from dataclasses import dataclass, asdict


@dataclass
class AssetConfig:
    """Configuration for a single asset"""
    symbol: str
    enabled: bool = True
    adapters: List[str] = None  # Preferred adapters in order
    collection_interval: str = "daily"  # daily, hourly, minute
    last_collected: Optional[datetime] = None
    priority: int = 1  # 1=high, 2=medium, 3=low
    
    def __post_init__(self):
        if self.adapters is None:
            self.adapters = []


class AssetConfigManager:
    """Manages asset configurations"""
    
    def __init__(self, config_file: str = "data/config/assets.json"):
        """
        Initialize asset config manager
        
        Args:
            config_file: Path to JSON config file
        """
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logger.bind(component="AssetConfigManager")
        self._assets: Dict[str, AssetConfig] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    for symbol, config_data in data.items():
                        # Convert last_collected string to datetime if present
                        if "last_collected" in config_data and config_data["last_collected"]:
                            config_data["last_collected"] = datetime.fromisoformat(
                                config_data["last_collected"]
                            )
                        self._assets[symbol] = AssetConfig(**config_data)
                self.logger.info(f"Loaded {len(self._assets)} asset configurations")
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
                self._assets = {}
        else:
            # Create default config
            self._create_default_config()
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            data = {}
            for symbol, config in self._assets.items():
                config_dict = asdict(config)
                # Convert datetime to ISO string
                if config_dict.get("last_collected"):
                    config_dict["last_collected"] = config_dict["last_collected"].isoformat()
                data[symbol] = config_dict
            
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)
            self.logger.debug(f"Saved {len(self._assets)} asset configurations")
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def _create_default_config(self):
        """Create default configuration with common assets"""
        default_assets = [
            # High priority
            AssetConfig("BTC", enabled=True, priority=1, adapters=["binance", "coingecko", "coinmarketcap"]),
            AssetConfig("ETH", enabled=True, priority=1, adapters=["binance", "coingecko", "coinmarketcap"]),
            AssetConfig("SPY", enabled=True, priority=1, adapters=["yahoofinance", "polygon", "alphavantage"]),
            
            # Medium priority
            AssetConfig("SOL", enabled=True, priority=2, adapters=["binance", "coingecko"]),
            AssetConfig("BNB", enabled=True, priority=2, adapters=["binance", "coingecko"]),
            AssetConfig("QQQ", enabled=True, priority=2, adapters=["yahoofinance", "polygon"]),
            
            # Lower priority
            AssetConfig("ADA", enabled=True, priority=3, adapters=["binance", "coingecko"]),
            AssetConfig("AVAX", enabled=True, priority=3, adapters=["binance", "coingecko"]),
            AssetConfig("MATIC", enabled=True, priority=3, adapters=["binance", "coingecko"]),
        ]
        
        for asset in default_assets:
            self._assets[asset.symbol] = asset
        
        self._save_config()
        self.logger.info("Created default asset configuration")
    
    def get_enabled_assets(self, priority: Optional[int] = None) -> List[AssetConfig]:
        """
        Get list of enabled assets
        
        Args:
            priority: Optional priority filter (1=high, 2=medium, 3=low)
        
        Returns:
            List of enabled asset configs
        """
        assets = [config for config in self._assets.values() if config.enabled]
        if priority:
            assets = [a for a in assets if a.priority == priority]
        return sorted(assets, key=lambda x: (x.priority, x.symbol))
    
    def enable_asset(self, symbol: str, adapters: Optional[List[str]] = None):
        """Enable asset for collection"""
        if symbol not in self._assets:
            self._assets[symbol] = AssetConfig(
                symbol=symbol,
                enabled=True,
                adapters=adapters or []
            )
        else:
            self._assets[symbol].enabled = True
            if adapters:
                self._assets[symbol].adapters = adapters
        self._save_config()
        self.logger.info(f"Enabled asset: {symbol}")
    
    def disable_asset(self, symbol: str):
        """Disable asset for collection"""
        if symbol in self._assets:
            self._assets[symbol].enabled = False
            self._save_config()
            self.logger.info(f"Disabled asset: {symbol}")
    
    def update_last_collected(self, symbol: str, timestamp: datetime):
        """Update last collection timestamp"""
        if symbol in self._assets:
            self._assets[symbol].last_collected = timestamp
            self._save_config()
    
    def get_asset_config(self, symbol: str) -> Optional[AssetConfig]:
        """Get configuration for specific asset"""
        return self._assets.get(symbol)
    
    def add_asset(self, config: AssetConfig):
        """Add or update asset configuration"""
        self._assets[config.symbol] = config
        self._save_config()
    
    def get_all_symbols(self) -> Set[str]:
        """Get all configured symbols"""
        return set(self._assets.keys())

