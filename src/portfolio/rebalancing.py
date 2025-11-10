"""
Portfolio Rebalancing Logic
Rebalances portfolio to maintain BTC allocation target
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from loguru import logger

from .portfolio import Portfolio
from ..data.btc_converter import BTCConverter
from ..data.manager import DataManager


class PortfolioRebalancer:
    """Rebalances portfolio to maintain BTC allocation target"""
    
    def __init__(
        self,
        portfolio: Portfolio,
        target_btc_pct: float = 0.50,
        btc_converter: Optional[BTCConverter] = None,
        data_manager: Optional[DataManager] = None
    ):
        """
        Initialize rebalancer
        
        Args:
            portfolio: Portfolio instance
            target_btc_pct: Target BTC allocation (0.0 to 1.0)
            btc_converter: BTCConverter instance
            data_manager: DataManager instance
        """
        self.portfolio = portfolio
        self.target_btc_pct = target_btc_pct
        self.btc_converter = btc_converter or BTCConverter(data_manager=data_manager)
        self.data_manager = data_manager or DataManager()
        self.logger = logger.bind(component="PortfolioRebalancer")
    
    def get_current_btc_allocation(self) -> float:
        """Get current BTC allocation percentage"""
        holdings = {
            symbol: self.portfolio.get_allocation(symbol)
            for symbol in self.portfolio.assets.keys()
        }
        return self.btc_converter.get_btc_allocation(holdings)
    
    def calculate_rebalancing_actions(
        self,
        current_holdings: Dict[str, float],
        target_allocations: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate rebalancing actions needed
        
        Args:
            current_holdings: Current holdings (symbol -> amount)
            target_allocations: Target allocations (symbol -> allocation %)
        
        Returns:
            Dictionary with buy/sell actions (positive = buy, negative = sell)
        """
        # Calculate current total value in BTC
        current_btc_value = self.btc_converter.calculate_portfolio_value_btc(current_holdings)
        
        if current_btc_value == 0:
            self.logger.warning("Portfolio value is zero")
            return {}
        
        actions = {}
        
        for symbol, target_pct in target_allocations.items():
            # Calculate target value in BTC
            target_btc_value = current_btc_value * target_pct
            
            # Get current value in BTC
            current_amount = current_holdings.get(symbol, 0.0)
            current_btc_value_asset = self.btc_converter.to_btc(current_amount, symbol)
            
            if current_btc_value_asset is None:
                continue
            
            # Calculate difference
            difference_btc = target_btc_value - current_btc_value_asset
            
            # Convert to asset amount
            if difference_btc > 0:
                # Need to buy
                asset_amount = self.btc_converter.from_btc(difference_btc, symbol)
                actions[symbol] = asset_amount if asset_amount else 0.0
            elif difference_btc < 0:
                # Need to sell
                asset_amount = self.btc_converter.from_btc(abs(difference_btc), symbol)
                actions[symbol] = -asset_amount if asset_amount else 0.0
            else:
                actions[symbol] = 0.0
        
        return actions
    
    def rebalance_to_btc_target(
        self,
        current_holdings: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate rebalancing to maintain BTC target
        
        Args:
            current_holdings: Current holdings (symbol -> amount)
        
        Returns:
            Dictionary with rebalancing actions
        """
        # Get current BTC allocation
        current_btc_pct = self.get_current_btc_allocation()
        
        # Calculate target allocations
        target_allocations = {}
        remaining_pct = 1.0 - self.target_btc_pct
        
        # Set BTC target
        target_allocations["BTC"] = self.target_btc_pct
        
        # Distribute remaining among other assets
        non_btc_symbols = [s for s in current_holdings.keys() if s != "BTC"]
        if non_btc_symbols:
            per_asset = remaining_pct / len(non_btc_symbols)
            for symbol in non_btc_symbols:
                target_allocations[symbol] = per_asset
        
        # Calculate actions
        actions = self.calculate_rebalancing_actions(current_holdings, target_allocations)
        
        return actions
    
    def rebalance_for_diversification(
        self,
        current_holdings: Dict[str, float],
        target_symbols: List[str],
        target_allocations: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Rebalance to diversify across target symbols
        
        Args:
            current_holdings: Current holdings
            target_symbols: List of target symbols
            target_allocations: Optional specific allocations (default: equal weight)
        
        Returns:
            Dictionary with rebalancing actions
        """
        if target_allocations is None:
            # Equal weight
            target_allocations = {symbol: 1.0 / len(target_symbols) for symbol in target_symbols}
        
        # Ensure BTC target is maintained
        if "BTC" in target_symbols:
            btc_target = max(self.target_btc_pct, target_allocations.get("BTC", 0.0))
            target_allocations["BTC"] = btc_target
            
            # Redistribute remaining
            remaining = 1.0 - btc_target
            non_btc = [s for s in target_symbols if s != "BTC"]
            if non_btc:
                per_asset = remaining / len(non_btc)
                for symbol in non_btc:
                    target_allocations[symbol] = per_asset
        
        actions = self.calculate_rebalancing_actions(current_holdings, target_allocations)
        return actions
    
    def print_rebalancing_plan(
        self,
        actions: Dict[str, float],
        current_holdings: Dict[str, float]
    ):
        """Print formatted rebalancing plan"""
        print("\n" + "="*60)
        print("REBALANCING PLAN")
        print("="*60)
        print(f"Target BTC Allocation: {self.target_btc_pct:.1%}")
        print(f"Current BTC Allocation: {self.get_current_btc_allocation():.1%}")
        print("\nActions:")
        
        buys = {k: v for k, v in actions.items() if v > 0}
        sells = {k: -v for k, v in actions.items() if v < 0}
        
        if buys:
            print("\n  BUY:")
            for symbol, amount in sorted(buys.items(), key=lambda x: x[1], reverse=True):
                current = current_holdings.get(symbol, 0.0)
                print(f"    {symbol:6s}: {amount:10.4f} (current: {current:10.4f})")
        
        if sells:
            print("\n  SELL:")
            for symbol, amount in sorted(sells.items(), key=lambda x: x[1], reverse=True):
                current = current_holdings.get(symbol, 0.0)
                print(f"    {symbol:6s}: {amount:10.4f} (current: {current:10.4f})")
        
        if not buys and not sells:
            print("  No rebalancing needed")
        
        print("="*60)

