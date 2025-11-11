"""
Portfolio Allocation Tracking API Routes
Phase: Portfolio Optimization 2025
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..portfolio.allocation_tracker import (
    AllocationTracker,
    RebalancingAlert,
    AllocationReport
)
from ..portfolio.multi_account_tracker import (
    MultiAccountTracker,
    AccountType,
    AccountInfo
)

router = APIRouter(prefix="/api/v1/allocation", tags=["allocation"])
logger = logging.getLogger(__name__)


class HoldingsRequest(BaseModel):
    """Request model for allocation calculation"""
    holdings: Dict[str, Dict[str, float]]  # {symbol: {asset_class, value, ...}}
    portfolio_value: float
    rebalancing_threshold: Optional[float] = 5.0


class AllocationResponse(BaseModel):
    """Response model for allocation report"""
    portfolio_value: float
    timestamp: str
    asset_classes: list
    total_drift: float
    needs_rebalancing: bool
    rebalancing_threshold: float
    rebalancing_actions: list


@router.post("/calculate", response_model=AllocationResponse)
async def calculate_allocation(request: HoldingsRequest):
    """
    Calculate current allocation vs targets.
    
    Returns allocation report with current vs target percentages,
    drift calculations, and rebalancing recommendations.
    """
    try:
        tracker = AllocationTracker(
            rebalancing_threshold=request.rebalancing_threshold or 5.0
        )
        
        report = tracker.calculate_allocation(
            holdings=request.holdings,
            portfolio_value=request.portfolio_value
        )
        
        actions = tracker.get_rebalancing_actions(report)
        
        return AllocationResponse(
            portfolio_value=report.portfolio_value,
            timestamp=report.timestamp,
            asset_classes=tracker.to_dict(report)["asset_classes"],
            total_drift=report.total_drift,
            needs_rebalancing=report.needs_rebalancing,
            rebalancing_threshold=report.rebalancing_threshold,
            rebalancing_actions=actions
        )
        
    except Exception as e:
        logger.error(f"Error calculating allocation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/targets")
async def get_target_allocations(
    portfolio_value: float = Query(..., description="Total portfolio value")
):
    """
    Get target dollar amounts for each asset class.
    
    Returns target allocations based on 2025 optimization plan:
    - Stocks: 50%
    - ETFs: 15%
    - Commodities: 15%
    - Crypto: 10%
    - Futures: 5%
    - Cash: 5%
    """
    try:
        tracker = AllocationTracker()
        targets = tracker.calculate_target_values(portfolio_value)
        
        return {
            "portfolio_value": portfolio_value,
            "targets": targets,
            "target_percentages": tracker.target_allocations
        }
        
    except Exception as e:
        logger.error(f"Error getting target allocations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-rebalancing")
async def check_rebalancing(
    holdings: str = Query(..., description="JSON string of holdings"),
    portfolio_value: float = Query(..., description="Total portfolio value"),
    threshold: float = Query(5.0, description="Rebalancing threshold (%)")
):
    """
    Quick check if rebalancing is needed.
    
    Returns boolean and alert messages for any asset classes
    that have drifted beyond threshold.
    """
    try:
        import json
        
        holdings_dict = json.loads(holdings)
        
        tracker = AllocationTracker(rebalancing_threshold=threshold)
        report = tracker.calculate_allocation(holdings_dict, portfolio_value)
        
        alert_system = RebalancingAlert(threshold=threshold)
        needs_rebalancing, alerts = alert_system.check_rebalancing_needed(report)
        
        return {
            "needs_rebalancing": needs_rebalancing,
            "alerts": alerts,
            "total_drift": report.total_drift,
            "threshold": threshold
        }
        
    except Exception as e:
        logger.error(f"Error checking rebalancing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drift-analysis")
async def get_drift_analysis(
    holdings: str = Query(..., description="JSON string of holdings"),
    portfolio_value: float = Query(..., description="Total portfolio value")
):
    """
    Get detailed drift analysis for each asset class.
    
    Shows how far each asset class has drifted from target,
    sorted by largest drift first.
    """
    try:
        import json
        
        holdings_dict = json.loads(holdings)
        
        tracker = AllocationTracker()
        report = tracker.calculate_allocation(holdings_dict, portfolio_value)
        
        # Sort by drift (largest first)
        drifts = [
            {
                "asset_class": ac.asset_class,
                "current_percent": ac.current_percent,
                "target_percent": ac.target_percent,
                "drift": ac.difference_percent,
                "drift_amount": ac.difference,
                "needs_rebalancing": abs(ac.difference_percent) > tracker.rebalancing_threshold
            }
            for ac in report.asset_classes
        ]
        drifts.sort(key=lambda x: abs(x["drift"]), reverse=True)
        
        return {
            "portfolio_value": portfolio_value,
            "timestamp": report.timestamp,
            "drifts": drifts,
            "total_drift": report.total_drift,
            "needs_rebalancing": report.needs_rebalancing
        }
        
    except Exception as e:
        logger.error(f"Error getting drift analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-account/summary")
async def get_multi_account_summary(
    accounts: str = Query(..., description="JSON string of accounts"),
    holdings: str = Query(..., description="JSON string of holdings by account")
):
    """
    Get summary across multiple account types (trading vs long-term).
    
    Separates prop firm, personal trading, and long-term accounts.
    """
    try:
        import json
        
        accounts_data = json.loads(accounts)
        holdings_data = json.loads(holdings)
        
        tracker = MultiAccountTracker()
        
        # Add accounts
        for acc_data in accounts_data:
            account = AccountInfo(
                account_id=acc_data["account_id"],
                account_name=acc_data["account_name"],
                account_type=AccountType(acc_data["account_type"]),
                broker=acc_data.get("broker", "Unknown"),
                current_balance=acc_data["current_balance"],
                currency=acc_data.get("currency", "USD"),
                tax_status=acc_data.get("tax_status")
            )
            tracker.add_account(account)
        
        # Calculate summaries by category
        summaries = {}
        for account_type in AccountType:
            account_holdings = {
                acc_id: holdings_data.get(acc_id, {})
                for acc_id in [acc.account_id for acc in tracker.get_accounts_by_type(account_type)]
            }
            if account_holdings:
                summaries[account_type.value] = tracker.calculate_category_summary(
                    account_type,
                    account_holdings
                )
        
        return {
            "total_portfolio_value": tracker.get_total_portfolio_value(),
            "category_breakdown": tracker.get_category_breakdown(),
            "category_percentages": tracker.get_category_percentages(),
            "summaries": {
                category: {
                    "total_capital": summary.total_capital,
                    "number_of_accounts": summary.number_of_accounts,
                    "average_balance": summary.average_balance,
                    "allocation_report": tracker.tracker.to_dict(summary.allocation_report) if summary.allocation_report else None
                }
                for category, summary in summaries.items()
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting multi-account summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

