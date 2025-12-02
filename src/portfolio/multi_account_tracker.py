"""
Multi-Account Portfolio Tracker
Tracks allocations across different account types (trading vs long-term)
Phase 1: Portfolio Assessment & Account Separation
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from .allocation_tracker import AllocationTracker, AllocationReport

logger = logging.getLogger(__name__)


class AccountType(Enum):
    """Account type enumeration"""
    PROP_FIRM = "prop_firm"
    PERSONAL_TRADING = "personal_trading"
    LONG_TERM_RETIREMENT = "long_term_retirement"
    LONG_TERM_TAXABLE = "long_term_taxable"


@dataclass
class AccountInfo:
    """Information about a single account"""
    account_id: str
    account_name: str
    account_type: AccountType
    broker: str
    current_balance: float
    currency: str = "USD"
    restrictions: Optional[List[str]] = None
    tax_status: Optional[str] = None


@dataclass
class AccountCategorySummary:
    """Summary for an account category"""
    category: str
    account_type: AccountType
    total_capital: float
    number_of_accounts: int
    average_balance: float
    allocation_report: Optional[AllocationReport] = None


class MultiAccountTracker:
    """Tracks portfolios across multiple account types"""
    
    # Target allocations by account type
    TRADING_ACCOUNT_TARGETS = {
        "futures": 40.0,
        "forex": 25.0,
        "crypto": 25.0,
        "cash": 10.0
    }
    
    PERSONAL_TRADING_TARGETS = {
        "stocks": 45.0,
        "options": 25.0,
        "crypto": 18.0,
        "futures": 12.0,
        "cash": 12.0
    }
    
    LONG_TERM_TARGETS = {
        "stocks": 50.0,
        "etfs": 15.0,
        "commodities": 15.0,
        "crypto": 10.0,
        "futures": 5.0,
        "cash": 5.0
    }
    
    def __init__(self, rebalancing_threshold: float = 5.0):
        """
        Initialize multi-account tracker.
        
        Args:
            rebalancing_threshold: Percent drift that triggers rebalancing
        """
        self.accounts: Dict[str, AccountInfo] = {}
        self.rebalancing_threshold = rebalancing_threshold
        self.tracker = AllocationTracker(rebalancing_threshold=rebalancing_threshold)
    
    def add_account(self, account: AccountInfo):
        """Add an account to tracking"""
        self.accounts[account.account_id] = account
        logger.info(f"Added account: {account.account_name} ({account.account_type.value})")
    
    def get_accounts_by_type(self, account_type: AccountType) -> List[AccountInfo]:
        """Get all accounts of a specific type"""
        return [acc for acc in self.accounts.values() if acc.account_type == account_type]
    
    def calculate_category_summary(
        self,
        account_type: AccountType,
        holdings: Dict[str, Dict[str, float]]
    ) -> AccountCategorySummary:
        """
        Calculate summary for an account category.
        
        Args:
            account_type: Type of accounts to summarize
            holdings: Dict of {account_id: {symbol: {asset_class, value, ...}}}
            
        Returns:
            AccountCategorySummary
        """
        accounts = self.get_accounts_by_type(account_type)
        total_capital = sum(acc.current_balance for acc in accounts)
        
        # Aggregate holdings for this category
        category_holdings = {}
        for account_id, account_holdings in holdings.items():
            if account_id in [acc.account_id for acc in accounts]:
                for symbol, data in account_holdings.items():
                    if symbol not in category_holdings:
                        category_holdings[symbol] = data.copy()
                    else:
                        category_holdings[symbol]["value"] += data.get("value", 0)
        
        # Calculate allocation report
        allocation_report = None
        if category_holdings and total_capital > 0:
            allocation_report = self.tracker.calculate_allocation(
                category_holdings,
                total_capital
            )
        
        return AccountCategorySummary(
            category=account_type.value,
            account_type=account_type,
            total_capital=total_capital,
            number_of_accounts=len(accounts),
            average_balance=total_capital / len(accounts) if accounts else 0,
            allocation_report=allocation_report
        )
    
    def get_total_portfolio_value(self) -> float:
        """Get total portfolio value across all accounts"""
        return sum(acc.current_balance for acc in self.accounts.values())
    
    def get_category_breakdown(self) -> Dict[str, float]:
        """Get capital breakdown by account category"""
        breakdown = {}
        for account_type in AccountType:
            accounts = self.get_accounts_by_type(account_type)
            total = sum(acc.current_balance for acc in accounts)
            breakdown[account_type.value] = total
        
        return breakdown
    
    def get_category_percentages(self) -> Dict[str, float]:
        """Get percentage breakdown by account category"""
        total = self.get_total_portfolio_value()
        if total == 0:
            return {}
        
        breakdown = self.get_category_breakdown()
        return {
            category: (value / total * 100)
            for category, value in breakdown.items()
        }
    
    def get_target_allocations(self, account_type: AccountType) -> Dict[str, float]:
        """
        Get target allocations for an account type.
        
        Args:
            account_type: Type of account
            
        Returns:
            Dict of {asset_class: target_percent}
        """
        if account_type == AccountType.PROP_FIRM:
            return self.TRADING_ACCOUNT_TARGETS.copy()
        elif account_type == AccountType.PERSONAL_TRADING:
            return self.PERSONAL_TRADING_TARGETS.copy()
        else:  # Long-term accounts
            return self.LONG_TERM_TARGETS.copy()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "total_portfolio_value": self.get_total_portfolio_value(),
            "accounts": [
                {
                    "account_id": acc.account_id,
                    "account_name": acc.account_name,
                    "account_type": acc.account_type.value,
                    "broker": acc.broker,
                    "current_balance": acc.current_balance,
                    "currency": acc.currency,
                    "tax_status": acc.tax_status
                }
                for acc in self.accounts.values()
            ],
            "category_breakdown": self.get_category_breakdown(),
            "category_percentages": self.get_category_percentages(),
            "timestamp": datetime.now().isoformat()
        }

