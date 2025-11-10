"""
Manual Workflow
Guides user through manual trade execution
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from ..signals.trading_signal import TradingSignal
from .decision_support import DecisionRecommendation, RecommendationType


class WorkflowStatus(Enum):
    """Workflow status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class WorkflowStep:
    """Single step in workflow"""
    step_number: int
    title: str
    description: str
    action_required: str
    completed: bool = False
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None


class ManualWorkflow:
    """Manual trade execution workflow"""
    
    def __init__(self):
        """Initialize workflow"""
        self.logger = logger.bind(component="ManualWorkflow")
    
    def create_execution_workflow(
        self,
        signal: TradingSignal,
        recommendation: DecisionRecommendation
    ) -> List[WorkflowStep]:
        """
        Create execution workflow for signal
        
        Args:
            signal: Trading signal
            recommendation: Decision recommendation
        
        Returns:
            List of workflow steps
        """
        steps = []
        
        # Step 1: Review recommendation
        steps.append(WorkflowStep(
            step_number=1,
            title="Review Recommendation",
            description=f"Review {recommendation.recommendation.value} recommendation",
            action_required="Read rationale and check bias warnings"
        ))
        
        # Step 2: Check portfolio allocation
        steps.append(WorkflowStep(
            step_number=2,
            title="Check Portfolio Allocation",
            description="Verify current portfolio allocation and BTC percentage",
            action_required="Check if new position fits portfolio constraints"
        ))
        
        # Step 3: Calculate position size
        steps.append(WorkflowStep(
            step_number=3,
            title="Calculate Position Size",
            description=f"Position size: {signal.position_size_pct:.2%} of portfolio",
            action_required=f"Calculate exact position size based on {signal.position_size_pct:.2%} risk"
        ))
        
        # Step 4: Set entry order
        steps.append(WorkflowStep(
            step_number=4,
            title="Set Entry Order",
            description=f"Entry: ${signal.entry_price:.2f}",
            action_required=f"Place {signal.signal_type.value} order at ${signal.entry_price:.2f}"
        ))
        
        # Step 5: Set take profit
        steps.append(WorkflowStep(
            step_number=5,
            title="Set Take Profit",
            description=f"Take profit: ${signal.take_profit:.2f} (+{signal.take_profit_pct:.2f}%)",
            action_required=f"Set TP order at ${signal.take_profit:.2f}"
        ))
        
        # Step 6: Set stop loss
        steps.append(WorkflowStep(
            step_number=6,
            title="Set Stop Loss",
            description=f"Stop loss: ${signal.stop_loss:.2f} (-{signal.stop_loss_pct:.2f}%)",
            action_required=f"Set SL order at ${signal.stop_loss:.2f} (MANDATORY)"
        ))
        
        # Step 7: Confirm execution
        steps.append(WorkflowStep(
            step_number=7,
            title="Confirm Execution",
            description="Review all orders before confirming",
            action_required="Confirm all orders are set correctly"
        ))
        
        return steps
    
    def create_review_workflow(
        self,
        signals: List[TradingSignal],
        recommendations: List[DecisionRecommendation]
    ) -> List[WorkflowStep]:
        """
        Create review workflow for multiple signals
        
        Args:
            signals: List of signals
            recommendations: List of recommendations
        
        Returns:
            List of workflow steps
        """
        steps = []
        
        # Step 1: Review all signals
        steps.append(WorkflowStep(
            step_number=1,
            title="Review All Signals",
            description=f"Review {len(signals)} generated signals",
            action_required="Review signal summary and recommendations"
        ))
        
        # Step 2: Filter by recommendation
        strong_signals = [r for r in recommendations if r.recommendation == RecommendationType.STRONG_BUY]
        buy_signals = [r for r in recommendations if r.recommendation == RecommendationType.BUY]
        
        steps.append(WorkflowStep(
            step_number=2,
            title="Filter Signals",
            description=f"Strong buy: {len(strong_signals)}, Buy: {len(buy_signals)}",
            action_required="Focus on strong buy and buy recommendations"
        ))
        
        # Step 3: Check portfolio constraints
        steps.append(WorkflowStep(
            step_number=3,
            title="Check Portfolio Constraints",
            description="Verify BTC allocation (50-60%) and individual asset limits (20%)",
            action_required="Ensure new positions don't violate constraints"
        ))
        
        # Step 4: Prioritize signals
        steps.append(WorkflowStep(
            step_number=4,
            title="Prioritize Signals",
            description="Sort by confidence and risk/reward ratio",
            action_required="Select top 3-5 signals for execution"
        ))
        
        return steps
    
    def validate_workflow_step(
        self,
        step: WorkflowStep,
        validation_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Validate workflow step completion
        
        Args:
            step: Workflow step
            validation_data: Optional validation data
        
        Returns:
            True if step is valid
        """
        # Basic validation
        if step.completed and step.completed_at is None:
            return False
        
        # Step-specific validation
        if step.step_number == 6:  # Stop loss step
            # Stop loss is mandatory
            if not step.completed:
                self.logger.warning("Stop loss step must be completed")
                return False
        
        return True
    
    def get_workflow_summary(self, steps: List[WorkflowStep]) -> dict:
        """
        Get workflow summary
        
        Args:
            steps: List of workflow steps
        
        Returns:
            Summary dictionary
        """
        completed = sum(1 for s in steps if s.completed)
        total = len(steps)
        
        return {
            "total_steps": total,
            "completed_steps": completed,
            "progress": completed / total if total > 0 else 0.0,
            "status": "completed" if completed == total else "in_progress",
            "steps": [
                {
                    "step_number": s.step_number,
                    "title": s.title,
                    "completed": s.completed,
                    "completed_at": s.completed_at.isoformat() if s.completed_at else None
                }
                for s in steps
            ]
        }
    
    def print_workflow(self, steps: List[WorkflowStep]):
        """Print formatted workflow"""
        print("\n" + "="*80)
        print("MANUAL EXECUTION WORKFLOW")
        print("="*80)
        
        for step in steps:
            status = "✓" if step.completed else "○"
            print(f"\n{status} Step {step.step_number}: {step.title}")
            print(f"   {step.description}")
            print(f"   Action: {step.action_required}")
            if step.completed_at:
                print(f"   Completed: {step.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if step.notes:
                print(f"   Notes: {step.notes}")
        
        summary = self.get_workflow_summary(steps)
        print(f"\nProgress: {summary['completed_steps']}/{summary['total_steps']} steps ({summary['progress']:.0%})")
        print("="*80)

