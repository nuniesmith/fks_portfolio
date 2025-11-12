"""
Chart Data Generator
Generates data for various chart visualizations
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from ..data.manager import DataManager
from ..data.asset_config import AssetConfigManager


class ChartDataGenerator:
    """Generates chart data for dashboard"""
    
    def __init__(
        self,
        data_manager: Optional[DataManager] = None,
        config_manager: Optional[AssetConfigManager] = None
    ):
        """
        Initialize chart data generator
        
        Args:
            data_manager: DataManager instance
            config_manager: AssetConfigManager instance
        """
        self.data_manager = data_manager or DataManager()
        self.config_manager = config_manager or AssetConfigManager()
        self.logger = logger.bind(component="ChartDataGenerator")
    
    def generate_price_chart_data(
        self,
        symbol: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate price chart data for a symbol
        
        Args:
            symbol: Asset symbol
            days: Number of days of data
        
        Returns:
            Chart data dictionary
        """
        try:
            prices = self.data_manager.get_historical_prices(symbol, days=days)
            
            if prices is None or prices.empty:
                return {
                    "symbol": symbol,
                    "error": "No data available",
                    "data": []
                }
            
            # Prepare chart data
            chart_data = []
            for idx, row in prices.iterrows():
                chart_data.append({
                    "date": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "volume": float(row['volume']) if 'volume' in row else 0
                })
            
            return {
                "symbol": symbol,
                "period_days": days,
                "data_points": len(chart_data),
                "data": chart_data,
                "latest_price": float(prices['close'].iloc[-1]),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error generating price chart for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "data": []
            }
    
    def generate_portfolio_allocation_chart(
        self,
        allocations: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Generate portfolio allocation chart data
        
        Args:
            allocations: Dictionary of symbol -> weight
        
        Returns:
            Chart data for pie/donut chart
        """
        try:
            chart_data = []
            total = sum(allocations.values())
            
            if total == 0:
                return {
                    "error": "No allocations provided",
                    "data": []
                }
            
            # Normalize weights
            for symbol, weight in allocations.items():
                normalized_weight = weight / total if total > 0 else 0
                chart_data.append({
                    "symbol": symbol,
                    "weight": float(normalized_weight),
                    "weight_pct": float(normalized_weight * 100)
                })
            
            # Sort by weight descending
            chart_data.sort(key=lambda x: x["weight"], reverse=True)
            
            return {
                "data": chart_data,
                "total_weight": float(total),
                "asset_count": len(chart_data),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error generating allocation chart: {e}")
            return {
                "error": str(e),
                "data": []
            }
    
    def generate_performance_comparison_chart(
        self,
        symbols: List[str],
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate performance comparison chart data
        
        Args:
            symbols: List of asset symbols
            days: Number of days to compare
        
        Returns:
            Chart data for comparison
        """
        try:
            comparison_data = []
            
            for symbol in symbols:
                try:
                    prices = self.data_manager.get_historical_prices(symbol, days=days)
                    
                    if prices is None or prices.empty:
                        continue
                    
                    # Calculate cumulative returns
                    start_price = prices['close'].iloc[0]
                    returns = []
                    
                    for idx, row in prices.iterrows():
                        current_price = row['close']
                        return_pct = ((current_price - start_price) / start_price) * 100
                        returns.append({
                            "date": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                            "return_pct": float(return_pct),
                            "price": float(current_price)
                        })
                    
                    comparison_data.append({
                        "symbol": symbol,
                        "data": returns,
                        "start_price": float(start_price),
                        "end_price": float(prices['close'].iloc[-1]),
                        "total_return_pct": float(((prices['close'].iloc[-1] - start_price) / start_price) * 100)
                    })
                except Exception as e:
                    self.logger.warning(f"Error processing {symbol} for comparison: {e}")
                    continue
            
            return {
                "symbols": symbols,
                "period_days": days,
                "data": comparison_data,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error generating comparison chart: {e}")
            return {
                "error": str(e),
                "data": []
            }
    
    def generate_signal_distribution_chart(
        self,
        signals: List[Any]
    ) -> Dict[str, Any]:
        """
        Generate signal distribution chart data
        
        Args:
            signals: List of trading signals
        
        Returns:
            Chart data for distribution
        """
        try:
            if not signals:
                return {
                    "error": "No signals provided",
                    "data": []
                }
            
            # Count by category
            by_category = {}
            by_strength = {}
            by_type = {}
            
            for signal in signals:
                # By category
                category = signal.category.value if hasattr(signal.category, 'value') else str(signal.category)
                by_category[category] = by_category.get(category, 0) + 1
                
                # By strength
                strength = signal.strength.value if hasattr(signal.strength, 'value') else str(signal.strength)
                by_strength[strength] = by_strength.get(strength, 0) + 1
                
                # By type
                signal_type = signal.signal_type.value if hasattr(signal.signal_type, 'value') else str(signal.signal_type)
                by_type[signal_type] = by_type.get(signal_type, 0) + 1
            
            return {
                "total": len(signals),
                "by_category": [{"category": k, "count": v} for k, v in by_category.items()],
                "by_strength": [{"strength": k, "count": v} for k, v in by_strength.items()],
                "by_type": [{"type": k, "count": v} for k, v in by_type.items()],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error generating signal distribution: {e}")
            return {
                "error": str(e),
                "data": []
            }

