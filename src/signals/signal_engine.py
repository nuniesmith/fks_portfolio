"""
Signal Engine
Generates trading signals with entry, TP, SL based on technical analysis
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from loguru import logger

from ..data.manager import DataManager
from .trading_signal import TradingSignal, SignalType, SignalStrength
from .trade_categories import TradeCategory, TradeCategoryClassifier


class SignalEngine:
    """Generates trading signals"""
    
    def __init__(
        self,
        data_manager: Optional[DataManager] = None,
        min_risk_reward: float = 1.5,
        max_position_size_pct: float = 0.02
    ):
        """
        Initialize signal engine
        
        Args:
            data_manager: DataManager instance
            min_risk_reward: Minimum risk/reward ratio (default: 1.5)
            max_position_size_pct: Maximum position size (default: 2%)
        """
        self.data_manager = data_manager or DataManager()
        self.min_risk_reward = min_risk_reward
        self.max_position_size_pct = max_position_size_pct
        self.logger = logger.bind(component="SignalEngine")
    
    def generate_signal(
        self,
        symbol: str,
        category: TradeCategory,
        lookback_days: int = 30
    ) -> Optional[TradingSignal]:
        """
        Generate trading signal for symbol
        
        Args:
            symbol: Asset symbol
            category: Trade category
            lookback_days: Days of historical data to analyze
        
        Returns:
            TradingSignal or None
        """
        try:
            # Fetch historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)
            
            prices_df = self.data_manager.fetch_historical_prices(
                symbol, start_date, end_date, interval="daily"
            )
            
            if prices_df.empty or len(prices_df) < 20:
                self.logger.warning(f"Insufficient data for {symbol}")
                return None
            
            # Get current price
            current_price = self.data_manager.fetch_price(symbol)
            if current_price is None:
                return None
            
            # Calculate technical indicators
            indicators = self._calculate_indicators(prices_df, category)
            
            # Determine signal type
            signal_type = self._determine_signal_type(indicators, category)
            
            if signal_type == SignalType.HOLD:
                return None
            
            # Calculate entry, TP, SL
            entry_price = current_price
            tp_pct, sl_pct = self._calculate_tp_sl(category, indicators)
            
            take_profit = entry_price * (1 + tp_pct / 100) if signal_type == SignalType.BUY else entry_price * (1 - tp_pct / 100)
            stop_loss = entry_price * (1 - sl_pct / 100) if signal_type == SignalType.BUY else entry_price * (1 + sl_pct / 100)
            
            # Calculate risk/reward
            risk_reward = tp_pct / sl_pct if sl_pct > 0 else 0
            
            if risk_reward < self.min_risk_reward:
                self.logger.debug(f"Risk/reward {risk_reward:.2f} below minimum {self.min_risk_reward}")
                return None
            
            # Calculate position size (1-2% risk)
            position_size_pct = min(self.max_position_size_pct, sl_pct / 100)
            
            # Determine signal strength
            strength = self._determine_strength(indicators, risk_reward)
            
            # Calculate confidence
            confidence = self._calculate_confidence(indicators, risk_reward)
            
            # Create signal
            signal = TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                category=category,
                entry_price=entry_price,
                take_profit=take_profit,
                stop_loss=stop_loss,
                take_profit_pct=tp_pct,
                stop_loss_pct=sl_pct,
                risk_reward_ratio=risk_reward,
                position_size_pct=position_size_pct,
                timestamp=datetime.now(),
                strength=strength,
                confidence=confidence,
                indicators=indicators
            )
            
            # Set expiry based on category
            config = TradeCategoryClassifier.get_config(category)
            signal.expiry = datetime.now() + config.time_horizon_max
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    def _calculate_indicators(
        self,
        prices_df: pd.DataFrame,
        category: TradeCategory
    ) -> Dict[str, Any]:
        """Calculate technical indicators"""
        indicators = {}
        
        if prices_df.empty:
            return indicators
        
        closes = prices_df["close"].values
        
        # RSI (14 period)
        indicators["rsi"] = self._calculate_rsi(closes, period=14)
        
        # Moving averages
        indicators["sma_20"] = np.mean(closes[-20:]) if len(closes) >= 20 else None
        indicators["sma_50"] = np.mean(closes[-50:]) if len(closes) >= 50 else None
        indicators["ema_12"] = self._calculate_ema(closes, period=12)
        indicators["ema_26"] = self._calculate_ema(closes, period=26)
        
        # MACD
        if indicators["ema_12"] and indicators["ema_26"]:
            indicators["macd"] = indicators["ema_12"] - indicators["ema_26"]
        else:
            indicators["macd"] = None
        
        # Price position
        current_price = closes[-1]
        high_52w = np.max(closes) if len(closes) >= 252 else np.max(closes)
        low_52w = np.min(closes) if len(closes) >= 252 else np.min(closes)
        indicators["price_position"] = (current_price - low_52w) / (high_52w - low_52w) if high_52w > low_52w else 0.5
        
        # Volatility
        returns = np.diff(closes) / closes[:-1]
        indicators["volatility"] = np.std(returns) * np.sqrt(252) if len(returns) > 0 else None
        
        # Trend
        if indicators["sma_20"] and indicators["sma_50"]:
            indicators["trend"] = "up" if indicators["sma_20"] > indicators["sma_50"] else "down"
        else:
            indicators["trend"] = "neutral"
        
        return indicators
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> Optional[float]:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> Optional[float]:
        """Calculate EMA"""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        
        return float(ema)
    
    def _determine_signal_type(
        self,
        indicators: Dict[str, Any],
        category: TradeCategory
    ) -> SignalType:
        """Determine signal type based on indicators"""
        # Simple logic - can be enhanced
        rsi = indicators.get("rsi")
        macd = indicators.get("macd")
        trend = indicators.get("trend")
        
        # RSI-based signals
        if rsi:
            if rsi < 30:
                return SignalType.BUY
            elif rsi > 70:
                return SignalType.SELL
        
        # MACD-based signals
        if macd:
            if macd > 0 and trend == "up":
                return SignalType.BUY
            elif macd < 0 and trend == "down":
                return SignalType.SELL
        
        # Trend-based
        if trend == "up":
            return SignalType.BUY
        elif trend == "down":
            return SignalType.SELL
        
        return SignalType.HOLD
    
    def _calculate_tp_sl(
        self,
        category: TradeCategory,
        indicators: Dict[str, Any]
    ) -> tuple:
        """Calculate TP and SL percentages"""
        config = TradeCategoryClassifier.get_config(category)
        tp_min, tp_max = config.take_profit_pct
        sl_min, sl_max = config.stop_loss_pct
        
        # Use volatility to adjust TP/SL
        volatility = indicators.get("volatility")
        if volatility:
            # Higher volatility = wider TP/SL
            volatility_factor = min(volatility / 0.3, 2.0)  # Cap at 2x
            tp_pct = tp_min + (tp_max - tp_min) * volatility_factor * 0.5
            sl_pct = sl_min + (sl_max - sl_min) * volatility_factor * 0.5
        else:
            # Default to middle of range
            tp_pct = (tp_min + tp_max) / 2
            sl_pct = (sl_min + sl_max) / 2
        
        return tp_pct, sl_pct
    
    def _determine_strength(
        self,
        indicators: Dict[str, Any],
        risk_reward: float
    ) -> SignalStrength:
        """Determine signal strength"""
        # Count confirming indicators
        confirmations = 0
        
        rsi = indicators.get("rsi")
        macd = indicators.get("macd")
        trend = indicators.get("trend")
        
        if rsi and (rsi < 30 or rsi > 70):
            confirmations += 1
        if macd and abs(macd) > 0:
            confirmations += 1
        if trend != "neutral":
            confirmations += 1
        if risk_reward >= 2.0:
            confirmations += 1
        
        if confirmations >= 3:
            return SignalStrength.VERY_STRONG
        elif confirmations >= 2:
            return SignalStrength.STRONG
        elif confirmations >= 1:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK
    
    def _calculate_confidence(
        self,
        indicators: Dict[str, Any],
        risk_reward: float
    ) -> float:
        """Calculate signal confidence (0.0 to 1.0)"""
        confidence = 0.5  # Base confidence
        
        # RSI confidence
        rsi = indicators.get("rsi")
        if rsi:
            if rsi < 20 or rsi > 80:
                confidence += 0.2
            elif rsi < 30 or rsi > 70:
                confidence += 0.1
        
        # Risk/reward confidence
        if risk_reward >= 3.0:
            confidence += 0.2
        elif risk_reward >= 2.0:
            confidence += 0.1
        
        # Trend confidence
        trend = indicators.get("trend")
        if trend != "neutral":
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def generate_signals_for_portfolio(
        self,
        symbols: List[str],
        category: TradeCategory,
        lookback_days: int = 30
    ) -> List[TradingSignal]:
        """
        Generate signals for multiple symbols
        
        Args:
            symbols: List of symbols
            category: Trade category
            lookback_days: Days of historical data
        
        Returns:
            List of valid trading signals
        """
        signals = []
        for symbol in symbols:
            signal = self.generate_signal(symbol, category, lookback_days)
            if signal and signal.is_valid():
                signals.append(signal)
        
        # Sort by confidence (highest first)
        signals.sort(key=lambda x: x.confidence, reverse=True)
        
        return signals

