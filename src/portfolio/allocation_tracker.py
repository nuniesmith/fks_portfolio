"""
Portfolio Allocation Tracker
Tracks current vs target allocations and calculates rebalancing needs
Phase: Portfolio Optimization 2025
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class AssetAllocation:
    """Represents a single asset allocation"""
    symbol: str
    asset_class: str  # stocks, etfs, commodities, crypto, futures, cash
    current_percent: float
    target_percent: float
    current_value: float
    target_value: float
    difference: float
    difference_percent: float


@dataclass
class AssetClassAllocation:
    """Represents allocation for an asset class"""
    asset_class: str
    current_percent: float
    target_percent: float
    current_value: float
    target_value: float
    difference: float
    difference_percent: float
    assets: List[AssetAllocation]


@dataclass
class AllocationReport:
    """Complete allocation report"""
    portfolio_value: float
    timestamp: str
    asset_classes: List[AssetClassAllocation]
    total_drift: float
    needs_rebalancing: bool
    rebalancing_threshold: float = 5.0


class AllocationTracker:
    """Tracks portfolio allocations against targets"""
    
    # Target allocations (2025 optimization plan)
    TARGET_ALLOCATIONS = {
        "stocks": 50.0,
        "etfs": 15.0,
        "commodities": 15.0,
        "crypto": 10.0,
        "futures": 5.0,
        "cash": 5.0
    }
    
    # ESG/Impact target allocations (optional)
    ESG_TARGET_ALLOCATIONS = {
        "esg_stocks": 15.0,  # ESG-focused stocks (part of stocks)
        "esg_etfs": 10.0,    # ESG ETFs (part of etfs)
        "impact_investments": 5.0,  # Direct impact investments
        "clean_energy": 3.0,  # Clean energy exposure
        "biodiversity": 2.0   # Biodiversity/nature investments
    }
    
    def __init__(self, rebalancing_threshold: float = 5.0):
        """
        Initialize allocation tracker.
        
        Args:
            rebalancing_threshold: Percent drift that triggers rebalancing (default: 5%)
        """
        self.rebalancing_threshold = rebalancing_threshold
        self.target_allocations = self.TARGET_ALLOCATIONS.copy()
    
    def calculate_allocation(
        self,
        holdings: Dict[str, Dict[str, float]],
        portfolio_value: float
    ) -> AllocationReport:
        """
        Calculate current allocation vs targets.
        
        Args:
            holdings: Dict of {symbol: {asset_class, value, ...}}
            portfolio_value: Total portfolio value
            
        Returns:
            AllocationReport with current vs target analysis
        """
        # Group by asset class
        asset_class_totals = {ac: 0.0 for ac in self.target_allocations.keys()}
        asset_allocations = []
        
        # Calculate current allocations
        for symbol, data in holdings.items():
            asset_class = data.get("asset_class", "stocks")
            value = data.get("value", 0.0)
            
            if asset_class in asset_class_totals:
                asset_class_totals[asset_class] += value
            
            # Calculate individual asset allocation
            current_percent = (value / portfolio_value * 100) if portfolio_value > 0 else 0
            target_percent = self._get_target_for_asset(symbol, asset_class)
            
            asset_allocations.append(AssetAllocation(
                symbol=symbol,
                asset_class=asset_class,
                current_percent=current_percent,
                target_percent=target_percent,
                current_value=value,
                target_value=(portfolio_value * target_percent / 100),
                difference=value - (portfolio_value * target_percent / 100),
                difference_percent=current_percent - target_percent
            ))
        
        # Calculate asset class allocations
        asset_class_allocations = []
        total_drift = 0.0
        
        for asset_class, target_percent in self.target_allocations.items():
            current_value = asset_class_totals.get(asset_class, 0.0)
            current_percent = (current_value / portfolio_value * 100) if portfolio_value > 0 else 0
            target_value = portfolio_value * target_percent / 100
            difference = current_value - target_value
            difference_percent = current_percent - target_percent
            
            # Get assets in this class
            class_assets = [a for a in asset_allocations if a.asset_class == asset_class]
            
            asset_class_allocations.append(AssetClassAllocation(
                asset_class=asset_class,
                current_percent=current_percent,
                target_percent=target_percent,
                current_value=current_value,
                target_value=target_value,
                difference=difference,
                difference_percent=difference_percent,
                assets=class_assets
            ))
            
            total_drift += abs(difference_percent)
        
        # Check if rebalancing needed
        needs_rebalancing = any(
            abs(ac.difference_percent) > self.rebalancing_threshold
            for ac in asset_class_allocations
        )
        
        return AllocationReport(
            portfolio_value=portfolio_value,
            timestamp=datetime.now().isoformat(),
            asset_classes=asset_class_allocations,
            total_drift=total_drift,
            needs_rebalancing=needs_rebalancing,
            rebalancing_threshold=self.rebalancing_threshold
        )
    
    def _get_target_for_asset(self, symbol: str, asset_class: str) -> float:
        """
        Get target allocation for a specific asset.
        
        Args:
            symbol: Asset symbol
            asset_class: Asset class
            
        Returns:
            Target percentage (0 if not specified)
        """
        # Individual asset targets (can be customized)
        asset_targets = {
            "AAPL": 10.0,  # Reduce from 14.68% to 10%
            "COST": 8.0,   # Reduce from 9.98% to 8%
            "HD": 7.0,     # Reduce from 8.07% to 7%
        }
        
        if symbol in asset_targets:
            return asset_targets[symbol]
        
        # Default: distribute within asset class
        return 0.0  # Will be calculated based on class allocation
    
    def get_rebalancing_actions(
        self,
        report: AllocationReport
    ) -> List[Dict[str, any]]:
        """
        Generate rebalancing actions needed.
        
        Args:
            report: AllocationReport from calculate_allocation
            
        Returns:
            List of rebalancing actions
        """
        actions = []
        
        for ac in report.asset_classes:
            if abs(ac.difference_percent) > self.rebalancing_threshold:
                action_type = "SELL" if ac.difference > 0 else "BUY"
                amount = abs(ac.difference)
                
                actions.append({
                    "asset_class": ac.asset_class,
                    "action": action_type,
                    "amount": amount,
                    "current_percent": ac.current_percent,
                    "target_percent": ac.target_percent,
                    "drift": ac.difference_percent
                })
        
        return actions
    
    def calculate_target_values(
        self,
        portfolio_value: float
    ) -> Dict[str, float]:
        """
        Calculate target dollar amounts for each asset class.
        
        Args:
            portfolio_value: Total portfolio value
            
        Returns:
            Dict of {asset_class: target_value}
        """
        return {
            asset_class: portfolio_value * percent / 100
            for asset_class, percent in self.target_allocations.items()
        }
    
    def to_dict(self, report: AllocationReport) -> Dict:
        """Convert report to dictionary"""
        return {
            "portfolio_value": report.portfolio_value,
            "timestamp": report.timestamp,
            "asset_classes": [
                {
                    "asset_class": ac.asset_class,
                    "current_percent": ac.current_percent,
                    "target_percent": ac.target_percent,
                    "current_value": ac.current_value,
                    "target_value": ac.target_value,
                    "difference": ac.difference,
                    "difference_percent": ac.difference_percent,
                    "assets": [
                        {
                            "symbol": a.symbol,
                            "current_percent": a.current_percent,
                            "target_percent": a.target_percent,
                            "current_value": a.current_value,
                            "target_value": a.target_value,
                            "difference": a.difference,
                            "difference_percent": a.difference_percent
                        }
                        for a in ac.assets
                    ]
                }
                for ac in report.asset_classes
            ],
            "total_drift": report.total_drift,
            "needs_rebalancing": report.needs_rebalancing,
            "rebalancing_threshold": report.rebalancing_threshold
        }


class RebalancingAlert:
    """Manages rebalancing alerts and notifications"""
    
    def __init__(self, threshold: float = 5.0):
        """
        Initialize rebalancing alert system.
        
        Args:
            threshold: Drift threshold for alerts (default: 5%)
        """
        self.threshold = threshold
        self.last_alert_time = {}
    
    def check_rebalancing_needed(
        self,
        report: AllocationReport
    ) -> Tuple[bool, List[str]]:
        """
        Check if rebalancing is needed and generate alerts.
        
        Args:
            report: AllocationReport
            
        Returns:
            Tuple of (needs_rebalancing, alert_messages)
        """
        alerts = []
        needs_rebalancing = False
        
        for ac in report.asset_classes:
            drift = abs(ac.difference_percent)
            
            if drift > self.threshold:
                needs_rebalancing = True
                direction = "over" if ac.difference > 0 else "under"
                alerts.append(
                    f"{ac.asset_class.upper()}: {direction}-allocated by "
                    f"{drift:.2f}% (current: {ac.current_percent:.2f}%, "
                    f"target: {ac.target_percent:.2f}%)"
                )
        
        return needs_rebalancing, alerts
    
    def should_send_alert(
        self,
        asset_class: str,
        cooldown_minutes: int = 60
    ) -> bool:
        """
        Check if alert should be sent (cooldown period).
        
        Args:
            asset_class: Asset class to check
            cooldown_minutes: Minutes between alerts (default: 60)
            
        Returns:
            True if alert should be sent
        """
        from datetime import datetime, timedelta
        
        if asset_class not in self.last_alert_time:
            return True
        
        last_alert = self.last_alert_time[asset_class]
        cooldown = timedelta(minutes=cooldown_minutes)
        
        return datetime.now() - last_alert > cooldown
    
    def record_alert(self, asset_class: str):
        """Record that an alert was sent"""
        self.last_alert_time[asset_class] = datetime.now()

