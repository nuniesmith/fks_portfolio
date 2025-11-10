"""
Caching layer for data fetchers
Supports both in-memory and file-based caching
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json
import pickle
from pathlib import Path
from loguru import logger
import hashlib


class DataCache:
    """Simple caching layer for price data"""
    
    def __init__(self, cache_dir: Optional[str] = None, ttl_seconds: int = 300):
        """
        Initialize cache
        
        Args:
            cache_dir: Directory for file cache (None = in-memory only)
            ttl_seconds: Time-to-live for cached data (default 5 minutes)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.ttl_seconds = ttl_seconds
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.logger = logger.bind(component="DataCache")
        
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, adapter: str, symbol: str, timestamp: Optional[datetime] = None) -> str:
        """Generate cache key"""
        key_parts = [adapter, symbol]
        if timestamp:
            key_parts.append(timestamp.strftime("%Y%m%d"))
        key = "_".join(key_parts)
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_file_path(self, cache_key: str) -> Path:
        """Get file path for cache key"""
        if not self.cache_dir:
            raise ValueError("File cache not enabled")
        return self.cache_dir / f"{cache_key}.pkl"
    
    def get(self, adapter: str, symbol: str, timestamp: Optional[datetime] = None) -> Optional[float]:
        """
        Get cached price
        
        Args:
            adapter: Adapter name
            symbol: Asset symbol
            timestamp: Optional timestamp
        
        Returns:
            Cached price or None
        """
        cache_key = self._get_cache_key(adapter, symbol, timestamp)
        
        # Check memory cache
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            age = (datetime.now() - entry["timestamp"]).total_seconds()
            if age < self.ttl_seconds:
                return entry["price"]
            else:
                # Expired, remove from cache
                del self.memory_cache[cache_key]
        
        # Check file cache
        if self.cache_dir:
            try:
                file_path = self._get_file_path(cache_key)
                if file_path.exists():
                    with open(file_path, "rb") as f:
                        entry = pickle.load(f)
                    age = (datetime.now() - entry["timestamp"]).total_seconds()
                    if age < self.ttl_seconds:
                        # Also add to memory cache
                        self.memory_cache[cache_key] = entry
                        return entry["price"]
                    else:
                        # Expired, remove file
                        file_path.unlink()
            except Exception as e:
                self.logger.warning(f"Error reading cache file: {e}")
        
        return None
    
    def set(self, adapter: str, symbol: str, price: float, timestamp: Optional[datetime] = None):
        """
        Cache price
        
        Args:
            adapter: Adapter name
            symbol: Asset symbol
            price: Price to cache
            timestamp: Optional timestamp
        """
        cache_key = self._get_cache_key(adapter, symbol, timestamp)
        entry = {
            "price": price,
            "timestamp": datetime.now(),
            "adapter": adapter,
            "symbol": symbol
        }
        
        # Store in memory cache
        self.memory_cache[cache_key] = entry
        
        # Store in file cache
        if self.cache_dir:
            try:
                file_path = self._get_file_path(cache_key)
                with open(file_path, "wb") as f:
                    pickle.dump(entry, f)
            except Exception as e:
                self.logger.warning(f"Error writing cache file: {e}")
    
    def clear(self, adapter: Optional[str] = None):
        """
        Clear cache
        
        Args:
            adapter: Optional adapter name (clear all if None)
        """
        if adapter:
            # Clear entries for specific adapter
            keys_to_remove = [
                k for k, v in self.memory_cache.items()
                if v.get("adapter") == adapter
            ]
            for k in keys_to_remove:
                del self.memory_cache[k]
        else:
            # Clear all
            self.memory_cache.clear()
        
        # Clear file cache
        if self.cache_dir:
            try:
                if adapter:
                    # Remove files for specific adapter (would need to read each file)
                    # For simplicity, clear all file cache
                    for file_path in self.cache_dir.glob("*.pkl"):
                        file_path.unlink()
                else:
                    for file_path in self.cache_dir.glob("*.pkl"):
                        file_path.unlink()
            except Exception as e:
                self.logger.warning(f"Error clearing cache files: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "memory_entries": len(self.memory_cache),
            "ttl_seconds": self.ttl_seconds,
            "cache_dir": str(self.cache_dir) if self.cache_dir else None
        }

