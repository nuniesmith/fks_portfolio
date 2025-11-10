"""
Correlation Analysis for Portfolio Diversification
Calculates correlations between assets and BTC
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from loguru import logger

from ..data.manager import DataManager


class CorrelationAnalyzer:
    """Analyzes correlations between assets"""
    
    def __init__(self, data_manager: Optional[DataManager] = None):
        """
        Initialize correlation analyzer
        
        Args:
            data_manager: DataManager instance for fetching historical data
        """
        self.data_manager = data_manager or DataManager()
        self.logger = logger.bind(component="CorrelationAnalyzer")
    
    def calculate_correlation_matrix(
        self,
        symbols: List[str],
        lookback_days: int = 90,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Calculate pairwise correlation matrix
        
        Args:
            symbols: List of asset symbols
            lookback_days: Number of days to look back
            end_date: End date (default: today)
        
        Returns:
            DataFrame with correlation matrix
        """
        if end_date is None:
            end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Fetch historical prices for all symbols
        price_data = {}
        for symbol in symbols:
            data = self.data_manager.fetch_historical_prices(
                symbol, start_date, end_date, interval="daily"
            )
            if not data.empty:
                price_data[symbol] = data.set_index("date")["close"]
        
        if len(price_data) < 2:
            self.logger.warning("Insufficient data for correlation matrix")
            return pd.DataFrame()
        
        # Align all dates (normalize timezone)
        all_dates = set()
        for prices in price_data.values():
            # Convert to timezone-naive if needed
            index = prices.index
            if hasattr(index, 'tz') and index.tz is not None:
                index = index.tz_localize(None)
            all_dates.update(index)
        all_dates = sorted(list(all_dates))
        
        # Create DataFrame with aligned prices
        aligned_data = pd.DataFrame(index=all_dates)
        for symbol, prices in price_data.items():
            aligned_data[symbol] = prices
        
        # Calculate returns
        returns = aligned_data.pct_change().dropna()
        
        # Calculate correlation matrix
        correlation_matrix = returns.corr()
        
        return correlation_matrix
    
    def calculate_btc_correlations(
        self,
        symbols: List[str],
        lookback_days: int = 90,
        end_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Calculate correlation of each asset with BTC
        
        Args:
            symbols: List of asset symbols (should include BTC)
            lookback_days: Number of days to look back
            end_date: End date (default: today)
        
        Returns:
            Dictionary mapping symbol to correlation with BTC
        """
        if "BTC" not in symbols:
            symbols = ["BTC"] + symbols
        
        correlation_matrix = self.calculate_correlation_matrix(
            symbols, lookback_days, end_date
        )
        
        if correlation_matrix.empty or "BTC" not in correlation_matrix.columns:
            return {}
        
        btc_correlations = {}
        for symbol in symbols:
            if symbol != "BTC" and symbol in correlation_matrix.columns:
                btc_correlations[symbol] = correlation_matrix.loc[symbol, "BTC"]
        
        return btc_correlations
    
    def find_low_correlation_assets(
        self,
        symbols: List[str],
        max_correlation: float = 0.5,
        lookback_days: int = 90
    ) -> List[str]:
        """
        Find assets with low correlation to BTC
        
        Args:
            symbols: List of asset symbols to analyze
            max_correlation: Maximum correlation threshold
            lookback_days: Number of days to look back
        
        Returns:
            List of symbols with correlation <= max_correlation
        """
        btc_correlations = self.calculate_btc_correlations(symbols, lookback_days)
        
        low_correlation = [
            symbol for symbol, corr in btc_correlations.items()
            if corr <= max_correlation
        ]
        
        return low_correlation
    
    def get_diversification_metrics(
        self,
        symbols: List[str],
        lookback_days: int = 90
    ) -> Dict[str, float]:
        """
        Calculate diversification metrics
        
        Args:
            symbols: List of asset symbols
            lookback_days: Number of days to look back
        
        Returns:
            Dictionary with diversification metrics
        """
        correlation_matrix = self.calculate_correlation_matrix(symbols, lookback_days)
        
        if correlation_matrix.empty:
            return {}
        
        # Calculate average correlation
        # Exclude diagonal (self-correlation = 1.0)
        mask = np.triu(np.ones_like(correlation_matrix.values), k=1)
        correlations = correlation_matrix.values[mask.astype(bool)]
        avg_correlation = float(np.mean(correlations)) if len(correlations) > 0 else 0.0
        
        # Calculate max correlation (excluding diagonal)
        max_correlation = float(np.max(correlations)) if len(correlations) > 0 else 0.0
        
        # Calculate min correlation
        min_correlation = float(np.min(correlations)) if len(correlations) > 0 else 0.0
        
        # Calculate average correlation to BTC
        btc_correlations = self.calculate_btc_correlations(symbols, lookback_days)
        avg_btc_correlation = (
            np.mean(list(btc_correlations.values()))
            if btc_correlations else 0.0
        )
        
        return {
            "avg_correlation": avg_correlation,
            "max_correlation": max_correlation,
            "min_correlation": min_correlation,
            "avg_btc_correlation": float(avg_btc_correlation),
            "num_assets": len(symbols)
        }
    
    def optimize_for_diversification(
        self,
        candidate_symbols: List[str],
        target_count: int = 5,
        max_btc_correlation: float = 0.5,
        lookback_days: int = 90
    ) -> List[str]:
        """
        Select assets optimized for diversification
        
        Args:
            candidate_symbols: List of candidate symbols
            target_count: Target number of assets
            max_btc_correlation: Maximum correlation to BTC
            lookback_days: Number of days to look back
        
        Returns:
            List of selected symbols
        """
        # Filter by BTC correlation
        low_corr_assets = self.find_low_correlation_assets(
            candidate_symbols, max_btc_correlation, lookback_days
        )
        
        if len(low_corr_assets) <= target_count:
            return low_corr_assets
        
        # If we have more than target, select to minimize inter-asset correlation
        selected = []
        remaining = low_corr_assets.copy()
        
        # Start with asset that has lowest BTC correlation
        btc_correlations = self.calculate_btc_correlations(remaining, lookback_days)
        if btc_correlations:
            first_asset = min(btc_correlations.items(), key=lambda x: x[1])[0]
            selected.append(first_asset)
            remaining.remove(first_asset)
        
        # Greedily add assets with lowest average correlation to selected
        while len(selected) < target_count and remaining:
            best_asset = None
            best_avg_corr = float('inf')
            
            for candidate in remaining:
                # Calculate average correlation to already selected assets
                test_set = selected + [candidate]
                corr_matrix = self.calculate_correlation_matrix(test_set, lookback_days)
                
                if not corr_matrix.empty:
                    # Average correlation to selected assets
                    avg_corr = corr_matrix.loc[candidate, selected].mean()
                    if avg_corr < best_avg_corr:
                        best_avg_corr = avg_corr
                        best_asset = candidate
            
            if best_asset:
                selected.append(best_asset)
                remaining.remove(best_asset)
            else:
                break
        
        return selected
    
    def print_correlation_matrix(self, symbols: List[str], lookback_days: int = 90):
        """Print formatted correlation matrix"""
        matrix = self.calculate_correlation_matrix(symbols, lookback_days)
        
        if matrix.empty:
            print("No correlation data available")
            return
        
        print("\n" + "="*60)
        print("CORRELATION MATRIX")
        print("="*60)
        print(matrix.round(3))
        print("="*60)
        
        # Print BTC correlations
        btc_correlations = self.calculate_btc_correlations(symbols, lookback_days)
        if btc_correlations:
            print("\nCorrelation to BTC:")
            for symbol, corr in sorted(btc_correlations.items(), key=lambda x: x[1]):
                print(f"  {symbol:6s}: {corr:6.3f}")

