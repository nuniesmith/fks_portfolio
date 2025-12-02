"""
Portfolio Value Calculation in BTC Terms
Tracks portfolio performance denominated in BTC
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from ..data.btc_converter import BTCConverter
from ..data.manager import DataManager
from .portfolio import Portfolio


class PortfolioValueTracker:
    """Tracks portfolio value in BTC terms over time"""
    
    def __init__(
        self,
        portfolio: Portfolio,
        btc_converter: Optional[BTCConverter] = None,
        data_manager: Optional[DataManager] = None
    ):
        """
        Initialize portfolio value tracker
        
        Args:
            portfolio: Portfolio instance
            btc_converter: BTCConverter instance
            data_manager: DataManager instance
        """
        self.portfolio = portfolio
        self.btc_converter = btc_converter or BTCConverter(data_manager=data_manager)
        self.data_manager = data_manager or DataManager()
        self.logger = logger.bind(component="PortfolioValueTracker")
    
    def calculate_current_value_btc(self) -> Dict[str, float]:
        """
        Calculate current portfolio value in BTC
        
        Returns:
            Dictionary with portfolio value breakdown
        """
        # Get current holdings (amounts of each asset)
        holdings = {}
        for symbol, asset in self.portfolio.assets.items():
            allocation = self.portfolio.get_allocation(symbol)
            # For now, assume portfolio value is normalized (total = 1.0)
            # In real implementation, this would use actual dollar amounts
            holdings[symbol] = allocation
        
        # Convert to BTC
        btc_holdings = self.btc_converter.convert_portfolio_to_btc(holdings)
        total_btc = btc_holdings.pop("_total", 0.0)
        
        # Calculate BTC allocation
        btc_allocation = self.btc_converter.get_btc_allocation(holdings)
        
        return {
            "total_btc": total_btc,
            "holdings_btc": btc_holdings,
            "btc_allocation": btc_allocation,
            "timestamp": datetime.now()
        }
    
    def track_value_over_time(
        self,
        start_date: datetime,
        end_date: datetime,
        interval: str = "daily"
    ) -> pd.DataFrame:
        """
        Track portfolio value in BTC over time
        
        Args:
            start_date: Start date
            end_date: End date
            interval: Data interval ("daily", "hourly")
        
        Returns:
            DataFrame with columns: date, total_btc, btc_allocation, holdings_btc_*
        """
        # Get historical prices for all assets in portfolio
        symbols = list(self.portfolio.assets.keys())
        
        # Fetch historical data
        historical_data = {}
        for symbol in symbols:
            data = self.data_manager.fetch_historical_prices(
                symbol, start_date, end_date, interval=interval
            )
            if not data.empty:
                historical_data[symbol] = data.set_index("date")["close"]
        
        if not historical_data:
            return pd.DataFrame()
        
        # Align all dates
        all_dates = set()
        for prices in historical_data.values():
            all_dates.update(prices.index)
        all_dates = sorted(list(all_dates))
        
        # Calculate portfolio value for each date
        results = []
        allocations = {
            symbol: self.portfolio.get_allocation(symbol)
            for symbol in symbols
        }
        
        for date in all_dates:
            # Get prices for this date
            holdings = {}
            for symbol in symbols:
                if symbol in historical_data and date in historical_data[symbol].index:
                    # Use allocation as amount (normalized portfolio)
                    holdings[symbol] = allocations.get(symbol, 0.0)
            
            # Convert to BTC for this date
            try:
                btc_holdings = self.btc_converter.convert_portfolio_to_btc(
                    holdings, timestamp=date
                )
                total_btc = btc_holdings.pop("_total", 0.0)
                btc_allocation = self.btc_converter.get_btc_allocation(holdings, timestamp=date)
                
                result = {
                    "date": date,
                    "total_btc": total_btc,
                    "btc_allocation": btc_allocation
                }
                
                # Add individual holdings
                for symbol, btc_value in btc_holdings.items():
                    result[f"{symbol}_btc"] = btc_value
                
                results.append(result)
            except Exception as e:
                self.logger.warning(f"Error calculating value for {date}: {e}")
                continue
        
        df = pd.DataFrame(results)
        return df
    
    def calculate_btc_returns(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """
        Calculate BTC-denominated returns for portfolio
        
        Args:
            start_date: Start date
            end_date: End date
        
        Returns:
            Dictionary with return metrics
        """
        # Track value over time
        value_df = self.track_value_over_time(start_date, end_date)
        
        if value_df.empty or "total_btc" not in value_df.columns:
            return {}
        
        # Calculate returns
        value_df = value_df.sort_values("date")
        initial_btc = value_df["total_btc"].iloc[0]
        final_btc = value_df["total_btc"].iloc[-1]
        
        total_return = (final_btc - initial_btc) / initial_btc if initial_btc > 0 else 0.0
        
        # Calculate daily returns
        daily_returns = value_df["total_btc"].pct_change().dropna()
        
        # Calculate metrics
        avg_daily_return = daily_returns.mean()
        volatility = daily_returns.std()
        sharpe_ratio = (avg_daily_return / volatility) if volatility > 0 else 0.0
        
        # Max drawdown
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        return {
            "total_return": total_return,
            "avg_daily_return": avg_daily_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "initial_btc": initial_btc,
            "final_btc": final_btc
        }
    
    def get_btc_allocation_breakdown(self) -> Dict[str, float]:
        """
        Get current BTC allocation breakdown
        
        Returns:
            Dictionary with allocation percentages
        """
        holdings = {
            symbol: self.portfolio.get_allocation(symbol)
            for symbol in self.portfolio.assets.keys()
        }
        
        btc_holdings = self.btc_converter.convert_portfolio_to_btc(holdings)
        total_btc = btc_holdings.pop("_total", 0.0)
        
        if total_btc == 0:
            return {}
        
        # Calculate percentages
        breakdown = {}
        for symbol, btc_value in btc_holdings.items():
            breakdown[symbol] = btc_value / total_btc if total_btc > 0 else 0.0
        
        return breakdown
    
    def print_portfolio_summary_btc(self):
        """Print portfolio summary in BTC terms"""
        value = self.calculate_current_value_btc()
        
        print("\n" + "="*60)
        print("PORTFOLIO VALUE (BTC TERMS)")
        print("="*60)
        print(f"Total Value: {value['total_btc']:.8f} BTC")
        print(f"BTC Allocation: {value['btc_allocation']:.2%}")
        print("\nHoldings (BTC):")
        for symbol, btc_value in sorted(value['holdings_btc'].items(), key=lambda x: x[1], reverse=True):
            if btc_value > 0.00000001:  # Only show non-zero
                percentage = btc_value / value['total_btc'] if value['total_btc'] > 0 else 0
                print(f"  {symbol:6s}: {btc_value:12.8f} BTC ({percentage:6.2%})")
        print("="*60)

