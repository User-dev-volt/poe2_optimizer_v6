"""Optimization engine for Path of Building builds

This package implements hill climbing optimization for passive tree configurations.

Primary API:
    optimize_build(config: OptimizationConfiguration) -> OptimizationResult
    calculate_metric(build: BuildData, metric_type: str) -> float

Example:
    >>> from src.optimizer import optimize_build, calculate_metric
    >>> from src.models.optimization_config import OptimizationConfiguration
    >>> config = OptimizationConfiguration(
    ...     build=my_build,
    ...     metric="dps",
    ...     unallocated_points=15
    ... )
    >>> result = optimize_build(config)
    >>> print(f"Improvement: {result.improvement_pct:.1f}%")

References:
    - Tech Spec Epic 2 - Section 7.1: Services and Modules
    - Story 2.1: Implement Hill Climbing Core Algorithm
    - Story 2.6: Metric Selection and Evaluation
"""

from src.optimizer.hill_climbing import optimize_build
from src.optimizer.metrics import calculate_metric, METRIC_DPS, METRIC_EHP, METRIC_BALANCED

__all__ = [
    'optimize_build',
    'calculate_metric',
    'METRIC_DPS',
    'METRIC_EHP',
    'METRIC_BALANCED'
]
