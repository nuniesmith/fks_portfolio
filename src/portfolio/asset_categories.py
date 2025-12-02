"""
Asset Categories and Classification
Categorizes assets for diversification analysis
"""
from typing import Dict, List, Set
from enum import Enum
from dataclasses import dataclass


class AssetCategory(Enum):
    """Asset category types"""
    HIGH_VOL_CRYPTO = "high_vol_crypto"
    STABLE_CRYPTO = "stable_crypto"
    STOCKS = "stocks"
    COMMODITIES = "commodities"
    STABLECOINS = "stablecoins"
    DEFI = "defi"
    LAYER1 = "layer1"
    LAYER2 = "layer2"
    MEME = "meme"


@dataclass
class AssetCategoryInfo:
    """Information about an asset category"""
    category: AssetCategory
    symbols: List[str]
    description: str
    typical_volatility: float
    typical_correlation_to_btc: float


class AssetCategorizer:
    """Categorizes assets for diversification"""
    
    # Asset category definitions
    CATEGORIES: Dict[AssetCategory, AssetCategoryInfo] = {
        AssetCategory.STABLE_CRYPTO: AssetCategoryInfo(
            category=AssetCategory.STABLE_CRYPTO,
            symbols=["BTC", "ETH"],
            description="Stable, established cryptocurrencies",
            typical_volatility=0.50,
            typical_correlation_to_btc=0.80
        ),
        AssetCategory.HIGH_VOL_CRYPTO: AssetCategoryInfo(
            category=AssetCategory.HIGH_VOL_CRYPTO,
            symbols=["SOL", "AVAX", "MATIC", "ADA", "DOT", "ATOM", "ALGO"],
            description="Higher volatility altcoins",
            typical_volatility=0.80,
            typical_correlation_to_btc=0.70
        ),
        AssetCategory.DEFI: AssetCategoryInfo(
            category=AssetCategory.DEFI,
            symbols=["UNI", "LINK", "AAVE", "COMP", "MKR", "SUSHI"],
            description="Decentralized finance tokens",
            typical_volatility=0.90,
            typical_correlation_to_btc=0.75
        ),
        AssetCategory.LAYER1: AssetCategoryInfo(
            category=AssetCategory.LAYER1,
            symbols=["SOL", "AVAX", "ADA", "DOT", "ATOM", "ALGO"],
            description="Layer 1 blockchain tokens",
            typical_volatility=0.75,
            typical_correlation_to_btc=0.70
        ),
        AssetCategory.LAYER2: AssetCategoryInfo(
            category=AssetCategory.LAYER2,
            symbols=["MATIC", "ARB", "OP"],
            description="Layer 2 scaling solutions",
            typical_volatility=0.85,
            typical_correlation_to_btc=0.75
        ),
        AssetCategory.MEME: AssetCategoryInfo(
            category=AssetCategory.MEME,
            symbols=["DOGE", "SHIB", "PEPE"],
            description="Meme coins",
            typical_volatility=1.20,
            typical_correlation_to_btc=0.60
        ),
        AssetCategory.STOCKS: AssetCategoryInfo(
            category=AssetCategory.STOCKS,
            symbols=["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"],
            description="Traditional stocks and ETFs",
            typical_volatility=0.25,
            typical_correlation_to_btc=0.30
        ),
        AssetCategory.COMMODITIES: AssetCategoryInfo(
            category=AssetCategory.COMMODITIES,
            symbols=["GLD", "SLV", "USO"],
            description="Commodities and precious metals",
            typical_volatility=0.20,
            typical_correlation_to_btc=0.10
        ),
        AssetCategory.STABLECOINS: AssetCategoryInfo(
            category=AssetCategory.STABLECOINS,
            symbols=["USDT", "USDC", "DAI"],
            description="Stablecoins (pegged to USD)",
            typical_volatility=0.01,
            typical_correlation_to_btc=0.00
        )
    }
    
    @classmethod
    def get_category(cls, symbol: str) -> List[AssetCategory]:
        """
        Get categories for a symbol
        
        Args:
            symbol: Asset symbol
        
        Returns:
            List of categories this symbol belongs to
        """
        categories = []
        symbol_upper = symbol.upper()
        
        for category, info in cls.CATEGORIES.items():
            if symbol_upper in info.symbols:
                categories.append(category)
        
        return categories
    
    @classmethod
    def get_symbols_in_category(cls, category: AssetCategory) -> List[str]:
        """
        Get all symbols in a category
        
        Args:
            category: Asset category
        
        Returns:
            List of symbols
        """
        if category in cls.CATEGORIES:
            return cls.CATEGORIES[category].symbols.copy()
        return []
    
    @classmethod
    def get_all_categories(cls) -> List[AssetCategory]:
        """Get all defined categories"""
        return list(cls.CATEGORIES.keys())
    
    @classmethod
    def get_category_info(cls, category: AssetCategory) -> AssetCategoryInfo:
        """Get information about a category"""
        return cls.CATEGORIES.get(category)
    
    @classmethod
    def is_diversified(cls, symbols: List[str]) -> bool:
        """
        Check if portfolio is diversified across categories
        
        Args:
            symbols: List of asset symbols
        
        Returns:
            True if diversified across multiple categories
        """
        categories_represented = set()
        for symbol in symbols:
            categories = cls.get_category(symbol)
            categories_represented.update(categories)
        
        # Consider diversified if represented in 3+ categories
        return len(categories_represented) >= 3
    
    @classmethod
    def get_diversification_score(cls, symbols: List[str]) -> float:
        """
        Calculate diversification score (0.0 to 1.0)
        
        Args:
            symbols: List of asset symbols
        
        Returns:
            Diversification score
        """
        categories_represented = set()
        for symbol in symbols:
            categories = cls.get_category(symbol)
            categories_represented.update(categories)
        
        # Score based on number of categories
        max_categories = len(cls.CATEGORIES)
        score = min(len(categories_represented) / max_categories, 1.0)
        
        return score
    
    @classmethod
    def suggest_diversification(cls, current_symbols: List[str]) -> List[str]:
        """
        Suggest assets to add for better diversification
        
        Args:
            current_symbols: Current portfolio symbols
        
        Returns:
            List of suggested symbols to add
        """
        current_categories = set()
        for symbol in current_symbols:
            current_categories.update(cls.get_category(symbol))
        
        # Find categories not represented
        all_categories = set(cls.CATEGORIES.keys())
        missing_categories = all_categories - current_categories
        
        suggestions = []
        for category in missing_categories:
            info = cls.CATEGORIES[category]
            # Suggest top symbols from missing categories
            for symbol in info.symbols[:3]:  # Top 3 from each category
                if symbol not in current_symbols:
                    suggestions.append(symbol)
        
        return suggestions[:10]  # Return top 10 suggestions

