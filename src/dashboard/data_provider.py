"""
Dashboard Data Provider
Provides aggregated data for dashboard visualization
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from ..data.manager import DataManager
from ..data.asset_config import AssetConfigManager
from ..portfolio.portfolio import Portfolio
from ..portfolio.portfolio_value import PortfolioValueTracker
from ..optimization.correlation import CorrelationAnalyzer
from ..signals.signal_generator import SignalGenerator
from ..signals.trade_categories import TradeCategory


class DashboardDataProvider:
    """Provides data for dashboard visualization"""
    
    def __init__(
        self,
        data_manager: Optional[DataManager] = None,
        config_manager: Optional[AssetConfigManager] = None
    ):
        """
        Initialize dashboard data provider
        
        Args:
            data_manager: DataManager instance
            config_manager: AssetConfigManager instance
        """
        self.data_manager = data_manager or DataManager()
        self.config_manager = config_manager or AssetConfigManager()
        self.signal_generator = SignalGenerator(
            data_manager=self.data_manager,
            config_manager=self.config_manager
        )
        self.logger = logger.bind(component="DashboardDataProvider")
    
    async def get_portfolio_overview(self) -> Dict[str, Any]:
        """
        Get portfolio overview data
        
        Returns:
            Portfolio overview dictionary
        """
        try:
            # Get enabled assets
            enabled_assets = self.config_manager.get_enabled_assets()
            
            # Get recent prices
            asset_prices = {}
            asset_data = {}
            
            for asset in enabled_assets[:10]:  # Limit to top 10 for performance
                try:
                    prices = self.data_manager.get_historical_prices(
                        asset.symbol,
                        days=30
                    )
                    if prices is not None and not prices.empty:
                        latest_price = prices['close'].iloc[-1]
                        asset_prices[asset.symbol] = float(latest_price)
                        
                        # Calculate 24h change
                        if len(prices) >= 2:
                            prev_price = prices['close'].iloc[-2]
                            change_pct = ((latest_price - prev_price) / prev_price) * 100
                            asset_data[asset.symbol] = {
                                "price": float(latest_price),
                                "change_24h": float(change_pct),
                                "volume": float(prices['volume'].iloc[-1]) if 'volume' in prices.columns else 0
                            }
                except Exception as e:
                    self.logger.warning(f"Error getting price for {asset.symbol}: {e}")
                    continue
            
            # Get signal summary
            try:
                signals = await self.signal_generator.generate_daily_signals(
                    TradeCategory.SWING,
                    ai_enhanced=False
                )
                signal_summary = {
                    "total": len(signals),
                    "buy": sum(1 for s in signals if s.signal_type.value == "buy"),
                    "sell": sum(1 for s in signals if s.signal_type.value == "sell"),
                    "avg_confidence": sum(s.confidence for s in signals) / len(signals) if signals else 0.0
                }
            except Exception as e:
                self.logger.warning(f"Error getting signals: {e}")
                signal_summary = {"total": 0, "buy": 0, "sell": 0, "avg_confidence": 0.0}
            
            return {
                "timestamp": datetime.now().isoformat(),
                "assets": {
                    "enabled_count": len(enabled_assets),
                    "tracked": len(asset_data),
                    "prices": asset_data
                },
                "signals": signal_summary,
                "status": "active"
            }
        except Exception as e:
            self.logger.error(f"Error getting portfolio overview: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "error"
            }
    
    async def get_portfolio_performance(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get portfolio performance metrics
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Performance metrics dictionary
        """
        try:
            enabled_assets = self.config_manager.get_enabled_assets()
            
            # Get historical prices for all assets
            performance_data = {}
            
            for asset in enabled_assets[:10]:  # Limit for performance
                try:
                    prices = self.data_manager.get_historical_prices(
                        asset.symbol,
                        days=days
                    )
                    if prices is not None and not prices.empty:
                        start_price = prices['close'].iloc[0]
                        end_price = prices['close'].iloc[-1]
                        return_pct = ((end_price - start_price) / start_price) * 100
                        
                        # Calculate volatility
                        returns = prices['close'].pct_change().dropna()
                        volatility = returns.std() * 100 if len(returns) > 0 else 0.0
                        
                        performance_data[asset.symbol] = {
                            "return_pct": float(return_pct),
                            "volatility": float(volatility),
                            "start_price": float(start_price),
                            "end_price": float(end_price)
                        }
                except Exception as e:
                    self.logger.warning(f"Error calculating performance for {asset.symbol}: {e}")
                    continue
            
            # Calculate aggregate metrics
            if performance_data:
                avg_return = sum(d["return_pct"] for d in performance_data.values()) / len(performance_data)
                avg_volatility = sum(d["volatility"] for d in performance_data.values()) / len(performance_data)
            else:
                avg_return = 0.0
                avg_volatility = 0.0
            
            return {
                "period_days": days,
                "assets": performance_data,
                "aggregate": {
                    "avg_return_pct": avg_return,
                    "avg_volatility": avg_volatility,
                    "asset_count": len(performance_data)
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting portfolio performance: {e}")
            return {
                "period_days": days,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_signal_summary(
        self,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get signal summary for dashboard
        
        Args:
            category: Optional trade category filter
        
        Returns:
            Signal summary dictionary
        """
        try:
            from ..signals.trade_categories import TradeCategory
            
            if category:
                category_map = {
                    "scalp": TradeCategory.SCALP,
                    "intraday": TradeCategory.INTRADAY,
                    "swing": TradeCategory.SWING,
                    "long_term": TradeCategory.LONG_TERM
                }
                trade_category = category_map.get(category.lower(), TradeCategory.SWING)
                categories = [trade_category]
            else:
                categories = [
                    TradeCategory.SCALP,
                    TradeCategory.INTRADAY,
                    TradeCategory.SWING,
                    TradeCategory.LONG_TERM
                ]
            
            summary_by_category = {}
            
            for cat in categories:
                try:
                    signals = await self.signal_generator.generate_daily_signals(
                        cat,
                        ai_enhanced=False
                    )
                    
                    summary_by_category[cat.value] = {
                        "count": len(signals),
                        "buy": sum(1 for s in signals if s.signal_type.value == "buy"),
                        "sell": sum(1 for s in signals if s.signal_type.value == "sell"),
                        "avg_confidence": sum(s.confidence for s in signals) / len(signals) if signals else 0.0,
                        "avg_risk_reward": sum(s.risk_reward_ratio for s in signals) / len(signals) if signals else 0.0
                    }
                except Exception as e:
                    self.logger.warning(f"Error getting signals for {cat.value}: {e}")
                    summary_by_category[cat.value] = {
                        "count": 0,
                        "buy": 0,
                        "sell": 0,
                        "avg_confidence": 0.0,
                        "avg_risk_reward": 0.0
                    }
            
            # Calculate totals
            total_signals = sum(s["count"] for s in summary_by_category.values())
            total_buy = sum(s["buy"] for s in summary_by_category.values())
            total_sell = sum(s["sell"] for s in summary_by_category.values())
            
            return {
                "by_category": summary_by_category,
                "totals": {
                    "count": total_signals,
                    "buy": total_buy,
                    "sell": total_sell
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting signal summary: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_asset_correlation_matrix(
        self,
        symbols: Optional[List[str]] = None,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Get correlation matrix for assets
        
        Args:
            symbols: Optional list of symbols (default: enabled assets)
            days: Number of days for correlation calculation
        
        Returns:
            Correlation matrix dictionary
        """
        try:
            if symbols is None:
                enabled_assets = self.config_manager.get_enabled_assets()
                symbols = [a.symbol for a in enabled_assets[:10]]  # Limit for performance
            
            # Get correlation analyzer
            analyzer = CorrelationAnalyzer(self.data_manager)
            
            # Calculate correlation
            correlation_matrix = analyzer.calculate_correlation_matrix(
                symbols,
                lookback_days=days
            )
            
            # Convert to dictionary format
            if correlation_matrix is not None and not correlation_matrix.empty:
                return {
                    "symbols": list(correlation_matrix.columns),
                    "matrix": correlation_matrix.to_dict(),
                    "period_days": days,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "symbols": symbols,
                    "matrix": {},
                    "period_days": days,
                    "error": "Insufficient data for correlation calculation",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Error getting correlation matrix: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

