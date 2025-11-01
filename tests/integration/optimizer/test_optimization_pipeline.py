"""
Integration tests for Hill Climbing Optimizer with real PoB calculator

Tests end-to-end optimization pipeline:
- Real calculate_build_stats() calls (no mocking)
- Integration with Epic 1 calculator API
- Verify OptimizationResult correctness
- Validate performance within acceptable limits

Story: 2.1 - Implement Hill Climbing Core Algorithm
Task 5: Integration with Epic 1 calculator
Author: Dev Agent (Amelia)
Date: 2025-10-27
"""

import pytest
import time
from src.optimizer import optimize_build
from src.models.build_data import BuildData, CharacterClass
from src.models.optimization_config import OptimizationConfiguration, OptimizationResult
from src.calculator.build_calculator import calculate_build_stats


@pytest.fixture
def small_witch_build():
    """
    Small Witch build for fast integration testing.

    Level 50, 30 allocated nodes (simple tree for quick calculations)
    """
    return BuildData(
        character_class=CharacterClass.WITCH,
        level=50,
        passive_nodes={
            # Start nodes near Witch starting position
            41263, 36634, 33631, 26725, 61419, 17219, 12613,
            48768, 55114, 61666, 6230, 18436, 11420, 46519,
            61305, 33753, 48439, 6910, 27415, 21835,
            # Add some life/ES nodes
            49080, 28475, 55190, 36931, 14993, 64583, 61834,
            2491, 27659, 48707
        },
        build_name="Test Small Witch"
    )


@pytest.fixture
def medium_warrior_build():
    """
    Medium Warrior build for integration testing.

    Level 70, 50 allocated nodes (moderate complexity)
    """
    return BuildData(
        character_class=CharacterClass.WARRIOR,
        level=70,
        passive_nodes={
            # Warrior starting area
            54142, 6114, 12161, 32763, 61419, 41263, 33631,
            17219, 12613, 48768, 55114, 61666, 6230, 18436,
            # Life nodes
            61305, 33753, 48439, 6910, 27415, 21835, 49080,
            28475, 55190, 36931, 14993, 64583, 61834, 2491,
            # Physical damage nodes
            36634, 26725, 11420, 46519, 27659, 48707, 24970,
            63447, 24971, 4397, 12926, 22618, 14914, 51198,
            # Additional strength nodes
            61305, 55885, 28859, 41876, 54127, 22748, 12596
        },
        build_name="Test Medium Warrior"
    )


class TestOptimizationPipelineIntegration:
    """Integration tests with real PoB calculator (Subtask 5.3)"""

    def test_optimize_build_integration_small_build(self, small_witch_build):
        """
        Verify optimization completes without errors on small build (AC-2.1.6 integration)

        Test:
            1. Create OptimizationConfiguration with small Witch build
            2. Limit max_iterations=5 for test speed
            3. Call optimize_build() with real calculator
            4. Verify result is valid OptimizationResult
            5. Verify no exceptions raised
        """
        # Arrange
        config = OptimizationConfiguration(
            build=small_witch_build,
            metric="dps",
            unallocated_points=15,
            max_iterations=5,  # Limit for test speed
            max_time_seconds=30
        )

        # Act
        start = time.time()
        result = optimize_build(config)
        elapsed = time.time() - start

        # Assert - valid result
        assert isinstance(result, OptimizationResult)
        assert result.optimized_build is not None
        assert result.baseline_stats is not None
        assert result.optimized_stats is not None

        # Assert - improvement is non-negative (never worse than baseline)
        assert result.improvement_pct >= 0.0

        # Assert - convergence info present
        assert result.convergence_reason in [
            "converged",
            "max_iterations",
            "timeout",
            "no_valid_neighbors"
        ]
        assert result.iterations_run >= 0
        assert result.iterations_run <= config.max_iterations

        # Assert - reasonable execution time
        assert elapsed < 60.0  # Should complete within 60 seconds for small build

        print(f"\nIntegration test result:")
        print(f"  Iterations: {result.iterations_run}")
        print(f"  Improvement: {result.improvement_pct:.2f}%")
        print(f"  Convergence: {result.convergence_reason}")
        print(f"  Time: {elapsed:.2f}s")

    def test_optimize_build_integration_medium_build(self, medium_warrior_build):
        """
        Verify optimization handles medium complexity build

        Test:
            1. Use Warrior level 70 build (50 allocated nodes)
            2. Limit max_iterations=3 for test speed
            3. Verify optimization completes without errors
        """
        # Arrange
        config = OptimizationConfiguration(
            build=medium_warrior_build,
            metric="ehp",
            unallocated_points=10,
            max_iterations=3,
            max_time_seconds=30
        )

        # Act
        start = time.time()
        result = optimize_build(config)
        elapsed = time.time() - start

        # Assert
        assert isinstance(result, OptimizationResult)
        assert result.improvement_pct >= 0.0
        assert elapsed < 60.0

        print(f"\nMedium build test result:")
        print(f"  Iterations: {result.iterations_run}")
        print(f"  Improvement: {result.improvement_pct:.2f}%")
        print(f"  Time: {elapsed:.2f}s")

    def test_optimize_build_baseline_calculation_accuracy(self, small_witch_build):
        """
        Verify baseline calculation matches direct calculator call (Subtask 1.4)

        Test:
            1. Calculate stats directly using calculate_build_stats()
            2. Run optimize_build() and get baseline_stats
            3. Verify both calculations match
        """
        # Arrange - calculate baseline directly
        direct_stats = calculate_build_stats(small_witch_build)

        # Act - optimize and get baseline from result
        config = OptimizationConfiguration(
            build=small_witch_build,
            metric="dps",
            unallocated_points=10,
            max_iterations=1
        )
        result = optimize_build(config)

        # Assert - baseline stats match
        assert result.baseline_stats.total_dps == direct_stats.total_dps
        assert result.baseline_stats.effective_hp == direct_stats.effective_hp
        assert result.baseline_stats.life == direct_stats.life

    def test_optimize_build_respects_max_iterations(self, small_witch_build):
        """
        Verify max_iterations limit is enforced

        Test:
            1. Set max_iterations=2
            2. Verify iterations_run <= 2
        """
        # Arrange
        config = OptimizationConfiguration(
            build=small_witch_build,
            metric="dps",
            unallocated_points=10,
            max_iterations=2
        )

        # Act
        result = optimize_build(config)

        # Assert
        assert result.iterations_run <= 2

    def test_optimize_build_respects_timeout(self, small_witch_build):
        """
        Verify max_time_seconds timeout is enforced

        Test:
            1. Set max_time_seconds=1 (very short)
            2. Verify elapsed time is close to timeout
            3. Verify convergence_reason includes "timeout" or "no_valid_neighbors"
        """
        # Arrange
        config = OptimizationConfiguration(
            build=small_witch_build,
            metric="dps",
            unallocated_points=10,
            max_iterations=1000,  # High limit, should timeout first
            max_time_seconds=1
        )

        # Act
        start = time.time()
        result = optimize_build(config)
        elapsed = time.time() - start

        # Assert - either timed out or converged quickly
        assert result.convergence_reason in ["timeout", "no_valid_neighbors", "converged"]
        # Elapsed should be close to timeout (within 0.5s margin for overhead)
        if result.convergence_reason == "timeout":
            assert elapsed >= 1.0
            assert elapsed < 2.0


class TestCalculatorIntegration:
    """Tests for Subtask 5.1 & 5.2: Import and use Epic 1 calculator"""

    def test_import_calculate_build_stats(self):
        """Verify calculate_build_stats can be imported (Subtask 5.1)"""
        from src.calculator.build_calculator import calculate_build_stats
        assert callable(calculate_build_stats)

    def test_import_build_models(self):
        """Verify BuildData and BuildStats can be imported (Subtask 5.2)"""
        from src.models.build_data import BuildData, CharacterClass
        from src.models.build_stats import BuildStats

        assert BuildData is not None
        assert BuildStats is not None
        assert CharacterClass is not None

    def test_calculate_build_stats_works(self, small_witch_build):
        """
        Verify calculate_build_stats() executes successfully (Subtask 5.1)

        Test:
            1. Call calculate_build_stats() with test build
            2. Verify BuildStats returned
            3. Verify stats have reasonable values
        """
        # Act
        stats = calculate_build_stats(small_witch_build)

        # Assert
        from src.models.build_stats import BuildStats
        assert isinstance(stats, BuildStats)

        # Verify reasonable values (non-negative)
        assert stats.total_dps >= 0
        assert stats.effective_hp >= 0
        assert stats.life > 0
        assert stats.energy_shield >= 0
        assert stats.mana > 0

        print(f"\nCalculator integration test:")
        print(f"  DPS: {stats.total_dps:.1f}")
        print(f"  EHP: {stats.effective_hp:.1f}")
        print(f"  Life: {stats.life}")


class TestOptimizationResultValidation:
    """Additional validation tests for OptimizationResult"""

    def test_optimization_result_budget_tracking(self, small_witch_build):
        """
        Verify budget usage is tracked correctly

        Test:
            1. Set unallocated_points=10, respec_points=5
            2. Run optimization
            3. Verify unallocated_used + respec_used doesn't exceed limits
        """
        # Arrange
        config = OptimizationConfiguration(
            build=small_witch_build,
            metric="dps",
            unallocated_points=10,
            respec_points=5,
            max_iterations=5
        )

        # Act
        result = optimize_build(config)

        # Assert - budget limits respected
        assert result.unallocated_used <= config.unallocated_points
        assert result.respec_used <= config.respec_points

        # Assert - usage is non-negative
        assert result.unallocated_used >= 0
        assert result.respec_used >= 0

    def test_optimization_result_node_tracking(self, small_witch_build):
        """
        Verify node changes are tracked (Subtask 3.3)

        Test:
            1. Run optimization
            2. Verify nodes_added, nodes_removed, nodes_swapped are tracked
            3. Verify types are correct (sets and int)
        """
        # Arrange
        config = OptimizationConfiguration(
            build=small_witch_build,
            metric="dps",
            unallocated_points=10,
            max_iterations=5
        )

        # Act
        result = optimize_build(config)

        # Assert - tracking fields exist and have correct types
        assert isinstance(result.nodes_added, set)
        assert isinstance(result.nodes_removed, set)
        assert isinstance(result.nodes_swapped, int)
        assert result.nodes_swapped >= 0

    def test_optimization_result_serialization(self, small_witch_build):
        """
        Verify OptimizationResult.to_dict() produces valid output

        Test:
            1. Run optimization
            2. Call to_dict()
            3. Verify all fields present in dictionary
        """
        # Arrange
        config = OptimizationConfiguration(
            build=small_witch_build,
            metric="dps",
            unallocated_points=10,
            max_iterations=2
        )

        # Act
        result = optimize_build(config)
        result_dict = result.to_dict()

        # Assert - dictionary structure
        assert isinstance(result_dict, dict)
        assert 'improvement_pct' in result_dict
        assert 'baseline_stats' in result_dict
        assert 'optimized_stats' in result_dict
        assert 'budget_usage' in result_dict
        assert 'convergence' in result_dict
        assert 'node_changes' in result_dict

        # Assert - nested structures
        assert 'unallocated_used' in result_dict['budget_usage']
        assert 'reason' in result_dict['convergence']
        assert 'added' in result_dict['node_changes']


@pytest.mark.slow
class TestOptimizationPerformance:
    """Performance validation tests (optional, marked as slow)"""

    def test_baseline_calculation_performance(self, small_witch_build):
        """
        Verify baseline calculation completes quickly (<100ms per AC-1.5.4)

        Test:
            1. Calculate baseline stats
            2. Verify execution time < 200ms (allows for first-call overhead)
        """
        # Act
        start = time.time()
        stats = calculate_build_stats(small_witch_build)
        elapsed = (time.time() - start) * 1000  # Convert to ms

        # Assert
        assert elapsed < 200.0  # First call may take ~200ms per AC-1.5.4
        print(f"\nBaseline calculation time: {elapsed:.1f}ms")

    def test_optimization_iteration_performance(self, small_witch_build):
        """
        Verify optimization completes within performance budget

        Target: <2 minutes for typical builds (300 iterations × 400ms avg)
        Test limit: 5 iterations should complete in <5 seconds
        """
        # Arrange
        config = OptimizationConfiguration(
            build=small_witch_build,
            metric="dps",
            unallocated_points=10,
            max_iterations=5,
            max_time_seconds=300
        )

        # Act
        start = time.time()
        result = optimize_build(config)
        elapsed = time.time() - start

        # Assert
        assert elapsed < 5.0  # 5 iterations in <5 seconds
        print(f"\n5 iterations completed in {elapsed:.2f}s")
        print(f"Average per iteration: {elapsed / max(result.iterations_run, 1):.2f}s")
