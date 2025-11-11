"""
Asset Classes for Portfolio Platform
Defines asset types (Crypto, Stock) with their properties
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class AssetType(Enum):
    """Asset type enumeration"""
    CRYPTO = "crypto"
    STOCK = "stock"
    FUTURES = "futures"
    CASH = "cash"


@dataclass
class BaseAsset:
    """Base asset class with common properties"""
    symbol: str
    asset_type: AssetType
    volatility: float = 0.0
    correlation_to_btc: float = 0.0
    expected_return: float = 0.0
    current_price: Optional[float] = None
    
    def __post_init__(self):
        """Validate asset properties"""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if self.volatility < 0:
            raise ValueError("Volatility cannot be negative")
        if not -1.0 <= self.correlation_to_btc <= 1.0:
            raise ValueError("Correlation must be between -1 and 1")


@dataclass
class CryptoAsset(BaseAsset):
    """Cryptocurrency asset"""
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    
    def __init__(self, symbol: str, **kwargs):
        super().__init__(
            symbol=symbol,
            asset_type=AssetType.CRYPTO,
            **kwargs
        )


@dataclass
class StockAsset(BaseAsset):
    """Stock asset"""
    sector: Optional[str] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    
    def __init__(self, symbol: str, sector: Optional[str] = None, **kwargs):
        # Remove sector from kwargs to avoid passing it twice
        kwargs.pop('sector', None)
        super().__init__(
            symbol=symbol,
            asset_type=AssetType.STOCK,
            **kwargs
        )
        # Set sector after initialization
        self.sector = sector


@dataclass
class CashAsset(BaseAsset):
    """Cash/USD asset"""
    def __init__(self, symbol: str = "USD", **kwargs):
        super().__init__(
            symbol=symbol,
            asset_type=AssetType.CASH,
            volatility=0.0,
            correlation_to_btc=0.0,
            expected_return=0.0,
            current_price=1.0,
            **kwargs
        )


def create_asset(symbol: str, asset_type: str, **kwargs) -> BaseAsset:
    """Factory function to create appropriate asset type"""
    asset_type_enum = AssetType(asset_type.lower())
    
    if asset_type_enum == AssetType.CRYPTO:
        return CryptoAsset(symbol, **kwargs)
    elif asset_type_enum == AssetType.STOCK:
        return StockAsset(symbol, **kwargs)
    elif asset_type_enum == AssetType.CASH:
        return CashAsset(symbol, **kwargs)
    else:
        raise ValueError(f"Unsupported asset type: {asset_type}")

