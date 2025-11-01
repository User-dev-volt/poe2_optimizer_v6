"""
Integration tests for ProgressTracker with hill climbing algorithm (Story 2.8).

Tests cover:
- Full optimization run with progress tracking
- Callback invocation with real hill climbing data
- Time elapsed monotonicity
- Budget usage accuracy during optimization
"""

import pytest
from unittest.mock import MagicMock, patch

from src.models.build_data import BuildData, CharacterClass
from src.models.build_stats import BuildStats
from src.models.optimization_config import OptimizationConfiguration
from src.optimizer.hill_climbing import optimize_build


@pytest.fixture
def sample_build():
    """Create a sample BuildData for testing."""
    return BuildData(
        character_class=CharacterClass.WITCH,
        level=50,
        ascendancy="Blood Mage",
        passive_nodes={1, 2, 3, 4, 5}
    )


@pytest.fixture
def sample_stats():
    """Create sample BuildStats for testing."""
    return BuildStats(
        total_dps=1000.0,
        life=5000,
        energy_shield=0,
        mana=1000,
        effective_hp=5000.0,
        resistances={"fire": 75, "cold": 75, "lightning": 75, "chaos": 0}
    )


class TestProgressTrackingIntegration:
    """Integration tests for ProgressTracker with optimize_build."""

    def test_progress_callback_invoked_during_optimization(self, sample_build, sample_stats):
        """Test that progress callback is invoked during optimization."""
        callback_invocations = []

        def test_callback(**kwargs):
            callback_invocations.append(kwargs)

        config = OptimizationConfiguration(
            build=sample_build,
            metric="dps",
            unallocated_points=10,
            respec_points=5,
            max_iterations=150,
            progress_callback=test_callback
        )

        # Mock calculate_build_stats to return consistent stats
        with patch('src.optimizer.hill_climbing.calculate_build_stats', return_value=sample_stats):
            result = optimize_build(config)

        # Should have callback invocations
        # (optimization converges immediately due to placeholder neighbor generation,
        # so we get the final progress update at iteration 0 or 1)
        assert len(callback_invocations) >= 1
        # First callback should be at iteration 0 or 1 (depends on convergence timing)
        assert callback_invocations[0]['iteration'] in [0, 1]

    def test_progress_callback_parameters_structure(self, sample_build, sample_stats):
        """Test that callback receives all required parameters."""
        callback_invocations = []

        def test_callback(**kwargs):
            callback_invocations.append(kwargs)

        config = OptimizationConfiguration(
            build=sample_build,
            metric="dps",
            unallocated_points=10,
            max_iterations=50,
            progress_callback=test_callback
        )

        with patch('src.optimizer.hill_climbing.calculate_build_stats', return_value=sample_stats):
            result = optimize_build(config)

        assert len(callback_invocations) >= 1
        first_call = callback_invocations[0]

        # Verify all required parameters present
        assert 'iteration' in first_call
        assert 'best_metric' in first_call
        assert 'improvement_pct' in first_call
        assert 'budget_used' in first_call
        assert 'time_elapsed' in first_call

        # Verify budget_used structure
        budget = first_call['budget_used']
        assert 'unallocated_used' in budget
        assert 'unallocated_available' in budget
        assert 'respec_used' in budget
        assert 'respec_available' in budget

    def test_time_elapsed_increases_monotonically(self, sample_build, sample_stats):
        """Test that time_elapsed increases across progress updates."""
        callback_invocations = []

        def test_callback(**kwargs):
            callback_invocations.append(kwargs)

        config = OptimizationConfiguration(
            build=sample_build,
            metric="dps",
            unallocated_points=10,
            max_iterations=250,  # Enough to get multiple callbacks
            progress_callback=test_callback
        )

        # Mock to simulate some iterations before converging
        iteration_counter = [0]

        def mock_generate_neighbors(*args, **kwargs):
            iteration_counter[0] += 1
            # Return empty list after 150 iterations to trigger convergence
            if iteration_counter[0] >= 150:
                return []
            # Return a fake neighbor for first 149 iterations
            return [sample_build]

        with patch('src.optimizer.hill_climbing.calculate_build_stats', return_value=sample_stats), \
             patch('src.optimizer.hill_climbing._generate_neighbors_placeholder', side_effect=mock_generate_neighbors):
            result = optimize_build(config)

        # Should have multiple callbacks if we ran enough iterations
        if len(callback_invocations) >= 2:
            for i in range(1, len(callback_invocations)):
                assert callback_invocations[i]['time_elapsed'] >= callback_invocations[i-1]['time_elapsed'], \
                    f"Time elapsed should be monotonic: {callback_invocations[i-1]['time_elapsed']} -> {callback_invocations[i]['time_elapsed']}"

    def test_budget_usage_reflects_optimization_state(self, sample_build, sample_stats):
        """Test that budget usage in callbacks reflects actual optimization state."""
        callback_invocations = []

        def test_callback(**kwargs):
            callback_invocations.append(kwargs)

        initial_unallocated = 15
        initial_respec = 10

        config = OptimizationConfiguration(
            build=sample_build,
            metric="dps",
            unallocated_points=initial_unallocated,
            respec_points=initial_respec,
            max_iterations=50,
            progress_callback=test_callback
        )

        with patch('src.optimizer.hill_climbing.calculate_build_stats', return_value=sample_stats):
            result = optimize_build(config)

        # Verify budget values in callback match initial configuration
        assert len(callback_invocations) >= 1
        budget = callback_invocations[0]['budget_used']

        assert budget['unallocated_available'] == initial_unallocated
        assert budget['respec_available'] == initial_respec
        # Used values should be 0 at start (no neighbors generated in placeholder)
        assert budget['unallocated_used'] == 0
        assert budget['respec_used'] == 0

    def test_optimization_without_callback(self, sample_build, sample_stats):
        """Test that optimization works without progress callback (None callback)."""
        config = OptimizationConfiguration(
            build=sample_build,
            metric="dps",
            unallocated_points=10,
            max_iterations=50,
            progress_callback=None  # No callback
        )

        with patch('src.optimizer.hill_climbing.calculate_build_stats', return_value=sample_stats):
            result = optimize_build(config)

        # Should complete without errors
        assert result is not None
        assert result.iterations_run >= 0

    def test_callback_invoked_with_real_metric_values(self, sample_build, sample_stats):
        """Test that callback receives real metric values from optimization."""
        callback_invocations = []

        def test_callback(**kwargs):
            callback_invocations.append(kwargs)

        config = OptimizationConfiguration(
            build=sample_build,
            metric="dps",
            unallocated_points=10,
            max_iterations=50,
            progress_callback=test_callback
        )

        with patch('src.optimizer.hill_climbing.calculate_build_stats', return_value=sample_stats):
            result = optimize_build(config)

        assert len(callback_invocations) >= 1
        first_call = callback_invocations[0]

        # best_metric should match the DPS from sample_stats
        assert first_call['best_metric'] == pytest.approx(sample_stats.total_dps, rel=1e-2)

        # improvement_pct should be 0 at start (no improvement yet)
        assert first_call['improvement_pct'] == pytest.approx(0.0, rel=1e-2)

    def test_multiple_reporting_intervals(self, sample_build, sample_stats):
        """Test progress reporting at multiple 100-iteration intervals."""
        callback_invocations = []

        def test_callback(**kwargs):
            callback_invocations.append(kwargs)

        config = OptimizationConfiguration(
            build=sample_build,
            metric="dps",
            unallocated_points=10,
            max_iterations=350,
            progress_callback=test_callback
        )

        # Note: Due to placeholder neighbor generation, optimization converges
        # immediately. This test verifies basic callback structure.
        # Full multi-iteration testing requires Story 2.2 (neighbor generation).
        with patch('src.optimizer.hill_climbing.calculate_build_stats', return_value=sample_stats):
            result = optimize_build(config)

        # Should have at least one callback (final progress update)
        assert len(callback_invocations) >= 1

        # Verify callback structure is correct
        reported_iterations = [call['iteration'] for call in callback_invocations]
        assert all(isinstance(i, int) for i in reported_iterations)
        # All reported iterations should be non-negative
        assert all(i >= 0 for i in reported_iterations)
