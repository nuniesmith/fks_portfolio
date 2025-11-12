"""
Portfolio Tracking and Decision Logging
Tracks portfolio performance and trading decisions
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from loguru import logger

from ..signals.trading_signal import TradingSignal
from .decision_support import DecisionRecommendation
from ..data.btc_converter import BTCConverter
from ..data.manager import DataManager


@dataclass
class DecisionLog:
    """Log entry for a trading decision"""
    timestamp: datetime
    signal: Dict[str, Any]
    recommendation: str
    decision: str  # "executed", "rejected", "pending"
    execution_price: Optional[float] = None
    execution_notes: Optional[str] = None
    outcome: Optional[str] = None  # "profit", "loss", "pending"
    pnl_btc: Optional[float] = None
    pnl_pct: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


class PortfolioTracker:
    """Tracks portfolio performance and decisions"""
    
    def __init__(
        self,
        log_file: str = "data/logs/decisions.json",
        btc_converter: Optional[BTCConverter] = None,
        data_manager: Optional[DataManager] = None
    ):
        """
        Initialize portfolio tracker
        
        Args:
            log_file: Path to decision log file
            btc_converter: BTCConverter instance
            data_manager: DataManager instance
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.btc_converter = btc_converter or BTCConverter(data_manager=data_manager)
        self.data_manager = data_manager or DataManager()
        self.logger = logger.bind(component="PortfolioTracker")
        self._load_logs()
    
    def _load_logs(self):
        """Load decision logs from file"""
        self.decision_logs: List[DecisionLog] = []
        
        if self.log_file.exists():
            try:
                with open(self.log_file, "r") as f:
                    data = json.load(f)
                    for entry in data:
                        entry["timestamp"] = datetime.fromisoformat(entry["timestamp"])
                        self.decision_logs.append(DecisionLog(**entry))
                self.logger.info(f"Loaded {len(self.decision_logs)} decision logs")
            except Exception as e:
                self.logger.error(f"Error loading logs: {e}")
                self.decision_logs = []
        else:
            self.decision_logs = []
    
    def _save_logs(self):
        """Save decision logs to file"""
        try:
            data = [log.to_dict() for log in self.decision_logs]
            with open(self.log_file, "w") as f:
                json.dump(data, f, indent=2)
            self.logger.debug(f"Saved {len(self.decision_logs)} decision logs")
        except Exception as e:
            self.logger.error(f"Error saving logs: {e}")
    
    def log_decision(
        self,
        signal: TradingSignal,
        recommendation: DecisionRecommendation,
        decision: str,
        execution_price: Optional[float] = None,
        execution_notes: Optional[str] = None
    ):
        """
        Log a trading decision
        
        Args:
            signal: Trading signal
            recommendation: Decision recommendation
            decision: Decision made ("executed", "rejected", "pending")
            execution_price: Execution price if executed
            execution_notes: Optional notes
        """
        log_entry = DecisionLog(
            timestamp=datetime.now(),
            signal=signal.to_dict(),
            recommendation=recommendation.recommendation.value,
            decision=decision,
            execution_price=execution_price,
            execution_notes=execution_notes,
            outcome="pending" if decision == "executed" else None
        )
        
        self.decision_logs.append(log_entry)
        self._save_logs()
        
        self.logger.info(f"Logged decision: {decision} for {signal.symbol}")
    
    def update_decision_outcome(
        self,
        signal: TradingSignal,
        outcome: str,
        pnl_btc: Optional[float] = None,
        pnl_pct: Optional[float] = None
    ):
        """
        Update decision outcome
        
        Args:
            signal: Trading signal
            outcome: Outcome ("profit", "loss", "pending")
            pnl_btc: P&L in BTC
            pnl_pct: P&L percentage
        """
        # Find matching log entry
        for log in self.decision_logs:
            if (log.signal.get("symbol") == signal.symbol and
                log.signal.get("timestamp") == signal.timestamp.isoformat()):
                log.outcome = outcome
                log.pnl_btc = pnl_btc
                log.pnl_pct = pnl_pct
                self._save_logs()
                self.logger.info(f"Updated outcome for {signal.symbol}: {outcome}")
                return
        
        self.logger.warning(f"No log entry found for {signal.symbol}")
    
    def get_decision_history(
        self,
        days: int = 30,
        symbol: Optional[str] = None
    ) -> List[DecisionLog]:
        """
        Get decision history
        
        Args:
            days: Number of days to look back
            symbol: Optional symbol filter
        
        Returns:
            List of decision logs
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        filtered = [
            log for log in self.decision_logs
            if log.timestamp >= cutoff_date
        ]
        
        if symbol:
            filtered = [
                log for log in filtered
                if log.signal.get("symbol") == symbol.upper()
            ]
        
        return sorted(filtered, key=lambda x: x.timestamp, reverse=True)
    
    def get_performance_metrics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get performance metrics
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Performance metrics dictionary
        """
        history = self.get_decision_history(days=days)
        executed = [log for log in history if log.decision == "executed"]
        completed = [log for log in executed if log.outcome and log.outcome != "pending"]
        
        if not completed:
            return {
                "total_decisions": len(history),
                "executed": len(executed),
                "completed": 0,
                "win_rate": 0.0,
                "total_pnl_btc": 0.0,
                "avg_pnl_pct": 0.0
            }
        
        wins = [log for log in completed if log.outcome == "profit"]
        losses = [log for log in completed if log.outcome == "loss"]
        
        total_pnl_btc = sum(log.pnl_btc or 0.0 for log in completed)
        avg_pnl_pct = sum(log.pnl_pct or 0.0 for log in completed) / len(completed) if completed else 0.0
        
        return {
            "total_decisions": len(history),
            "executed": len(executed),
            "completed": len(completed),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": len(wins) / len(completed) if completed else 0.0,
            "total_pnl_btc": total_pnl_btc,
            "avg_pnl_pct": avg_pnl_pct
        }
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """Get decision statistics"""
        if not self.decision_logs:
            return {
                "total_decisions": 0,
                "by_recommendation": {},
                "by_decision": {},
                "by_outcome": {}
            }
        
        stats = {
            "total_decisions": len(self.decision_logs),
            "by_recommendation": {},
            "by_decision": {},
            "by_outcome": {}
        }
        
        for log in self.decision_logs:
            # Count by recommendation
            rec = log.recommendation
            stats["by_recommendation"][rec] = stats["by_recommendation"].get(rec, 0) + 1
            
            # Count by decision
            decision = log.decision
            stats["by_decision"][decision] = stats["by_decision"].get(decision, 0) + 1
            
            # Count by outcome
            if log.outcome:
                outcome = log.outcome
                stats["by_outcome"][outcome] = stats["by_outcome"].get(outcome, 0) + 1
        
        return stats
    
    def print_performance_report(self, days: int = 30):
        """Print performance report"""
        metrics = self.get_performance_metrics(days=days)
        stats = self.get_decision_statistics()
        
        print("\n" + "="*80)
        print("PORTFOLIO PERFORMANCE REPORT")
        print("="*80)
        print(f"Period: Last {days} days")
        print(f"\nDecisions:")
        print(f"  Total: {metrics['total_decisions']}")
        print(f"  Executed: {metrics['executed']}")
        print(f"  Completed: {metrics['completed']}")
        
        if metrics['completed'] > 0:
            print(f"\nPerformance:")
            print(f"  Wins: {metrics['wins']}")
            print(f"  Losses: {metrics['losses']}")
            print(f"  Win Rate: {metrics['win_rate']:.1%}")
            print(f"  Total P&L: {metrics['total_pnl_btc']:.8f} BTC")
            print(f"  Avg P&L: {metrics['avg_pnl_pct']:.2%}")
        
        print(f"\nRecommendations:")
        for rec, count in stats['by_recommendation'].items():
            print(f"  {rec}: {count}")
        
        print("="*80)

