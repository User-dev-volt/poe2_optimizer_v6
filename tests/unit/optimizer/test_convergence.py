"""Unit tests for convergence detection module.

Tests cover:
- Patience counter logic (no improvement for N iterations)
- Diminishing returns detection (improvement < threshold)
- State management and edge cases
- Convergence reason reporting
"""

import pytest
import math
from src.optimizer.convergence import ConvergenceDetector


class TestConvergenceDetectorInitialization:
    """Test ConvergenceDetector initialization and defaults."""

    def test_default_initialization(self):
        """Test detector initializes with default values."""
        detector = ConvergenceDetector()
        assert detector.patience == 3
        assert detector.min_improvement == 0.001
        assert detector.iterations_without_improvement == 0
        assert detector.best_metric is None
        assert detector.convergence_reason is None

    def test_custom_initialization(self):
        """Test detector initializes with custom values."""
        detector = ConvergenceDetector(patience=5, min_improvement=0.01)
        assert detector.patience == 5
        assert detector.min_improvement == 0.01


class TestPatienceCounterLogic:
    """Test patience counter behavior (AC-2.7.1)."""

    def test_no_improvement_triggers_convergence(self):
        """Test that 3 consecutive iterations without improvement triggers convergence."""
        detector = ConvergenceDetector(patience=3)

        # Iteration 1: establish baseline
        detector.update(100.0)
        assert not detector.has_converged()
        assert detector.iterations_without_improvement == 0

        # Iterations 2-4: no improvement
        detector.update(100.0)
        assert detector.iterations_without_improvement == 1
        assert not detector.has_converged()

        detector.update(100.0)
        assert detector.iterations_without_improvement == 2
        assert not detector.has_converged()

        detector.update(100.0)
        assert detector.iterations_without_improvement == 3
        assert detector.has_converged()
        assert detector.convergence_reason == "no_improvement"

    def test_improvement_resets_counter(self):
        """Test that patience counter resets when improvement is found."""
        detector = ConvergenceDetector(patience=3, min_improvement=0.001)

        # Establish baseline
        detector.update(100.0)
        assert detector.iterations_without_improvement == 0

        # Two iterations without improvement
        detector.update(100.0)
        detector.update(100.0)
        assert detector.iterations_without_improvement == 2

        # Significant improvement (>0.1%) - should reset counter
        detector.update(100.2)  # 0.2% improvement
        assert detector.iterations_without_improvement == 0
        assert detector.best_metric == 100.2
        assert not detector.has_converged()

    def test_first_iteration_no_convergence(self):
        """Test that first iteration establishes baseline without convergence."""
        detector = ConvergenceDetector(patience=3)

        detector.update(50.0)
        assert detector.best_metric == 50.0
        assert detector.iterations_without_improvement == 0
        assert not detector.has_converged()
        assert detector.convergence_reason is None


class TestDiminishingReturns:
    """Test diminishing returns detection (AC-2.7.2)."""

    def test_small_improvement_triggers_convergence(self):
        """Test that improvement < 0.1% triggers convergence."""
        detector = ConvergenceDetector(patience=3, min_improvement=0.001)

        # Establish baseline at 1000.0
        detector.update(1000.0)

        # Small improvements below threshold (< 0.1% = < 1.0)
        detector.update(1000.5)  # 0.05% improvement - below threshold
        assert detector.iterations_without_improvement == 1

        detector.update(1000.8)  # Still below threshold cumulatively
        assert detector.iterations_without_improvement == 2

        detector.update(1000.9)  # Still below threshold
        assert detector.iterations_without_improvement == 3
        assert detector.has_converged()
        assert detector.convergence_reason == "diminishing_returns"

    def test_boundary_exactly_threshold(self):
        """Test that exactly 0.1% improvement does NOT trigger diminishing returns."""
        detector = ConvergenceDetector(patience=3, min_improvement=0.001)

        # Establish baseline at 1000.0
        detector.update(1000.0)

        # Exactly 0.1% improvement (1.0 increase on 1000.0)
        detector.update(1001.0)
        assert detector.iterations_without_improvement == 0
        assert detector.best_metric == 1001.0
        assert not detector.has_converged()

    def test_above_threshold_continues(self):
        """Test that improvement > 0.1% continues optimization."""
        detector = ConvergenceDetector(patience=3, min_improvement=0.001)

        # Establish baseline
        detector.update(100.0)

        # Significant improvements (> 0.1%)
        detector.update(100.2)  # 0.2% improvement
        assert detector.iterations_without_improvement == 0
        assert not detector.has_converged()

        detector.update(101.0)  # Large improvement
        assert detector.iterations_without_improvement == 0
        assert not detector.has_converged()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_negative_improvement_regression(self):
        """Test that regression (negative improvement) increments counter."""
        detector = ConvergenceDetector(patience=3)

        # Establish baseline
        detector.update(100.0)

        # Regression - worse metric
        detector.update(95.0)
        assert detector.iterations_without_improvement == 1
        assert detector.best_metric == 100.0  # Best should not change

    def test_equal_metric_values(self):
        """Test that equal metric values count as no improvement."""
        detector = ConvergenceDetector(patience=3)

        detector.update(100.0)
        detector.update(100.0)
        detector.update(100.0)

        assert detector.iterations_without_improvement == 2
        assert detector.best_metric == 100.0

    def test_very_large_metric_values(self):
        """Test handling of very large metric values (overflow protection)."""
        detector = ConvergenceDetector(patience=3, min_improvement=0.001)

        # Very large values
        large_value = 1e15
        detector.update(large_value)
        detector.update(large_value * 1.002)  # 0.2% improvement

        assert detector.best_metric == large_value * 1.002
        assert detector.iterations_without_improvement == 0
        assert not detector.has_converged()

    def test_none_metric_values(self):
        """Test defensive handling of None metric values."""
        detector = ConvergenceDetector(patience=3)

        detector.update(100.0)
        detector.update(None)

        assert detector.iterations_without_improvement == 1
        assert detector.best_metric == 100.0

    def test_nan_metric_values(self):
        """Test defensive handling of NaN metric values."""
        detector = ConvergenceDetector(patience=3)

        detector.update(100.0)
        detector.update(float('nan'))

        assert detector.iterations_without_improvement == 1
        assert detector.best_metric == 100.0

    def test_zero_best_metric(self):
        """Test handling when best_metric is zero (division edge case)."""
        detector = ConvergenceDetector(patience=3, min_improvement=0.001)

        detector.update(0.0)
        detector.update(1.0)  # Improvement from 0

        # Should handle division by zero gracefully
        assert detector.best_metric == 1.0
        assert detector.iterations_without_improvement == 0


class TestConvergenceReasonReporting:
    """Test convergence reason string formatting (AC-2.7.4)."""

    def test_no_improvement_reason_string(self):
        """Test convergence reason for patience exceeded."""
        detector = ConvergenceDetector(patience=3)

        detector.update(100.0)
        detector.update(100.0)
        detector.update(100.0)
        detector.update(100.0)

        assert detector.has_converged()
        reason = detector.get_convergence_reason()
        assert reason == "Converged: no improvement for 3 iterations"

    def test_diminishing_returns_reason_string(self):
        """Test convergence reason for diminishing returns."""
        detector = ConvergenceDetector(patience=3, min_improvement=0.001)

        detector.update(1000.0)
        detector.update(1000.5)  # 0.05% - below threshold
        detector.update(1000.5)
        detector.update(1000.5)

        assert detector.has_converged()
        reason = detector.get_convergence_reason()
        assert reason == "Converged: diminishing returns (<0.1% improvement)"

    def test_no_reason_before_convergence(self):
        """Test that reason is None before convergence."""
        detector = ConvergenceDetector(patience=3)

        detector.update(100.0)
        detector.update(105.0)

        assert not detector.has_converged()
        assert detector.get_convergence_reason() is None

    def test_custom_patience_in_reason(self):
        """Test that custom patience value appears in reason string."""
        detector = ConvergenceDetector(patience=5)

        # Trigger no improvement convergence
        detector.update(100.0)
        for _ in range(5):
            detector.update(100.0)

        assert detector.has_converged()
        reason = detector.get_convergence_reason()
        assert "5 iterations" in reason

    def test_custom_min_improvement_in_reason(self):
        """Test that custom min_improvement appears in reason string."""
        detector = ConvergenceDetector(patience=3, min_improvement=0.01)  # 1%

        detector.update(100.0)
        detector.update(100.5)  # 0.5% - below 1% threshold
        detector.update(100.5)
        detector.update(100.5)

        assert detector.has_converged()
        reason = detector.get_convergence_reason()
        assert "1.0%" in reason


class TestStateManagement:
    """Test internal state tracking across updates."""

    def test_best_metric_tracking(self):
        """Test that best_metric is properly tracked across updates."""
        detector = ConvergenceDetector(patience=3, min_improvement=0.001)

        detector.update(100.0)
        assert detector.best_metric == 100.0

        detector.update(105.0)
        assert detector.best_metric == 105.0

        detector.update(103.0)  # Regression
        assert detector.best_metric == 105.0  # Should not change

        detector.update(110.0)  # New best
        assert detector.best_metric == 110.0

    def test_convergence_reason_set_correctly(self):
        """Test that convergence_reason is set when has_converged returns True."""
        detector = ConvergenceDetector(patience=3)

        detector.update(100.0)
        for _ in range(3):
            detector.update(100.0)

        # Check convergence sets reason
        converged = detector.has_converged()
        assert converged is True
        assert detector.convergence_reason is not None

    def test_multiple_convergence_checks(self):
        """Test that multiple calls to has_converged() are idempotent."""
        detector = ConvergenceDetector(patience=3)

        detector.update(100.0)
        detector.update(100.0)
        detector.update(100.0)
        detector.update(100.0)

        # Multiple calls should return same result
        assert detector.has_converged() is True
        assert detector.has_converged() is True
        assert detector.has_converged() is True


class TestConvergenceConditionPriority:
    """Test which convergence condition is reported when multiple apply."""

    def test_diminishing_returns_detected_first(self):
        """Test that diminishing returns is detected and reported correctly."""
        detector = ConvergenceDetector(patience=3, min_improvement=0.001)

        # Start with baseline
        detector.update(1000.0)

        # Small improvement below threshold - triggers diminishing returns
        detector.update(1000.5)  # 0.05% improvement
        assert detector.convergence_reason == "diminishing_returns"

        # Continue with no improvement
        detector.update(1000.5)
        detector.update(1000.5)

        # Should have converged, and reason should still be diminishing returns
        assert detector.has_converged()
        assert detector.convergence_reason == "diminishing_returns"
