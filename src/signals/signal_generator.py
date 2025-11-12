"""
Signal Generator
High-level interface for generating and managing trading signals
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from loguru import logger

from ..data.manager import DataManager
from ..data.asset_config import AssetConfigManager
from ..risk.bias_detection import BiasDetector
from .signal_engine import SignalEngine
from .trading_signal import TradingSignal, SignalType
from .trade_categories import TradeCategory, TradeCategoryClassifier


class SignalGenerator:
    """High-level signal generator with bias detection"""
    
    def __init__(
        self,
        data_manager: Optional[DataManager] = None,
        config_manager: Optional[AssetConfigManager] = None
    ):
        """
        Initialize signal generator
        
        Args:
            data_manager: DataManager instance
            config_manager: AssetConfigManager instance
        """
        self.data_manager = data_manager or DataManager()
        self.config_manager = config_manager or AssetConfigManager()
        self.signal_engine = SignalEngine(data_manager=self.data_manager)
        self.bias_detector = BiasDetector()
        self.logger = logger.bind(component="SignalGenerator")
    
    async def generate_daily_signals(
        self,
        category: TradeCategory = TradeCategory.SWING,
        symbols: Optional[List[str]] = None,
        ai_enhanced: bool = False
    ) -> List[TradingSignal]:
        """
        Generate daily trading signals
        
        Args:
            category: Trade category
            symbols: Optional list of symbols (default: enabled assets)
            ai_enhanced: Whether to enhance signals with AI (default: False)
        
        Returns:
            List of trading signals (with bias filtering and optional AI enhancement)
        """
        if symbols is None:
            # Get enabled assets
            enabled = self.config_manager.get_enabled_assets()
            symbols = [a.symbol for a in enabled]
        
        self.logger.info(f"Generating {category.value} signals for {len(symbols)} symbols (AI enhanced: {ai_enhanced})")
        
        # Generate signals
        signals = self.signal_engine.generate_signals_for_portfolio(
            symbols, category, lookback_days=30
        )
        
        # Filter by bias detection
        filtered_signals = []
        for signal in signals:
            # Check for biases
            biases = self._check_signal_biases(signal)
            signal.bias_flags = biases
            
            # Only include signals without high-severity biases
            high_severity_biases = [b for b in biases if hasattr(b, 'severity') and b.severity == "high"]
            if not high_severity_biases:
                filtered_signals.append(signal)
            else:
                self.logger.debug(f"Filtered out {signal.symbol} due to biases: {high_severity_biases}")
        
        # Enhance with AI if requested
        if ai_enhanced and filtered_signals:
            try:
                from ..ai.signal_refiner import AISignalRefiner
                refiner = AISignalRefiner()
                
                self.logger.info(f"Enhancing {len(filtered_signals)} signals with AI...")
                enhanced_signals = await refiner.refine_signals(filtered_signals)
                filtered_signals = enhanced_signals
                self.logger.info(f"AI enhancement complete: {len(filtered_signals)} signals")
            except Exception as e:
                self.logger.error(f"AI enhancement failed: {e}, using baseline signals")
        
        self.logger.info(f"Generated {len(filtered_signals)} valid signals (filtered from {len(signals)})")
        
        return filtered_signals
    
    def _check_signal_biases(self, signal: TradingSignal) -> list:
        """Check signal for biases"""
        biases = []
        
        # Check position sizing
        if signal.position_size_pct > 0.02:
            bias = self.bias_detector.check_position_sizing(
                signal.position_size_pct,
                0.02
            )
            if bias:
                biases.append(bias)
        
        # Check risk/reward
        if signal.risk_reward_ratio < 1.0:
            # Low risk/reward might indicate overconfidence
            bias = self.bias_detector.check_overconfidence(
                recent_wins=0,  # Would need historical data
                win_rate=0.5
            )
            if bias:
                biases.append(bias)
        
        return biases
    
    def get_signals_by_category(
        self,
        symbols: Optional[List[str]] = None
    ) -> Dict[TradeCategory, List[TradingSignal]]:
        """
        Get signals for all categories
        
        Args:
            symbols: Optional list of symbols
        
        Returns:
            Dictionary mapping category to signals
        """
        signals_by_category = {}
        
        for category in TradeCategoryClassifier.get_all_categories():
            # Note: This method is not async, so we can't use await here
            # In practice, this should be called from an async context
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                signals = loop.run_until_complete(self.generate_daily_signals(category, symbols))
            except RuntimeError:
                # No event loop, create new one
                signals = asyncio.run(self.generate_daily_signals(category, symbols))
            signals_by_category[category] = signals
        
        return signals_by_category
    
    def get_best_signals(
        self,
        category: TradeCategory,
        limit: int = 5,
        symbols: Optional[List[str]] = None
    ) -> List[TradingSignal]:
        """
        Get best signals for category
        
        Args:
            category: Trade category
            limit: Maximum number of signals
            symbols: Optional list of symbols
        
        Returns:
            List of best signals (sorted by confidence)
        """
        # Note: This method is not async, so we can't use await here
        # In practice, this should be called from an async context
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            signals = loop.run_until_complete(self.generate_daily_signals(category, symbols))
        except RuntimeError:
            # No event loop, create new one
            signals = asyncio.run(self.generate_daily_signals(category, symbols))
        return signals[:limit]
    
    def get_signal_summary(self, signals: List[TradingSignal]) -> dict:
        """
        Get summary of signals
        
        Args:
            signals: List of trading signals
        
        Returns:
            Summary dictionary
        """
        if not signals:
            return {
                "total": 0,
                "by_type": {},
                "by_category": {},
                "by_strength": {},
                "avg_confidence": 0.0,
                "avg_risk_reward": 0.0
            }
        
        summary = {
            "total": len(signals),
            "by_type": {},
            "by_category": {},
            "by_strength": {},
            "avg_confidence": sum(s.confidence for s in signals) / len(signals),
            "avg_risk_reward": sum(s.risk_reward_ratio for s in signals) / len(signals)
        }
        
        # Count by type
        for signal in signals:
            signal_type = signal.signal_type.value
            summary["by_type"][signal_type] = summary["by_type"].get(signal_type, 0) + 1
        
        # Count by category
        for signal in signals:
            category = signal.category.value
            summary["by_category"][category] = summary["by_category"].get(category, 0) + 1
        
        # Count by strength
        for signal in signals:
            strength = signal.strength.value
            summary["by_strength"][strength] = summary["by_strength"].get(strength, 0) + 1
        
        return summary
    
    def print_signals(self, signals: List[TradingSignal]):
        """Print formatted signal list"""
        if not signals:
            print("\nNo signals generated")
            return
        
        print("\n" + "="*80)
        print(f"TRADING SIGNALS ({len(signals)} total)")
        print("="*80)
        
        for i, signal in enumerate(signals, 1):
            print(f"\n{i}. {signal.symbol} - {signal.signal_type.value.upper()} ({signal.category.value})")
            print(f"   Entry:    ${signal.entry_price:.2f}")
            print(f"   TP:       ${signal.take_profit:.2f} (+{signal.take_profit_pct:.2f}%)")
            print(f"   SL:       ${signal.stop_loss:.2f} (-{signal.stop_loss_pct:.2f}%)")
            print(f"   R/R:      {signal.risk_reward_ratio:.2f}")
            print(f"   Size:     {signal.position_size_pct:.2%}")
            print(f"   Strength: {signal.strength.value}")
            print(f"   Confidence: {signal.confidence:.2%}")
            if signal.bias_flags:
                print(f"   ⚠ Biases: {len(signal.bias_flags)} detected")
        
        print("\n" + "="*80)

