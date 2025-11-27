"""Hill climbing optimization algorithm for passive tree configuration

This module implements steepest-ascent hill climbing to iteratively improve
passive tree allocations based on DPS, EHP, or balanced objectives.

Algorithm:
    1. Calculate baseline stats for current build
    2. Generate neighbor configurations (add/swap 1 node)
    3. Evaluate each neighbor using PoB calculations
    4. Select best neighbor if improvement found
    5. Update state and check convergence
    6. Repeat until converged or timeout

Performance:
    - Target: <2 minutes for typical builds (300 iterations)
    - Maximum: <5 minutes for complex builds (600 iterations)
    - Per-iteration: ~400ms average (2ms calc × 200 neighbors)

References:
    - Tech Spec Epic 2 - Section 7.3: APIs and Interfaces
    - Tech Spec Epic 2 - Section 7.4: Workflows and Sequencing
    - Story 2.1 Tasks 1-3: Core algorithm implementation
"""

import logging
import time
from typing import List, Tuple, Optional
from dataclasses import replace

from src.models.build_data import BuildData
from src.models.build_stats import BuildStats
from src.models.optimization_config import (
    OptimizationConfiguration,
    OptimizationResult
)
from src.calculator.build_calculator import calculate_build_stats
from src.calculator.passive_tree import get_passive_tree
from src.optimizer.convergence import ConvergenceDetector
from src.optimizer.progress import ProgressTracker
from src.optimizer.budget_tracker import BudgetState
from src.optimizer.neighbor_generator import generate_neighbors, BudgetState as NeighborBudgetState

logger = logging.getLogger(__name__)


def optimize_build(config: OptimizationConfiguration) -> OptimizationResult:
    """
    Execute hill climbing optimization on a build's passive tree.

    Implements steepest-ascent hill climbing algorithm:
    1. Start with baseline build and calculate stats
    2. Generate all valid neighbor configurations (1-hop moves)
    3. Evaluate all neighbors using PoB calculations
    4. Select best neighbor if improvement found
    5. Update build and budget state
    6. Check convergence conditions
    7. Repeat until converged, max iterations, or timeout

    Args:
        config: OptimizationConfiguration with build, metric, budgets, and limits

    Returns:
        OptimizationResult with optimized build, stats comparison, improvement %,
        budget usage, convergence info, and node change tracking

    Raises:
        ValueError: If configuration is invalid
        CalculationError: If PoB calculation fails
        CalculationTimeout: If single calculation exceeds timeout

    Example:
        >>> config = OptimizationConfiguration(
        ...     build=my_build,
        ...     metric="dps",
        ...     unallocated_points=15,
        ...     max_iterations=600
        ... )
        >>> result = optimize_build(config)
        >>> print(f"Improvement: {result.improvement_pct:.1f}%")
        >>> print(f"Converged in {result.iterations_run} iterations")

    Performance:
        - Typical: 300 iterations × 400ms = 120s (2 minutes)
        - Maximum: 600 iterations × 425ms = 255s (4.25 minutes)

    References:
        - Tech Spec Epic 2 - Section 7.3: optimize_build() API
        - Story 2.1 AC #1-6: Algorithm acceptance criteria
    """
    logger.info(
        "Starting optimization: metric=%s, unallocated=%d, respec=%s, max_iter=%d",
        config.metric,
        config.unallocated_points,
        config.respec_points,
        config.max_iterations
    )

    start_time = time.time()

    # ========================================
    # Task 1.4: Calculate baseline stats (AC #1)
    # ========================================
    logger.debug("Calculating baseline stats for original build")
    baseline_stats = calculate_build_stats(config.build)

    logger.info(
        "Baseline calculated: DPS=%.1f, Life=%d, EHP=%.1f",
        baseline_stats.total_dps,
        baseline_stats.life,
        baseline_stats.effective_hp
    )

    # ========================================
    # Initialize passive tree for neighbor generation
    # ========================================
    tree = get_passive_tree()
    logger.debug("Passive tree loaded for neighbor generation")

    # ========================================
    # Task 2.1: Initialize optimization state
    # ========================================
    current_build = config.build
    current_stats = baseline_stats
    best_build = config.build
    best_stats = baseline_stats

    iterations_run = 0
    nodes_added_total = set()
    nodes_removed_total = set()
    swaps_count = 0

    # Budget tracking
    unallocated_remaining = config.unallocated_points
    respec_remaining = config.respec_points if config.respec_points is not None else float('inf')

    # Convergence tracking (Story 2.7: ConvergenceDetector integration)
    convergence_detector = ConvergenceDetector(
        patience=config.convergence_patience,
        min_improvement=0.001  # 0.1% threshold from tech spec
    )
    logger.debug(
        "Convergence detector initialized: patience=%d, min_improvement=%.3f",
        config.convergence_patience,
        0.001
    )

    # Progress tracking (Story 2.8: ProgressTracker integration)
    progress_tracker = ProgressTracker(callback=config.progress_callback)
    baseline_metric = _get_metric_value(baseline_stats, config.metric)
    progress_tracker.set_baseline(baseline_metric)
    logger.debug("Progress tracker initialized with baseline metric: %.2f", baseline_metric)

    # ========================================
    # Task 2.7: Main optimization loop
    # ========================================
    while iterations_run < config.max_iterations:
        # Check timeout (AC #5 - part of convergence)
        elapsed = time.time() - start_time
        if elapsed >= config.max_time_seconds:
            logger.info("Timeout reached: %.1f seconds", elapsed)
            convergence_reason = "timeout"
            break

        # ========================================
        # Task 2.2: Generate neighbors
        # ========================================
        # Create budget state for neighbor generator
        neighbor_budget = NeighborBudgetState(
            unallocated_available=config.unallocated_points,
            unallocated_used=config.unallocated_points - int(unallocated_remaining),
            respec_available=config.respec_points,
            respec_used=0 if config.respec_points is None else (config.respec_points - int(respec_remaining))
        )

        # Generate mutations (returns List[TreeMutation])
        mutations = generate_neighbors(
            current_build,
            tree,
            neighbor_budget,
            prioritize_adds=True
        )

        # Convert mutations to BuildData neighbors
        neighbors = [mutation.apply(current_build) for mutation in mutations]

        # Track mutations for later use (needed for node change tracking)
        neighbor_mutations = mutations

        # Check if no valid neighbors (convergence condition)
        if not neighbors:
            logger.info("No valid neighbors found - converged")
            convergence_reason = "no_valid_neighbors"
            break

        # ========================================
        # Task 2.3: Evaluate all neighbors (AC #3)
        # ========================================
        neighbor_evaluations = _evaluate_neighbors(
            neighbors,
            config.metric,
            current_stats
        )

        # ========================================
        # Task 2.4: Select best neighbor (AC #4)
        # ========================================
        best_neighbor = _select_best_neighbor(
            neighbor_evaluations,
            neighbor_mutations,
            config.metric
        )

        # ========================================
        # Task 2.5: Update state if improvement found (AC #4)
        # ========================================
        if best_neighbor is not None:
            improved_build, improved_stats, nodes_added, nodes_removed = best_neighbor

            # Track node changes
            nodes_added_total.update(nodes_added)
            nodes_removed_total.update(nodes_removed)
            if nodes_added and nodes_removed:
                swaps_count += 1

            # Update budget
            unallocated_remaining -= len(nodes_added)
            respec_remaining -= len(nodes_removed) if respec_remaining != float('inf') else 0

            # Update current state
            current_build = improved_build
            current_stats = improved_stats
            best_build = improved_build
            best_stats = improved_stats

            # Update convergence detector with improved metric (Story 2.7)
            current_metric = _get_metric_value(improved_stats, config.metric)
            convergence_detector.update(current_metric)

            logger.debug(
                "Iteration %d: Improvement found (DPS=%.1f, EHP=%.1f, metric=%.1f)",
                iterations_run,
                improved_stats.total_dps,
                improved_stats.effective_hp,
                current_metric
            )
        else:
            # No improvement - update detector with current metric (Story 2.7)
            current_metric = _get_metric_value(current_stats, config.metric)
            convergence_detector.update(current_metric)

            logger.debug(
                "Iteration %d: No improvement (patience=%d/%d)",
                iterations_run,
                convergence_detector.iterations_without_improvement,
                convergence_detector.patience
            )

        # ========================================
        # Task 2.6: Check convergence (Story 2.7: ConvergenceDetector integration)
        # ========================================
        if convergence_detector.has_converged():
            reason = convergence_detector.get_convergence_reason()
            logger.info(reason)
            convergence_reason = "converged"
            break

        iterations_run += 1

        # Progress tracking (Story 2.8: Update progress tracker)
        current_budget = BudgetState(
            unallocated_available=config.unallocated_points,
            unallocated_used=config.unallocated_points - int(unallocated_remaining),
            respec_available=config.respec_points,
            respec_used=(config.respec_points - int(respec_remaining)) if config.respec_points is not None else 0
        )
        best_metric = _get_metric_value(best_stats, config.metric)
        progress_tracker.update(iterations_run, best_metric, current_budget)

    # Handle case where loop completed without break
    else:
        convergence_reason = "max_iterations"
        logger.info("Max iterations reached: %d", config.max_iterations)

    # ========================================
    # Story 2.8: Final progress update on completion
    # ========================================
    final_budget = BudgetState(
        unallocated_available=config.unallocated_points,
        unallocated_used=config.unallocated_points - int(unallocated_remaining),
        respec_available=config.respec_points,
        respec_used=(config.respec_points - int(respec_remaining)) if config.respec_points is not None else 0
    )
    final_metric = _get_metric_value(best_stats, config.metric)
    progress_tracker.update(iterations_run, final_metric, final_budget)

    # ========================================
    # Task 3: Generate optimization result (AC #6)
    # ========================================
    elapsed_time = time.time() - start_time

    # Task 3.1 & 3.2: Calculate final stats and improvement
    improvement_pct = _calculate_improvement_percentage(
        baseline_stats,
        best_stats,
        config.metric
    )

    # Task 3.3 & 3.4: Package result
    result = OptimizationResult(
        optimized_build=best_build,
        baseline_stats=baseline_stats,
        optimized_stats=best_stats,
        improvement_pct=improvement_pct,
        unallocated_used=config.unallocated_points - int(unallocated_remaining),
        respec_used=config.respec_points - int(respec_remaining) if config.respec_points is not None else 0,
        iterations_run=iterations_run,
        convergence_reason=convergence_reason,
        time_elapsed_seconds=elapsed_time,
        nodes_added=nodes_added_total,
        nodes_removed=nodes_removed_total,
        nodes_swapped=swaps_count
    )

    logger.info(
        "Optimization complete: improvement=%.2f%%, iterations=%d, time=%.1fs, reason=%s",
        improvement_pct,
        iterations_run,
        elapsed_time,
        convergence_reason
    )

    return result


def _generate_neighbors_placeholder(
    current_build: BuildData,
    unallocated_remaining: int,
    respec_remaining: float
) -> List[BuildData]:
    """
    PLACEHOLDER for neighbor generation (Story 2.2).

    For Story 2.1, this returns an empty list to trigger immediate convergence.
    Story 2.2 will implement full neighbor generation with:
    - Add node mutations (1-hop from allocated nodes)
    - Swap node mutations (remove 1, add 1)
    - Connectivity validation
    - Budget enforcement
    - Prioritization heuristics

    Args:
        current_build: Current BuildData state
        unallocated_remaining: Available free points
        respec_remaining: Available respec points (inf = unlimited)

    Returns:
        Empty list (Story 2.1 placeholder)
        Story 2.2 will return List[BuildData] with neighbor configurations

    References:
        - Story 2.2: Generate neighbor configurations (1-hop moves)
        - Tech Spec Epic 2 - Section 7.4: Neighbor generation workflow
    """
    logger.debug("Neighbor generation placeholder - returning empty list")
    # Story 2.2 will implement: return generate_neighbors(current_build, ...)
    return []


def _evaluate_neighbors(
    neighbors: List[BuildData],
    metric: str,
    baseline_stats: BuildStats
) -> List[Tuple[BuildData, BuildStats]]:
    """
    Evaluate all neighbor configurations using PoB calculations (AC #3).

    Calculates statistics for each neighbor build and returns results.
    Implements steepest-ascent strategy by evaluating ALL neighbors.

    Args:
        neighbors: List of neighbor BuildData configurations
        metric: Optimization metric ("dps", "ehp", "balanced")
        baseline_stats: Baseline stats for comparison

    Returns:
        List of (build, stats) tuples for neighbors that calculated successfully

    References:
        - Story 2.1 Task 2.3: Steepest-ascent evaluation
        - Tech Spec Epic 2 - Section 7.4: Evaluate neighbors workflow
    """
    evaluations = []

    for neighbor in neighbors:
        try:
            stats = calculate_build_stats(neighbor)
            evaluations.append((neighbor, stats))

        except Exception as e:
            # Log error and skip this neighbor
            logger.warning("Failed to evaluate neighbor: %s", e)
            continue

    logger.debug("Evaluated %d/%d neighbors successfully", len(evaluations), len(neighbors))
    return evaluations


def _select_best_neighbor(
    evaluations: List[Tuple[BuildData, BuildStats]],
    mutations: List,
    metric: str
) -> Optional[Tuple[BuildData, BuildStats, set, set]]:
    """
    Select the best neighbor from evaluations based on metric (AC #4).

    Implements steepest-ascent selection: choose neighbor with greatest improvement.
    Returns None if no improvement found (convergence signal).

    Args:
        evaluations: List of (build, stats) tuples from _evaluate_neighbors
        mutations: List of TreeMutation objects corresponding to neighbors
        metric: Optimization metric ("dps", "ehp", "balanced")

    Returns:
        Tuple of (best_build, best_stats, nodes_added, nodes_removed) or None
        nodes_added and nodes_removed are Set[int] for tracking changes

    References:
        - Story 2.1 Task 2.4: Best neighbor selection logic
        - Tech Spec Epic 2 - Section 7.4: Update state workflow
    """
    if not evaluations:
        return None

    # Find best neighbor by metric value
    best_idx = max(range(len(evaluations)), key=lambda i: _get_metric_value(evaluations[i][1], metric))
    best_build, best_stats = evaluations[best_idx]

    # Extract node changes from corresponding mutation
    best_mutation = mutations[best_idx]
    nodes_added = best_mutation.nodes_added
    nodes_removed = best_mutation.nodes_removed

    return (best_build, best_stats, nodes_added, nodes_removed)


def _get_metric_value(stats: BuildStats, metric: str) -> float:
    """
    Extract metric value from BuildStats (simplified for Story 2.1).

    Story 2.6 will implement full metric calculation with:
    - Weighted objectives for "balanced" metric
    - Normalization and scaling
    - Custom metric formulas

    Args:
        stats: BuildStats from PoB calculation
        metric: Optimization metric ("dps", "ehp", "balanced")

    Returns:
        Numeric value for optimization (higher is better)

    References:
        - Story 2.6: Metric selection and evaluation
    """
    if metric == "dps":
        return stats.total_dps
    elif metric == "ehp":
        return stats.effective_hp
    elif metric == "balanced":
        # Simplified balanced metric (Story 2.6 will implement proper normalization)
        # Tech spec: 60% DPS, 40% EHP weighting
        return stats.total_dps * 0.6 + stats.effective_hp * 0.4
    else:
        raise ValueError(f"Unknown metric: {metric}")


def _calculate_improvement_percentage(
    baseline_stats: BuildStats,
    optimized_stats: BuildStats,
    metric: str
) -> float:
    """
    Calculate improvement percentage for the target metric (Task 3.2).

    Formula: ((optimized - baseline) / baseline) * 100

    Args:
        baseline_stats: Original build statistics
        optimized_stats: Optimized build statistics
        metric: Target optimization metric

    Returns:
        Improvement percentage (e.g., 15.3 means +15.3% improvement)
        Returns 0.0 if baseline is 0 (avoid division by zero)

    Example:
        >>> baseline = BuildStats(total_dps=10000, ...)
        >>> optimized = BuildStats(total_dps=11500, ...)
        >>> improvement = _calculate_improvement_percentage(baseline, optimized, "dps")
        >>> print(improvement)  # 15.0
    """
    baseline_value = _get_metric_value(baseline_stats, metric)
    optimized_value = _get_metric_value(optimized_stats, metric)

    if baseline_value == 0:
        return 0.0

    improvement = ((optimized_value - baseline_value) / baseline_value) * 100
    return round(improvement, 2)
