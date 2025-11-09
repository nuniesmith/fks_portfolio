"""
Portfolio Platform CLI
Command-line interface for portfolio optimization and management
"""
import argparse
import json
import sys
from pathlib import Path
import pandas as pd
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.portfolio.portfolio import Portfolio
from src.portfolio.asset import CryptoAsset, StockAsset, CashAsset
from src.data.fetchers import CryptoFetcher, YahooFinanceFetcher
from src.optimization.mean_variance import MeanVarianceOptimizer
from src.risk.report import RiskReportGenerator
from src.backtesting.simple_backtest import SimpleBacktest


def setup_logging(log_level: str = "INFO"):
    """Configure logging"""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level
    )
    logger.add(
        "portfolio.log",
        rotation="10 MB",
        retention="7 days",
        level=log_level
    )


def test_data_fetching():
    """Test data fetching functionality"""
    logger.info("Testing data fetchers...")
    
    # Test BTC
    btc_fetcher = CryptoFetcher()
    btc_price = btc_fetcher.fetch_price("BTC")
    if btc_price:
        logger.success(f"✓ BTC Price: ${btc_price:,.2f}")
    else:
        logger.error("✗ Failed to fetch BTC price")
    
    # Test SPY
    spy_fetcher = YahooFinanceFetcher()
    spy_price = spy_fetcher.fetch_price("SPY")
    if spy_price:
        logger.success(f"✓ SPY Price: ${spy_price:,.2f}")
    else:
        logger.error("✗ Failed to fetch SPY price")
    
    return btc_price is not None and spy_price is not None


def create_sample_portfolio():
    """Create a sample portfolio for testing"""
    logger.info("Creating sample portfolio...")
    
    portfolio = Portfolio()
    
    # Add BTC (50%)
    btc = CryptoAsset(
        symbol="BTC",
        volatility=0.60,
        correlation_to_btc=1.0,
        expected_return=0.15
    )
    portfolio.add_asset(btc, allocation=0.50)
    
    # Add ETH (20%)
    eth = CryptoAsset(
        symbol="ETH",
        volatility=0.70,
        correlation_to_btc=0.80,
        expected_return=0.18
    )
    portfolio.add_asset(eth, allocation=0.20)
    
    # Add SPY (15%)
    spy = StockAsset(
        symbol="SPY",
        sector="Diversified",
        volatility=0.20,
        correlation_to_btc=0.30,
        expected_return=0.10
    )
    portfolio.add_asset(spy, allocation=0.15)
    
    # Add SOL (10%)
    sol = CryptoAsset(
        symbol="SOL",
        volatility=0.80,
        correlation_to_btc=0.70,
        expected_return=0.20
    )
    portfolio.add_asset(sol, allocation=0.10)
    
    # Add Cash (5%)
    cash = CashAsset()
    portfolio.add_asset(cash, allocation=0.05)
    
    # Validate
    valid, error = portfolio.validate_allocations()
    if valid:
        logger.success("✓ Portfolio allocations valid")
    else:
        logger.error(f"✗ Portfolio validation failed: {error}")
    
    btc_valid, btc_error = portfolio.check_btc_constraints()
    if btc_valid:
        logger.success("✓ BTC constraints met")
    else:
        logger.error(f"✗ BTC constraints failed: {btc_error}")
    
    return portfolio


def print_portfolio_summary(portfolio: Portfolio):
    """Print portfolio summary"""
    summary = portfolio.get_portfolio_summary()
    
    print("\n" + "="*60)
    print("PORTFOLIO SUMMARY")
    print("="*60)
    print(f"Total Assets: {summary['total_assets']}")
    print(f"Total Allocation: {summary['total_allocation']*100:.2f}%")
    print(f"BTC Allocation: {summary['btc_allocation']*100:.2f}%")
    print(f"\nAllocations:")
    for symbol, allocation in summary['allocations'].items():
        print(f"  {symbol:6s}: {allocation*100:6.2f}%")
    print("="*60 + "\n")
    
    if summary['allocations_error']:
        logger.warning(f"Allocation error: {summary['allocations_error']}")
    if summary['btc_constraints_error']:
        logger.warning(f"BTC constraint error: {summary['btc_constraints_error']}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="FKS Portfolio Platform CLI")
    parser.add_argument(
        "--test-data",
        action="store_true",
        help="Test data fetching"
    )
    parser.add_argument(
        "--create-portfolio",
        action="store_true",
        help="Create and display sample portfolio"
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Run portfolio optimization (requires historical data)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    logger.info("FKS Portfolio Platform CLI")
    logger.info("="*60)
    
    # Test data fetching
    if args.test_data:
        success = test_data_fetching()
        sys.exit(0 if success else 1)
    
    # Create sample portfolio
    if args.create_portfolio:
        portfolio = create_sample_portfolio()
        print_portfolio_summary(portfolio)
        sys.exit(0)
    
    # Optimize portfolio
    if args.optimize:
        logger.info("Running portfolio optimization and backtest...")
        
        # Create sample portfolio
        portfolio = create_sample_portfolio()
        
        # Fetch historical data
        backtest = SimpleBacktest()
        symbols = list(portfolio.assets.keys())
        
        try:
            historical_prices = backtest.fetch_historical_data(symbols, days=365)
            
            # Calculate returns
            returns = backtest.calculate_returns(historical_prices)
            
            # Run optimization
            optimizer = MeanVarianceOptimizer()
            result = optimizer.optimize(returns, method="max_sharpe")
            
            logger.success("Optimization complete!")
            print("\n" + "="*60)
            print("OPTIMIZATION RESULTS")
            print("="*60)
            print(f"Expected Return: {result['expected_return']:.2%}")
            print(f"Volatility:      {result['volatility']:.2%}")
            print(f"Sharpe Ratio:    {result['sharpe_ratio']:.2f}")
            print("\nOptimized Allocations:")
            for symbol, weight in sorted(result['weights'].items(), key=lambda x: x[1], reverse=True):
                if weight > 0.001:  # Only show significant allocations
                    print(f"  {symbol:6s}: {weight*100:6.2f}%")
            print("="*60)
            
            # Run backtest with optimized allocations
            logger.info("Running backtest with optimized allocations...")
            backtest_results = backtest.backtest_allocation(result['weights'], historical_prices)
            backtest.print_backtest_results(backtest_results)
            
            # Generate risk report
            logger.info("Generating risk report...")
            portfolio_returns = pd.Series({
                date: sum(returns.loc[date, sym] * result['weights'].get(sym, 0) 
                         for sym in returns.columns)
                for date in returns.index
            })
            
            risk_gen = RiskReportGenerator()
            risk_report = risk_gen.generate_report(portfolio_returns)
            risk_gen.print_report(risk_report)
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            logger.info("Make sure dependencies are installed: pip install -r requirements.txt")
            sys.exit(1)
        
        sys.exit(0)
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()

