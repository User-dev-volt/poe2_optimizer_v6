"""
Progress tracking module for optimization process.

This module provides the ProgressTracker class for tracking and reporting
optimization progress including iteration count, best metric value, improvement
percentage, and budget usage.
"""

import logging
import time
from typing import Callable, Optional

from src.optimizer.budget_tracker import BudgetState

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Tracks and reports optimization progress."""

    def __init__(self, callback: Optional[Callable] = None):
        """
        Initialize progress tracker.

        Args:
            callback: Optional callback function invoked every 100 iterations
                     with progress data (iteration, best_metric, improvement_pct,
                     budget_used, time_elapsed)
        """
        self.callback = callback
        self.start_time = time.time()
        self.iteration_count = 0
        self.best_metric = None
        self.baseline_metric = None

    def set_baseline(self, baseline_metric: float) -> None:
        """
        Set baseline metric for improvement calculation.

        Args:
            baseline_metric: Initial metric value before optimization starts
        """
        self.baseline_metric = baseline_metric

    def update(
        self,
        iteration: int,
        best_metric: float,
        budget: BudgetState
    ) -> None:
        """
        Update progress state and invoke callback if needed.

        Args:
            iteration: Current iteration number
            best_metric: Best metric value found so far
            budget: Current budget state (unallocated and respec points)
        """
        self.iteration_count = iteration
        if self.best_metric is None or best_metric > self.best_metric:
            self.best_metric = best_metric

        if self.should_report():
            self._invoke_callback(budget)

    def should_report(self) -> bool:
        """
        Check if we should report progress (every 100 iterations).

        Returns:
            True if current iteration is 1 or divisible by 100, False otherwise
        """
        return (self.iteration_count == 1 or
                self.iteration_count % 100 == 0)

    def _invoke_callback(self, budget: BudgetState) -> None:
        """
        Invoke callback with current progress data.

        Args:
            budget: Current budget state for reporting
        """
        improvement_pct = 0.0
        if self.baseline_metric and self.baseline_metric > 0:
            improvement_pct = ((self.best_metric - self.baseline_metric) /
                             self.baseline_metric * 100)

        budget_used = {
            'unallocated_used': budget.unallocated_used,
            'unallocated_available': budget.unallocated_available,
            'respec_used': budget.respec_used,
            'respec_available': budget.respec_available
        }

        time_elapsed = time.time() - self.start_time

        # Console logging for development visibility (Story 2.8 Task 7)
        respec_str = (
            f"{budget.respec_used}/{budget.respec_available} R"
            if budget.respec_available is not None
            else f"{budget.respec_used}/∞ R"
        )
        logger.info(
            "Iteration %d: %+.1f%% improvement, Budget: %d/%d U, %s, Elapsed: %.0fs",
            self.iteration_count,
            improvement_pct,
            budget.unallocated_used,
            budget.unallocated_available,
            respec_str,
            time_elapsed
        )

        # Invoke user-provided callback if present
        if self.callback is not None:
            self.callback(
                iteration=self.iteration_count,
                best_metric=self.best_metric,
                improvement_pct=improvement_pct,
                budget_used=budget_used,
                time_elapsed=time_elapsed
            )
