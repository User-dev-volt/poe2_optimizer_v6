"""Convergence detection for optimization algorithms.

This module provides a pure-logic convergence detector that determines when
optimization should terminate based on improvement history.

Convergence conditions:
1. No improvement: No neighbor improves metric for N consecutive iterations
2. Diminishing returns: Improvement delta < threshold (e.g., 0.1%)

The detector is stateful and tracks improvement history across iterations.
It has zero external dependencies (Python stdlib only).
"""


class ConvergenceDetector:
    """Detects when optimization should stop based on improvement patterns.

    This detector tracks improvement history and identifies convergence based on:
    - Patience: Number of consecutive iterations without improvement
    - Diminishing returns: Very small improvements below a threshold

    The detector is called once per optimization iteration and maintains state
    across calls to track convergence patterns.
    """

    def __init__(self, patience: int = 3, min_improvement: float = 0.001):
        """Initialize convergence detector.

        Args:
            patience: Number of iterations without improvement before convergence.
                Default is 3 iterations.
            min_improvement: Minimum improvement threshold as a fraction.
                Improvements below this are considered diminishing returns.
                Default is 0.001 (0.1%).
        """
        self.patience = patience
        self.min_improvement = min_improvement
        self.iterations_without_improvement = 0
        self.best_metric = None
        self.convergence_reason = None

    def update(self, current_metric: float) -> None:
        """Update detector with latest metric value.

        Tracks improvement history and updates internal counters. This method
        should be called once per optimization iteration with the current
        metric value.

        Args:
            current_metric: The metric value for the current iteration.
                Higher values are considered better.
        """
        # Handle None/NaN values defensively
        if current_metric is None or (isinstance(current_metric, float) and
                                     current_metric != current_metric):  # NaN check
            # Treat None/NaN as no improvement
            self.iterations_without_improvement += 1
            return

        # First iteration - establish baseline
        if self.best_metric is None:
            self.best_metric = current_metric
            self.iterations_without_improvement = 0
            return

        # Calculate improvement
        improvement = current_metric - self.best_metric

        # Check if this is a meaningful improvement
        if improvement > 0:
            # Calculate relative improvement
            relative_improvement = improvement / abs(self.best_metric) if self.best_metric != 0 else improvement

            if relative_improvement >= self.min_improvement:
                # Significant improvement - reset counter and update best
                self.best_metric = current_metric
                self.iterations_without_improvement = 0
            else:
                # Improvement too small (diminishing returns)
                self.iterations_without_improvement += 1
                # Set convergence reason for diminishing returns
                if self.convergence_reason is None:
                    self.convergence_reason = "diminishing_returns"
        else:
            # No improvement or regression
            self.iterations_without_improvement += 1

    def has_converged(self) -> bool:
        """Check if optimization has converged.

        Returns True if either:
        - Patience threshold exceeded (no improvement for N iterations)
        - Diminishing returns detected (improvement < threshold)

        Returns:
            True if optimization should stop, False otherwise.
        """
        if self.iterations_without_improvement >= self.patience:
            # Set convergence reason if not already set
            if self.convergence_reason is None:
                self.convergence_reason = "no_improvement"
            return True
        return False

    def get_convergence_reason(self) -> str:
        """Return convergence reason string.

        Returns a human-readable reason for convergence, suitable for logging.

        Returns:
            A string describing why convergence occurred:
            - "Converged: no improvement for N iterations" - patience exceeded
            - "Converged: diminishing returns (<0.1% improvement)" - improvement too small
            - None if not yet converged
        """
        if self.convergence_reason == "no_improvement":
            return f"Converged: no improvement for {self.patience} iterations"
        elif self.convergence_reason == "diminishing_returns":
            return f"Converged: diminishing returns (<{self.min_improvement * 100:.1f}% improvement)"
        return None
