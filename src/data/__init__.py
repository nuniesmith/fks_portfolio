"""Data module"""
# Legacy fetchers (kept for backward compatibility)
from .fetchers import PriceFetcher, YahooFinanceFetcher, CryptoFetcher, get_fetcher

# New adapter-based system
from .adapters import BaseDataAdapter, YahooFinanceAdapter, CoinGeckoAdapter
from .cache import DataCache
from .storage import DataStorage
from .manager import DataManager
from .asset_config import AssetConfig, AssetConfigManager
from .collector import DataCollector
from .btc_converter import BTCConverter

__all__ = [
    # Legacy
    "PriceFetcher",
    "YahooFinanceFetcher",
    "CryptoFetcher",
    "get_fetcher",
    # New
    "BaseDataAdapter",
    "YahooFinanceAdapter",
    "CoinGeckoAdapter",
    "DataCache",
    "DataStorage",
    "DataManager",
    "AssetConfig",
    "AssetConfigManager",
    "DataCollector",
    "BTCConverter",
]

