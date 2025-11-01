"""
Unit tests for ProgressTracker (Story 2.8).

Tests cover:
- AC-2.8.1: Track current iteration number
- AC-2.8.2: Track best metric value found so far
- AC-2.8.3: Track current improvement percentage versus baseline
- AC-2.8.4: Track budget usage (unallocated and respec points)
- AC-2.8.5: Provide progress callback mechanism for UI updates
- AC-2.8.6: Report progress every 100 iterations
"""

import time
import pytest
from unittest.mock import MagicMock

from src.optimizer.progress import ProgressTracker
from src.optimizer.budget_tracker import BudgetState


@pytest.fixture
def mock_budget():
    """Sample budget state for testing."""
    return BudgetState(
        unallocated_available=15,
        unallocated_used=8,
        respec_available=12,
        respec_used=2
    )


@pytest.fixture
def mock_budget_unlimited_respec():
    """Sample budget state with unlimited respec for testing."""
    return BudgetState(
        unallocated_available=10,
        unallocated_used=5,
        respec_available=None,  # unlimited
        respec_used=100
    )


@pytest.fixture
def progress_tracker_with_callback():
    """ProgressTracker with callback that captures invocations."""
    callback_data = []

    def capture_callback(**kwargs):
        callback_data.append(kwargs)

    tracker = ProgressTracker(callback=capture_callback)
    return tracker, callback_data


class TestProgressTrackerInitialization:
    """Test ProgressTracker initialization (AC-2.8.5)."""

    def test_init_with_callback(self):
        """Test initialization with callback function."""
        callback = MagicMock()
        tracker = ProgressTracker(callback=callback)

        assert tracker.callback is callback
        assert tracker.iteration_count == 0
        assert tracker.best_metric is None
        assert tracker.baseline_metric is None
        assert tracker.start_time is not None

    def test_init_without_callback(self):
        """Test initialization without callback (None callback handling)."""
        tracker = ProgressTracker()

        assert tracker.callback is None
        assert tracker.iteration_count == 0
        assert tracker.best_metric is None
        assert tracker.baseline_metric is None

    def test_set_baseline(self):
        """Test setting baseline metric."""
        tracker = ProgressTracker()
        tracker.set_baseline(1000.0)

        assert tracker.baseline_metric == 1000.0


class TestIterationTracking:
    """Test iteration counter tracking (AC-2.8.1)."""

    def test_iteration_counter_updates(self, mock_budget):
        """Test that iteration counter increments correctly."""
        tracker = ProgressTracker()
        tracker.set_baseline(100.0)

        tracker.update(1, 105.0, mock_budget)
        assert tracker.iteration_count == 1

        tracker.update(50, 110.0, mock_budget)
        assert tracker.iteration_count == 50

        tracker.update(100, 115.0, mock_budget)
        assert tracker.iteration_count == 100

    def test_iteration_counter_non_sequential(self, mock_budget):
        """Test iteration counter with non-sequential updates."""
        tracker = ProgressTracker()
        tracker.set_baseline(100.0)

        tracker.update(100, 110.0, mock_budget)
        assert tracker.iteration_count == 100

        tracker.update(200, 120.0, mock_budget)
        assert tracker.iteration_count == 200


class TestBestMetricTracking:
    """Test best metric tracking (AC-2.8.2)."""

    def test_best_metric_updates_on_improvement(self, mock_budget):
        """Test best metric updates when better value found."""
        tracker = ProgressTracker()
        tracker.set_baseline(100.0)

        tracker.update(1, 105.0, mock_budget)
        assert tracker.best_metric == 105.0

        tracker.update(2, 110.0, mock_budget)
        assert tracker.best_metric == 110.0

        tracker.update(3, 115.0, mock_budget)
        assert tracker.best_metric == 115.0

    def test_best_metric_does_not_update_on_worse_value(self, mock_budget):
        """Test best metric does not update on worse values."""
        tracker = ProgressTracker()
        tracker.set_baseline(100.0)

        tracker.update(1, 110.0, mock_budget)
        assert tracker.best_metric == 110.0

        tracker.update(2, 105.0, mock_budget)  # Worse
        assert tracker.best_metric == 110.0  # Should not change

        tracker.update(3, 100.0, mock_budget)  # Even worse
        assert tracker.best_metric == 110.0  # Should not change

    def test_best_metric_initial_value(self, mock_budget):
        """Test best metric is set on first update even if None."""
        tracker = ProgressTracker()
        tracker.set_baseline(100.0)

        assert tracker.best_metric is None

        tracker.update(1, 95.0, mock_budget)  # Worse than baseline
        assert tracker.best_metric == 95.0  # Should still be set


class TestImprovementPercentageCalculation:
    """Test improvement percentage calculation (AC-2.8.3)."""

    def test_positive_improvement_calculation(self, progress_tracker_with_callback, mock_budget):
        """Test positive improvement percentage calculation."""
        tracker, callback_data = progress_tracker_with_callback
        tracker.set_baseline(1000.0)

        tracker.update(100, 1150.0, mock_budget)  # +15% improvement

        assert len(callback_data) == 1
        assert callback_data[0]['improvement_pct'] == pytest.approx(15.0, rel=1e-2)

    def test_negative_improvement_calculation(self, progress_tracker_with_callback, mock_budget):
        """Test negative improvement (regression) calculation."""
        tracker, callback_data = progress_tracker_with_callback
        tracker.set_baseline(1000.0)

        tracker.update(100, 900.0, mock_budget)  # -10% improvement

        assert len(callback_data) == 1
        assert callback_data[0]['improvement_pct'] == pytest.approx(-10.0, rel=1e-2)

    def test_zero_improvement_calculation(self, progress_tracker_with_callback, mock_budget):
        """Test zero improvement calculation."""
        tracker, callback_data = progress_tracker_with_callback
        tracker.set_baseline(1000.0)

        tracker.update(100, 1000.0, mock_budget)  # No change

        assert len(callback_data) == 1
        assert callback_data[0]['improvement_pct'] == pytest.approx(0.0, rel=1e-2)

    def test_baseline_zero_protection(self, progress_tracker_with_callback, mock_budget):
        """Test division by zero protection when baseline is 0."""
        tracker, callback_data = progress_tracker_with_callback
        tracker.set_baseline(0.0)

        tracker.update(100, 100.0, mock_budget)

        # Should not crash, improvement should be 0
        assert len(callback_data) == 1
        assert callback_data[0]['improvement_pct'] == 0.0


class TestBudgetStateTracking:
    """Test budget state tracking accuracy (AC-2.8.4)."""

    def test_budget_data_structure(self, progress_tracker_with_callback, mock_budget):
        """Test budget data contains all required fields."""
        tracker, callback_data = progress_tracker_with_callback
        tracker.set_baseline(100.0)

        tracker.update(100, 110.0, mock_budget)

        assert len(callback_data) == 1
        budget_used = callback_data[0]['budget_used']

        assert 'unallocated_used' in budget_used
        assert 'unallocated_available' in budget_used
        assert 'respec_used' in budget_used
        assert 'respec_available' in budget_used

    def test_budget_values_accuracy(self, progress_tracker_with_callback, mock_budget):
        """Test budget values match BudgetState."""
        tracker, callback_data = progress_tracker_with_callback
        tracker.set_baseline(100.0)

        tracker.update(100, 110.0, mock_budget)

        budget_used = callback_data[0]['budget_used']
        assert budget_used['unallocated_used'] == 8
        assert budget_used['unallocated_available'] == 15
        assert budget_used['respec_used'] == 2
        assert budget_used['respec_available'] == 12

    def test_budget_unlimited_respec(self, progress_tracker_with_callback, mock_budget_unlimited_respec):
        """Test budget tracking with unlimited respec points."""
        tracker, callback_data = progress_tracker_with_callback
        tracker.set_baseline(100.0)

        tracker.update(100, 110.0, mock_budget_unlimited_respec)

        budget_used = callback_data[0]['budget_used']
        assert budget_used['respec_used'] == 100
        assert budget_used['respec_available'] is None  # Unlimited


class TestReportingFrequency:
    """Test reporting frequency control (AC-2.8.6)."""

    def test_should_report_iteration_1(self):
        """Test should_report returns True on iteration 1."""
        tracker = ProgressTracker()
        tracker.set_baseline(100.0)
        tracker.iteration_count = 1

        assert tracker.should_report() is True

    def test_should_report_multiples_of_100(self):
        """Test should_report returns True at iterations 100, 200, 300, etc."""
        tracker = ProgressTracker()
        tracker.set_baseline(100.0)

        for iteration in [100, 200, 300, 400, 500]:
            tracker.iteration_count = iteration
            assert tracker.should_report() is True, f"Failed at iteration {iteration}"

    def test_should_not_report_other_iterations(self):
        """Test should_report returns False for non-reporting iterations."""
        tracker = ProgressTracker()
        tracker.set_baseline(100.0)

        for iteration in [2, 50, 99, 101, 150, 199, 250]:
            tracker.iteration_count = iteration
            assert tracker.should_report() is False, f"Failed at iteration {iteration}"

    def test_callback_invocation_frequency(self, progress_tracker_with_callback, mock_budget):
        """Test callback is invoked every 100 iterations."""
        tracker, callback_data = progress_tracker_with_callback
        tracker.set_baseline(100.0)

        # Update through 300 iterations
        for i in range(1, 301):
            tracker.update(i, 100.0 + i, mock_budget)

        # Should have 4 callbacks: iterations 1, 100, 200, 300
        assert len(callback_data) == 4
        assert callback_data[0]['iteration'] == 1
        assert callback_data[1]['iteration'] == 100
        assert callback_data[2]['iteration'] == 200
        assert callback_data[3]['iteration'] == 300


class TestCallbackInvocation:
    """Test callback invocation and parameter passing (AC-2.8.5)."""

    def test_callback_parameters(self, progress_tracker_with_callback, mock_budget):
        """Test callback receives all required parameters."""
        tracker, callback_data = progress_tracker_with_callback
        tracker.set_baseline(100.0)

        tracker.update(100, 115.0, mock_budget)

        assert len(callback_data) == 1
        params = callback_data[0]

        assert 'iteration' in params
        assert 'best_metric' in params
        assert 'improvement_pct' in params
        assert 'budget_used' in params
        assert 'time_elapsed' in params

    def test_callback_parameter_values(self, progress_tracker_with_callback, mock_budget):
        """Test callback parameter values are correct."""
        tracker, callback_data = progress_tracker_with_callback
        tracker.set_baseline(1000.0)

        tracker.update(200, 1100.0, mock_budget)

        params = callback_data[0]
        assert params['iteration'] == 200
        assert params['best_metric'] == 1100.0
        assert params['improvement_pct'] == pytest.approx(10.0, rel=1e-2)
        assert params['time_elapsed'] >= 0  # May be 0 on fast machines

    def test_none_callback_no_crash(self, mock_budget):
        """Test None callback does not cause crash."""
        tracker = ProgressTracker(callback=None)
        tracker.set_baseline(100.0)

        # Should not crash
        tracker.update(1, 110.0, mock_budget)
        tracker.update(100, 120.0, mock_budget)
        tracker.update(200, 130.0, mock_budget)

    def test_time_elapsed_increases(self, progress_tracker_with_callback, mock_budget):
        """Test time_elapsed increases across progress updates."""
        tracker, callback_data = progress_tracker_with_callback
        tracker.set_baseline(100.0)

        tracker.update(1, 105.0, mock_budget)
        time.sleep(0.01)  # Small delay
        tracker.update(100, 110.0, mock_budget)

        assert len(callback_data) == 2
        assert callback_data[1]['time_elapsed'] > callback_data[0]['time_elapsed']


class TestEdgeCases:
    """Test edge cases and defensive programming."""

    def test_multiple_updates_between_reports(self, progress_tracker_with_callback, mock_budget):
        """Test multiple updates between reporting intervals."""
        tracker, callback_data = progress_tracker_with_callback
        tracker.set_baseline(100.0)

        # Update 50 times (should only report at iteration 1)
        for i in range(1, 51):
            tracker.update(i, 100.0 + i, mock_budget)

        assert len(callback_data) == 1  # Only iteration 1
        assert callback_data[0]['iteration'] == 1

    def test_best_metric_preserved_across_iterations(self, mock_budget):
        """Test best metric is preserved even when worse values come later."""
        tracker = ProgressTracker()
        tracker.set_baseline(100.0)

        tracker.update(1, 150.0, mock_budget)
        assert tracker.best_metric == 150.0

        for i in range(2, 101):
            tracker.update(i, 120.0, mock_budget)  # All worse than 150

        assert tracker.best_metric == 150.0  # Should still be 150
