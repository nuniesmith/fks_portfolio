"""
FastAPI routes for portfolio dashboard
Provides REST API endpoints for web dashboard
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

from ..data.manager import DataManager
from ..data.btc_converter import BTCConverter
from ..data.asset_config import AssetConfigManager
from ..portfolio.portfolio import Portfolio
from ..portfolio.portfolio_value import PortfolioValueTracker
from ..portfolio.asset_categories import AssetCategorizer
from ..optimization.correlation import CorrelationAnalyzer
from ..portfolio.rebalancing import PortfolioRebalancer
from .signal_routes import router as signal_router
from .guidance_routes import router as guidance_router
from .ai_routes import router as ai_router
from .dashboard_routes import router as dashboard_router
from .allocation_routes import router as allocation_router


# Pydantic models for request/response
class PortfolioValueResponse(BaseModel):
    total_btc: float
    holdings_btc: Dict[str, float]
    btc_allocation: float
    timestamp: str


class AssetPriceResponse(BaseModel):
    symbol: str
    price_usd: Optional[float]
    price_btc: Optional[float]
    change_24h: Optional[float]


class CorrelationResponse(BaseModel):
    symbol: str
    correlation_to_btc: float


class RebalancingAction(BaseModel):
    symbol: str
    action: str  # "buy" or "sell"
    amount: float
    current_amount: float


class RebalancingPlanResponse(BaseModel):
    target_btc_allocation: float
    current_btc_allocation: float
    actions: List[RebalancingAction]


def create_app() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title="FKS Portfolio API",
        description="API for portfolio management and dashboard",
        version="0.1.0"
    )
    
    # CORS middleware for web dashboard
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify actual origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include signal routes
    app.include_router(signal_router)
    app.include_router(guidance_router)
    app.include_router(ai_router)
    app.include_router(dashboard_router)
    app.include_router(allocation_router)
    
    # Initialize services
    data_manager = DataManager()
    btc_converter = BTCConverter(data_manager=data_manager)
    config_manager = AssetConfigManager()
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "service": "FKS Portfolio API",
            "version": "0.1.0",
            "status": "running"
        }
    
    @app.get("/health")
    async def health():
        """Health check endpoint"""
        try:
            # Quick check that data manager is accessible
            _ = data_manager.adapters
            return {
                "status": "healthy",
                "service": "FKS Portfolio API",
                "version": "0.1.0",
                "port": 8012
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(status_code=503, detail="Service unhealthy")
    
    @app.get("/ready")
    async def ready():
        """Readiness check endpoint"""
        try:
            # Check if critical services are ready
            _ = data_manager.adapters
            _ = config_manager.get_enabled_assets()
            return {
                "status": "ready",
                "service": "FKS Portfolio API",
                "dependencies": {
                    "data_manager": "ready",
                    "config_manager": "ready"
                }
            }
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            raise HTTPException(status_code=503, detail="Service not ready")
    
    @app.get("/api/assets/prices")
    async def get_asset_prices(symbols: Optional[str] = None):
        """
        Get current prices for assets
        
        Args:
            symbols: Comma-separated list of symbols (default: all enabled)
        
        Returns:
            List of asset prices
        """
        try:
            if symbols:
                symbol_list = [s.strip().upper() for s in symbols.split(",")]
            else:
                # Get enabled assets
                enabled = config_manager.get_enabled_assets()
                symbol_list = [a.symbol for a in enabled]
            
            prices = data_manager.fetch_multiple_prices(symbol_list)
            
            results = []
            btc_price = btc_converter.get_btc_price()
            
            for symbol, usd_price in prices.items():
                if usd_price is None:
                    continue
                
                # Convert to BTC
                btc_price_asset = btc_converter.to_btc(1.0, symbol) if btc_price else None
                
                # TODO: Calculate 24h change (would need historical data)
                results.append(AssetPriceResponse(
                    symbol=symbol,
                    price_usd=usd_price,
                    price_btc=btc_price_asset,
                    change_24h=None
                ))
            
            return results
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/portfolio/value")
    async def get_portfolio_value(
        allocations: Optional[str] = None
    ):
        """
        Get portfolio value in BTC terms
        
        Args:
            allocations: JSON string of allocations (default: sample portfolio)
        
        Returns:
            Portfolio value breakdown
        """
        try:
            # Create portfolio from allocations or use default
            portfolio = Portfolio()
            
            if allocations:
                # Parse allocations JSON
                import json
                alloc_dict = json.loads(allocations)
                # Add assets based on allocations
                # This is simplified - in production, would use actual asset data
                from ..portfolio.asset import CryptoAsset, StockAsset
                for symbol, alloc in alloc_dict.items():
                    if symbol == "BTC":
                        portfolio.add_asset(
                            CryptoAsset("BTC", volatility=0.6, correlation_to_btc=1.0),
                            allocation=alloc
                        )
                    elif symbol in ["ETH", "SOL"]:
                        portfolio.add_asset(
                            CryptoAsset(symbol, volatility=0.7, correlation_to_btc=0.8),
                            allocation=alloc
                        )
                    else:
                        portfolio.add_asset(
                            StockAsset(symbol, sector="Diversified", volatility=0.2, correlation_to_btc=0.3),
                            allocation=alloc
                        )
            else:
                # Default sample portfolio
                from ..portfolio.asset import CryptoAsset, StockAsset
                portfolio.add_asset(CryptoAsset("BTC", volatility=0.6, correlation_to_btc=1.0), 0.5)
                portfolio.add_asset(CryptoAsset("ETH", volatility=0.7, correlation_to_btc=0.8), 0.2)
                portfolio.add_asset(StockAsset("SPY", sector="Diversified", volatility=0.2, correlation_to_btc=0.3), 0.15)
            
            tracker = PortfolioValueTracker(portfolio, btc_converter=btc_converter)
            value = tracker.calculate_current_value_btc()
            
            return PortfolioValueResponse(
                total_btc=value["total_btc"],
                holdings_btc=value["holdings_btc"],
                btc_allocation=value["btc_allocation"],
                timestamp=value["timestamp"].isoformat()
            )
        except Exception as e:
            logger.error(f"Error calculating portfolio value: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/correlation/btc")
    async def get_btc_correlations(
        symbols: str,
        lookback_days: int = 90
    ):
        """
        Get correlation to BTC for symbols
        
        Args:
            symbols: Comma-separated list of symbols
            lookback_days: Number of days to look back
        
        Returns:
            List of correlations
        """
        try:
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
            analyzer = CorrelationAnalyzer(data_manager=data_manager)
            correlations = analyzer.calculate_btc_correlations(symbol_list, lookback_days)
            
            results = [
                CorrelationResponse(symbol=symbol, correlation_to_btc=corr)
                for symbol, corr in correlations.items()
            ]
            
            return results
        except Exception as e:
            logger.error(f"Error calculating correlations: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/correlation/matrix")
    async def get_correlation_matrix(
        symbols: str,
        lookback_days: int = 90
    ):
        """
        Get full correlation matrix
        
        Args:
            symbols: Comma-separated list of symbols
            lookback_days: Number of days to look back
        
        Returns:
            Correlation matrix as dictionary
        """
        try:
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
            analyzer = CorrelationAnalyzer(data_manager=data_manager)
            matrix = analyzer.calculate_correlation_matrix(symbol_list, lookback_days)
            
            if matrix.empty:
                return {"matrix": {}, "symbols": symbol_list}
            
            # Convert to dictionary format
            matrix_dict = matrix.to_dict()
            
            return {
                "matrix": matrix_dict,
                "symbols": symbol_list
            }
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/diversification/score")
    async def get_diversification_score(symbols: str):
        """
        Get diversification score for portfolio
        
        Args:
            symbols: Comma-separated list of symbols
        
        Returns:
            Diversification metrics
        """
        try:
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
            categorizer = AssetCategorizer()
            
            score = categorizer.get_diversification_score(symbol_list)
            is_diversified = categorizer.is_diversified(symbol_list)
            suggestions = categorizer.suggest_diversification(symbol_list)
            
            return {
                "score": score,
                "is_diversified": is_diversified,
                "suggestions": suggestions,
                "symbols": symbol_list
            }
        except Exception as e:
            logger.error(f"Error calculating diversification: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/rebalancing/plan")
    async def get_rebalancing_plan(
        allocations: str,
        target_btc_pct: float = 0.5
    ):
        """
        Get rebalancing plan
        
        Args:
            allocations: JSON string of current allocations
            target_btc_pct: Target BTC allocation (0.0 to 1.0)
        
        Returns:
            Rebalancing plan
        """
        try:
            import json
            current_allocations = json.loads(allocations)
            
            # Create portfolio
            portfolio = Portfolio()
            from ..portfolio.asset import CryptoAsset, StockAsset
            for symbol, alloc in current_allocations.items():
                if symbol == "BTC":
                    portfolio.add_asset(
                        CryptoAsset("BTC", volatility=0.6, correlation_to_btc=1.0),
                        allocation=alloc
                    )
                elif symbol in ["ETH", "SOL"]:
                    portfolio.add_asset(
                        CryptoAsset(symbol, volatility=0.7, correlation_to_btc=0.8),
                        allocation=alloc
                    )
                else:
                    portfolio.add_asset(
                        StockAsset(symbol, sector="Diversified", volatility=0.2, correlation_to_btc=0.3),
                        allocation=alloc
                    )
            
            rebalancer = PortfolioRebalancer(
                portfolio,
                target_btc_pct=target_btc_pct,
                btc_converter=btc_converter
            )
            
            current_btc = rebalancer.get_current_btc_allocation()
            actions = rebalancer.rebalance_to_btc_target(current_allocations)
            
            action_list = []
            for symbol, amount in actions.items():
                if amount != 0:
                    action_list.append(RebalancingAction(
                        symbol=symbol,
                        action="buy" if amount > 0 else "sell",
                        amount=abs(amount),
                        current_amount=current_allocations.get(symbol, 0.0)
                    ))
            
            return RebalancingPlanResponse(
                target_btc_allocation=target_btc_pct,
                current_btc_allocation=current_btc,
                actions=action_list
            )
        except Exception as e:
            logger.error(f"Error calculating rebalancing plan: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/assets/enabled")
    async def get_enabled_assets():
        """Get list of enabled assets"""
        try:
            enabled = config_manager.get_enabled_assets()
            return {
                "assets": [
                    {
                        "symbol": a.symbol,
                        "priority": a.priority,
                        "adapters": a.adapters,
                        "collection_interval": a.collection_interval,
                        "last_collected": a.last_collected.isoformat() if a.last_collected else None
                    }
                    for a in enabled
                ]
            }
        except Exception as e:
            logger.error(f"Error fetching enabled assets: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return app

