"""
Portfolio Class for Portfolio Platform
Manages portfolio composition and calculations
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from loguru import logger
from .asset import BaseAsset, AssetType


@dataclass
class Portfolio:
    """Portfolio class managing asset allocations"""
    assets: Dict[str, BaseAsset] = field(default_factory=dict)
    allocations: Dict[str, float] = field(default_factory=dict)
    total_value: float = 0.0
    
    def add_asset(self, asset: BaseAsset, allocation: float = 0.0):
        """Add an asset to the portfolio"""
        if not 0.0 <= allocation <= 1.0:
            raise ValueError(f"Allocation must be between 0 and 1, got {allocation}")
        
        self.assets[asset.symbol] = asset
        self.allocations[asset.symbol] = allocation
        logger.info(f"Added {asset.symbol} with {allocation*100:.2f}% allocation")
    
    def set_allocation(self, symbol: str, allocation: float):
        """Set allocation for an existing asset"""
        if symbol not in self.assets:
            raise ValueError(f"Asset {symbol} not found in portfolio")
        if not 0.0 <= allocation <= 1.0:
            raise ValueError(f"Allocation must be between 0 and 1, got {allocation}")
        
        self.allocations[symbol] = allocation
        logger.info(f"Set {symbol} allocation to {allocation*100:.2f}%")
    
    def get_allocation(self, symbol: str) -> float:
        """Get allocation for an asset"""
        return self.allocations.get(symbol, 0.0)
    
    def validate_allocations(self) -> tuple[bool, Optional[str]]:
        """Validate that allocations sum to 1.0 (100%)"""
        total = sum(self.allocations.values())
        if abs(total - 1.0) > 0.001:  # Allow small floating point errors
            return False, f"Allocations sum to {total*100:.2f}%, expected 100%"
        return True, None
    
    def get_btc_allocation(self) -> float:
        """Get BTC allocation percentage"""
        return self.get_allocation("BTC")
    
    def check_btc_constraints(self) -> tuple[bool, Optional[str]]:
        """Check if BTC allocation meets constraints (50-60%)"""
        btc_alloc = self.get_btc_allocation()
        if btc_alloc < 0.50:
            return False, f"BTC allocation {btc_alloc*100:.2f}% is below minimum 50%"
        if btc_alloc > 0.60:
            return False, f"BTC allocation {btc_alloc*100:.2f}% exceeds maximum 60%"
        return True, None
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        valid, error = self.validate_allocations()
        btc_valid, btc_error = self.check_btc_constraints()
        
        return {
            "total_assets": len(self.assets),
            "total_allocation": sum(self.allocations.values()),
            "allocations_valid": valid,
            "allocations_error": error,
            "btc_allocation": self.get_btc_allocation(),
            "btc_constraints_met": btc_valid,
            "btc_constraints_error": btc_error,
            "allocations": self.allocations.copy(),
            "assets": {symbol: asset.symbol for symbol, asset in self.assets.items()}
        }
    
    def __repr__(self) -> str:
        """String representation"""
        summary = self.get_portfolio_summary()
        return f"Portfolio(assets={len(self.assets)}, btc_alloc={summary['btc_allocation']*100:.1f}%)"

