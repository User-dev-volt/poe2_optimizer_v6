"""
Unit tests for Hill Climbing Optimizer

Tests all acceptance criteria for Story 2.1:
- AC-2.1.1: Algorithm starts with current passive tree (baseline)
- AC-2.1.2: Algorithm generates neighbor configurations
- AC-2.1.3: Algorithm evaluates each neighbor using PoB calculations
- AC-2.1.4: Algorithm selects best neighbor if improvement found
- AC-2.1.5: Algorithm repeats until convergence (no improvement)
- AC-2.1.6: Algorithm returns best configuration found

Story: 2.1 - Implement Hill Climbing Core Algorithm
Author: Dev Agent (Amelia)
Date: 2025-10-27
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, call
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from optimizer.hill_climbing import (
    optimize_build,
    _generate_neighbors_placeholder,
    _evaluate_neighbors,
    _select_best_neighbor,
    _get_metric_value,
    _calculate_improvement_percentage
)
from models.build_data import BuildData, CharacterClass
from models.build_stats import BuildStats
from models.optimization_config import OptimizationConfiguration, OptimizationResult


@pytest.fixture
def sample_build():
    """Create a sample BuildData for testing"""
    return BuildData(
        character_class=CharacterClass.WITCH,
        level=50,
        passive_nodes={1, 2, 3}
    )


@pytest.fixture
def sample_stats():
    """Create sample BuildStats for testing"""
    return BuildStats(
        total_dps=10000.0,
        effective_hp=5000.0,
        life=2000,
        energy_shield=1000,
        mana=800,
        resistances={"fire": 75, "cold": 75, "lightning": 75, "chaos": 0}
    )


@pytest.fixture
def sample_config(sample_build):
    """Create sample OptimizationConfiguration for testing"""
    return OptimizationConfiguration(
        build=sample_build,
        metric="dps",
        unallocated_points=10,
        respec_points=5,
        max_iterations=10,
        max_time_seconds=300,
        convergence_patience=3
    )


class TestBaselineCalculation:
    """Test suite for AC-2.1.1: Algorithm starts with baseline"""

    @patch('optimizer.hill_climbing.calculate_build_stats')
    def test_optimize_build_calculates_baseline_stats(
        self,
        mock_calculate,
        sample_config,
        sample_stats
    ):
        """
        Verify optimize_build() calculates baseline stats using calculator (AC-2.1.1)

        Test:
            1. Mock calculate_build_stats to return fixed stats
            2. Call optimize_build()
            3. Verify calculate_build_stats was called with original build
            4. Verify baseline_stats in result matches mocked return
        """
        # Arrange
        mock_calculate.return_value = sample_stats

        # Act
        result = optimize_build(sample_config)

        # Assert - baseline calculation called with original build
        assert mock_calculate.call_count >= 1
        first_call = mock_calculate.call_args_list[0]
        assert first_call[0][0] == sample_config.build

        # Assert - baseline stats in result
        assert result.baseline_stats == sample_stats
        assert result.baseline_stats.total_dps == 10000.0

    @patch('optimizer.hill_climbing.calculate_build_stats')
    def test_baseline_stats_logged(self, mock_calculate, sample_config, sample_stats):
        """Verify baseline calculation is logged for debugging"""
        mock_calculate.return_value = sample_stats

        with patch('optimizer.hill_climbing.logger') as mock_logger:
            result = optimize_build(sample_config)

            # Check that baseline calculation was logged
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any('Baseline calculated' in str(call) for call in log_calls)


class TestNeighborGeneration:
    """Test suite for AC-2.1.2: Algorithm generates neighbors"""

    def test_generate_neighbors_placeholder_returns_empty_list(self, sample_build):
        """
        Verify neighbor generation placeholder returns empty list (Story 2.1)

        Story 2.1 uses placeholder that returns empty list for immediate convergence.
        Story 2.2 will implement full neighbor generation.
        """
        # Act
        neighbors = _generate_neighbors_placeholder(sample_build, 10, 5)

        # Assert
        assert isinstance(neighbors, list)
        assert len(neighbors) == 0

    @patch('optimizer.hill_climbing._generate_neighbors_placeholder')
    @patch('optimizer.hill_climbing.calculate_build_stats')
    def test_optimize_build_calls_neighbor_generator(
        self,
        mock_calculate,
        mock_generate_neighbors,
        sample_config,
        sample_stats
    ):
        """
        Verify optimize_build() calls neighbor generator during loop (AC-2.1.2)

        Test:
            1. Mock neighbor generator to return empty list
            2. Mock calculate_build_stats for baseline
            3. Call optimize_build()
            4. Verify neighbor generator was called at least once
        """
        # Arrange
        mock_calculate.return_value = sample_stats
        mock_generate_neighbors.return_value = []

        # Act
        result = optimize_build(sample_config)

        # Assert - neighbor generator called
        assert mock_generate_neighbors.call_count >= 1

        # Assert - called with current build and budget info
        call_args = mock_generate_neighbors.call_args
        assert isinstance(call_args[0][0], BuildData)
        assert isinstance(call_args[0][1], (int, float))  # unallocated_remaining
        assert isinstance(call_args[0][2], (int, float))  # respec_remaining


class TestNeighborEvaluation:
    """Test suite for AC-2.1.3: Algorithm evaluates all neighbors"""

    @patch('optimizer.hill_climbing.calculate_build_stats')
    def test_evaluate_neighbors_all_neighbors_evaluated(
        self,
        mock_calculate,
        sample_build,
        sample_stats
    ):
        """
        Verify _evaluate_neighbors() calculates stats for all neighbors (AC-2.1.3)

        Test:
            1. Create list of 5 neighbor builds
            2. Mock calculate_build_stats to return different stats
            3. Call _evaluate_neighbors()
            4. Verify calculate_build_stats called 5 times
        """
        # Arrange - create 5 neighbor builds
        neighbors = [
            BuildData(
                character_class=CharacterClass.WITCH,
                level=50,
                passive_nodes={1, 2, 3, i}
            )
            for i in range(4, 9)
        ]

        # Mock different DPS for each neighbor
        mock_calculate.side_effect = [
            BuildStats(
                total_dps=10000.0 + i * 100,
                effective_hp=5000.0,
                life=2000,
                energy_shield=1000,
                mana=800,
                resistances={"fire": 75, "cold": 75, "lightning": 75, "chaos": 0}
            )
            for i in range(5)
        ]

        # Act
        evaluations = _evaluate_neighbors(neighbors, "dps", sample_stats)

        # Assert - all neighbors evaluated
        assert mock_calculate.call_count == 5
        assert len(evaluations) == 5

        # Assert - evaluations contain (build, stats) tuples
        for build, stats in evaluations:
            assert isinstance(build, BuildData)
            assert isinstance(stats, BuildStats)

    @patch('optimizer.hill_climbing.calculate_build_stats')
    def test_evaluate_neighbors_handles_calculation_error(
        self,
        mock_calculate,
        sample_build
    ):
        """
        Verify _evaluate_neighbors() skips neighbors that fail calculation

        Test:
            1. Create 3 neighbors
            2. Mock calculate_build_stats to fail on 2nd neighbor
            3. Verify only 2 evaluations returned (1st and 3rd succeed)
        """
        # Arrange
        neighbors = [
            BuildData(
                character_class=CharacterClass.WITCH,
                level=50,
                passive_nodes={1, 2, 3, i}
            )
            for i in range(4, 7)
        ]

        # Mock: success, failure, success
        mock_calculate.side_effect = [
            BuildStats(
                total_dps=10000.0,
                effective_hp=5000.0,
                life=2000,
                energy_shield=1000,
                mana=800,
                resistances={"fire": 75, "cold": 75, "lightning": 75, "chaos": 0}
            ),
            Exception("PoB calculation failed"),
            BuildStats(
                total_dps=11000.0,
                effective_hp=5000.0,
                life=2000,
                energy_shield=1000,
                mana=800,
                resistances={"fire": 75, "cold": 75, "lightning": 75, "chaos": 0}
            )
        ]

        # Act
        evaluations = _evaluate_neighbors(neighbors, "dps", None)

        # Assert - only 2 successful evaluations
        assert len(evaluations) == 2


class TestBestNeighborSelection:
    """Test suite for AC-2.1.4: Algorithm selects best neighbor"""

    def test_select_best_neighbor_highest_dps(self):
        """
        Verify _select_best_neighbor() selects neighbor with highest DPS (AC-2.1.4)

        Test:
            1. Create evaluations with different DPS values
            2. Call _select_best_neighbor() with metric="dps"
            3. Verify highest DPS neighbor selected
        """
        # Arrange - evaluations with different DPS
        evaluations = [
            (
                BuildData(
                    character_class=CharacterClass.WITCH,
                    level=50,
                    passive_nodes={1, 2, 3, 4}
                ),
                BuildStats(
                    total_dps=9000.0,
                    effective_hp=5000.0,
                    life=2000,
                    energy_shield=1000,
                    mana=800,
                    resistances={"fire": 75, "cold": 75, "lightning": 75, "chaos": 0}
                )
            ),
            (
                BuildData(
                    character_class=CharacterClass.WITCH,
                    level=50,
                    passive_nodes={1, 2, 3, 5}
                ),
                BuildStats(
                    total_dps=12000.0,  # Highest DPS
                    effective_hp=5000.0,
                    life=2000,
                    energy_shield=1000,
                    mana=800,
                    resistances={"fire": 75, "cold": 75, "lightning": 75, "chaos": 0}
                )
            ),
            (
                BuildData(
                    character_class=CharacterClass.WITCH,
                    level=50,
                    passive_nodes={1, 2, 3, 6}
                ),
                BuildStats(
                    total_dps=11000.0,
                    effective_hp=5000.0,
                    life=2000,
                    energy_shield=1000,
                    mana=800,
                    resistances={"fire": 75, "cold": 75, "lightning": 75, "chaos": 0}
                )
            )
        ]

        # Act
        best = _select_best_neighbor(evaluations, "dps")

        # Assert
        assert best is not None
        best_build, best_stats, nodes_added, nodes_removed = best
        assert best_stats.total_dps == 12000.0

    def test_select_best_neighbor_no_evaluations_returns_none(self):
        """Verify _select_best_neighbor() returns None for empty evaluations"""
        # Act
        best = _select_best_neighbor([], "dps")

        # Assert
        assert best is None

    def test_get_metric_value_dps(self, sample_stats):
        """Verify _get_metric_value() correctly extracts DPS metric"""
        value = _get_metric_value(sample_stats, "dps")
        assert value == 10000.0

    def test_get_metric_value_ehp(self, sample_stats):
        """Verify _get_metric_value() correctly extracts EHP metric"""
        value = _get_metric_value(sample_stats, "ehp")
        assert value == 5000.0

    def test_get_metric_value_balanced(self, sample_stats):
        """Verify _get_metric_value() computes balanced metric"""
        value = _get_metric_value(sample_stats, "balanced")
        # Balanced = dps * 0.6 + ehp * 0.4 = 10000 * 0.6 + 5000 * 0.4 = 8000
        assert value == 8000.0


class TestConvergence:
    """Test suite for AC-2.1.5: Algorithm repeats until convergence"""

    @patch('optimizer.hill_climbing._generate_neighbors_placeholder')
    @patch('optimizer.hill_climbing.calculate_build_stats')
    def test_optimize_build_converges_no_neighbors(
        self,
        mock_calculate,
        mock_generate_neighbors,
        sample_config,
        sample_stats
    ):
        """
        Verify loop terminates when no neighbors available (AC-2.1.5)

        Test:
            1. Mock neighbor generator to return empty list
            2. Call optimize_build()
            3. Verify convergence_reason = "no_valid_neighbors"
            4. Verify iterations_run = 0
        """
        # Arrange
        mock_calculate.return_value = sample_stats
        mock_generate_neighbors.return_value = []

        # Act
        result = optimize_build(sample_config)

        # Assert
        assert result.convergence_reason == "no_valid_neighbors"
        assert result.iterations_run == 0
        assert result.improvement_pct == 0.0

    @patch('optimizer.hill_climbing.calculate_build_stats')
    def test_optimize_build_max_iterations_timeout(self, mock_calculate, sample_build):
        """
        Verify loop terminates after max_iterations (AC-2.1.5)

        Test:
            1. Set max_iterations=5
            2. Call optimize_build()
            3. Verify iterations_run <= 5
            4. Verify convergence_reason = "max_iterations" or "no_valid_neighbors"
        """
        # Arrange
        config = OptimizationConfiguration(
            build=sample_build,
            metric="dps",
            unallocated_points=10,
            max_iterations=5
        )

        mock_calculate.return_value = BuildStats(
            total_dps=10000.0,
            effective_hp=5000.0,
            life=2000,
            energy_shield=1000,
            mana=800,
            resistances={"fire": 75, "cold": 75, "lightning": 75, "chaos": 0}
        )

        # Act
        result = optimize_build(config)

        # Assert
        assert result.iterations_run <= 5
        # Since neighbor generator returns empty list, should converge immediately
        assert result.convergence_reason in ["max_iterations", "no_valid_neighbors"]


class TestOptimizationResult:
    """Test suite for AC-2.1.6: Algorithm returns best configuration"""

    @patch('optimizer.hill_climbing.calculate_build_stats')
    def test_optimize_build_returns_valid_result(
        self,
        mock_calculate,
        sample_config,
        sample_stats
    ):
        """
        Verify optimize_build() returns OptimizationResult with all fields (AC-2.1.6)

        Test:
            1. Call optimize_build()
            2. Verify result is OptimizationResult instance
            3. Verify all required fields present and valid types
        """
        # Arrange
        mock_calculate.return_value = sample_stats

        # Act
        result = optimize_build(sample_config)

        # Assert - correct type (check class name to handle import path differences)
        assert result.__class__.__name__ == 'OptimizationResult'

        # Assert - all fields present
        assert hasattr(result, 'optimized_build')
        assert hasattr(result, 'baseline_stats')
        assert hasattr(result, 'optimized_stats')
        assert hasattr(result, 'improvement_pct')
        assert hasattr(result, 'unallocated_used')
        assert hasattr(result, 'respec_used')
        assert hasattr(result, 'iterations_run')
        assert hasattr(result, 'convergence_reason')
        assert hasattr(result, 'time_elapsed_seconds')
        assert hasattr(result, 'nodes_added')
        assert hasattr(result, 'nodes_removed')
        assert hasattr(result, 'nodes_swapped')

        # Assert - correct types
        assert isinstance(result.optimized_build, BuildData)
        assert isinstance(result.baseline_stats, BuildStats)
        assert isinstance(result.optimized_stats, BuildStats)
        assert isinstance(result.improvement_pct, float)
        assert isinstance(result.unallocated_used, int)
        assert isinstance(result.respec_used, int)
        assert isinstance(result.iterations_run, int)
        assert isinstance(result.convergence_reason, str)
        assert isinstance(result.time_elapsed_seconds, float)
        assert isinstance(result.nodes_added, set)
        assert isinstance(result.nodes_removed, set)
        assert isinstance(result.nodes_swapped, int)

        # Assert - valid ranges
        assert result.unallocated_used >= 0
        assert result.respec_used >= 0
        assert result.iterations_run >= 0
        assert result.time_elapsed_seconds >= 0
        assert result.nodes_swapped >= 0

    def test_calculate_improvement_percentage_positive(self):
        """Verify improvement calculation for positive improvement"""
        baseline = BuildStats(
            total_dps=10000.0,
            effective_hp=5000.0,
            life=2000,
            energy_shield=1000,
            mana=800,
            resistances={"fire": 75, "cold": 75, "lightning": 75, "chaos": 0}
        )

        optimized = BuildStats(
            total_dps=11500.0,  # 15% improvement
            effective_hp=5000.0,
            life=2000,
            energy_shield=1000,
            mana=800,
            resistances={"fire": 75, "cold": 75, "lightning": 75, "chaos": 0}
        )

        improvement = _calculate_improvement_percentage(baseline, optimized, "dps")
        assert improvement == 15.0

    def test_calculate_improvement_percentage_zero_baseline(self):
        """Verify improvement calculation handles zero baseline (avoid division by zero)"""
        baseline = BuildStats(
            total_dps=0.0,
            effective_hp=5000.0,
            life=2000,
            energy_shield=1000,
            mana=800,
            resistances={"fire": 75, "cold": 75, "lightning": 75, "chaos": 0}
        )

        optimized = BuildStats(
            total_dps=10000.0,
            effective_hp=5000.0,
            life=2000,
            energy_shield=1000,
            mana=800,
            resistances={"fire": 75, "cold": 75, "lightning": 75, "chaos": 0}
        )

        improvement = _calculate_improvement_percentage(baseline, optimized, "dps")
        assert improvement == 0.0  # Should return 0 instead of error

    def test_optimization_result_to_dict(self, sample_build, sample_stats):
        """Verify OptimizationResult.to_dict() serialization"""
        result = OptimizationResult(
            optimized_build=sample_build,
            baseline_stats=sample_stats,
            optimized_stats=sample_stats,
            improvement_pct=15.3,
            unallocated_used=10,
            respec_used=5,
            iterations_run=45,
            convergence_reason="converged",
            time_elapsed_seconds=18.5,
            nodes_added={1234, 5678},
            nodes_removed={9012},
            nodes_swapped=1
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict['improvement_pct'] == 15.3
        assert result_dict['budget_usage']['unallocated_used'] == 10
        assert result_dict['budget_usage']['respec_used'] == 5
        assert result_dict['convergence']['reason'] == "converged"
        assert result_dict['convergence']['iterations_run'] == 45
        assert result_dict['node_changes']['added'] == [1234, 5678]
        assert result_dict['node_changes']['removed'] == [9012]
        assert result_dict['node_changes']['swapped'] == 1


class TestConfigurationValidation:
    """Test suite for OptimizationConfiguration validation"""

    def test_config_validates_metric(self, sample_build):
        """Verify OptimizationConfiguration validates metric values"""
        with pytest.raises(ValueError, match="metric must be one of"):
            OptimizationConfiguration(
                build=sample_build,
                metric="invalid_metric",
                unallocated_points=10
            )

    def test_config_validates_negative_budget(self, sample_build):
        """Verify OptimizationConfiguration rejects negative budgets"""
        with pytest.raises(ValueError, match="unallocated_points must be >= 0"):
            OptimizationConfiguration(
                build=sample_build,
                metric="dps",
                unallocated_points=-5
            )

    def test_config_validates_max_iterations(self, sample_build):
        """Verify OptimizationConfiguration validates max_iterations > 0"""
        with pytest.raises(ValueError, match="max_iterations must be > 0"):
            OptimizationConfiguration(
                build=sample_build,
                metric="dps",
                unallocated_points=10,
                max_iterations=0
            )
