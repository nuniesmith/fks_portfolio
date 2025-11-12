"""
Simple Backtesting Framework
Validates portfolio allocation with historical data
"""
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from loguru import logger

from ..data.fetchers import CryptoFetcher, YahooFinanceFetcher
from ..portfolio.portfolio import Portfolio


class SimpleBacktest:
    """Simple backtesting engine for portfolio validation"""
    
    def __init__(self):
        self.logger = logger
        self.crypto_fetcher = CryptoFetcher()
        self.stock_fetcher = YahooFinanceFetcher()
    
    def fetch_historical_data(
        self,
        symbols: List[str],
        days: int = 365
    ) -> pd.DataFrame:
        """
        Fetch historical data for multiple symbols
        
        Args:
            symbols: List of symbols to fetch
            days: Number of days of history
        
        Returns:
            DataFrame with historical prices (columns = symbols, index = dates)
        """
        all_data = {}
        
        for symbol in symbols:
            self.logger.info(f"Fetching historical data for {symbol}...")
            
            # Determine asset type
            if symbol in ["BTC", "ETH", "SOL"] or symbol.endswith("-USD"):
                data = self.crypto_fetcher.fetch_historical(symbol, days)
            else:
                data = self.stock_fetcher.fetch_historical(symbol, days)
            
            if data is not None and not data.empty:
                all_data[symbol] = data['close']
            else:
                self.logger.warning(f"No data fetched for {symbol}")
        
        if not all_data:
            raise ValueError("No historical data fetched for any symbol")
        
        # Combine into single DataFrame
        df = pd.DataFrame(all_data)
        df = df.sort_index()  # Sort by date
        
        self.logger.info(f"Fetched {len(df)} days of data for {len(df.columns)} symbols")
        
        return df
    
    def calculate_returns(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Calculate daily returns from prices"""
        returns = prices.pct_change().dropna()
        return returns
    
    def backtest_allocation(
        self,
        allocations: Dict[str, float],
        historical_prices: pd.DataFrame,
        rebalance_frequency: str = "monthly"
    ) -> Dict:
        """
        Backtest portfolio allocation
        
        Args:
            allocations: Dictionary of symbol -> allocation weights
            historical_prices: DataFrame with historical prices
            rebalance_frequency: "daily", "weekly", "monthly"
        
        Returns:
            Dictionary with backtest results
        """
        if historical_prices.empty:
            raise ValueError("Historical prices DataFrame is empty")
        
        # Validate allocations sum to 1
        total_allocation = sum(allocations.values())
        if abs(total_allocation - 1.0) > 0.001:
            raise ValueError(f"Allocations sum to {total_allocation:.4f}, expected 1.0")
        
        # Calculate returns
        returns = self.calculate_returns(historical_prices)
        
        # Filter to symbols in allocation
        portfolio_symbols = [s for s in allocations.keys() if s in returns.columns]
        if not portfolio_symbols:
            raise ValueError("No matching symbols between allocations and historical data")
        
        returns = returns[portfolio_symbols]
        
        # Normalize allocations to match available symbols
        total_alloc = sum(allocations[s] for s in portfolio_symbols)
        normalized_allocations = {s: allocations[s] / total_alloc for s in portfolio_symbols}
        
        # Calculate portfolio returns (weighted average)
        portfolio_returns = pd.Series(index=returns.index, dtype=float)
        
        for date in returns.index:
            portfolio_return = sum(
                returns.loc[date, symbol] * normalized_allocations[symbol]
                for symbol in portfolio_symbols
            )
            portfolio_returns.loc[date] = portfolio_return
        
        # Calculate cumulative returns
        cumulative_returns = (1 + portfolio_returns).cumprod()
        
        # Calculate metrics
        total_return = cumulative_returns.iloc[-1] - 1
        annualized_return = (1 + total_return) ** (252 / len(portfolio_returns)) - 1
        volatility = portfolio_returns.std() * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Calculate drawdown
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Calculate win rate (if we had signals)
        positive_days = (portfolio_returns > 0).sum()
        win_rate = positive_days / len(portfolio_returns) if len(portfolio_returns) > 0 else 0
        
        results = {
            "total_return": float(total_return),
            "annualized_return": float(annualized_return),
            "volatility": float(volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "max_drawdown": float(max_drawdown),
            "win_rate": float(win_rate),
            "total_days": len(portfolio_returns),
            "positive_days": int(positive_days),
            "start_date": str(portfolio_returns.index[0]),
            "end_date": str(portfolio_returns.index[-1]),
            "allocations": normalized_allocations,
            "cumulative_returns": cumulative_returns.to_dict()
        }
        
        self.logger.info(
            f"Backtest complete: Return={total_return:.2%}, "
            f"Sharpe={sharpe_ratio:.2f}, MaxDD={max_drawdown:.2%}"
        )
        
        return results
    
    def print_backtest_results(self, results: Dict):
        """Print formatted backtest results"""
        print("\n" + "="*60)
        print("BACKTEST RESULTS")
        print("="*60)
        print(f"\nPeriod: {results['start_date']} to {results['end_date']}")
        print(f"Total Days: {results['total_days']}")
        
        print("\nPerformance Metrics:")
        print(f"  Total Return:      {results['total_return']:.2%}")
        print(f"  Annualized Return: {results['annualized_return']:.2%}")
        print(f"  Volatility:        {results['volatility']:.2%}")
        print(f"  Sharpe Ratio:      {results['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown:      {results['max_drawdown']:.2%}")
        print(f"  Win Rate:          {results['win_rate']:.2%} ({results['positive_days']}/{results['total_days']} days)")
        
        print("\nAllocations:")
        for symbol, allocation in results['allocations'].items():
            print(f"  {symbol:6s}: {allocation*100:6.2f}%")
        
        print("="*60 + "\n")

