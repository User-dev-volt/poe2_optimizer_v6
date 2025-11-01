"""
Optimization metrics for evaluating build performance.

This module implements multiple optimization goals to support different
playstyles: DPS (damage), EHP (survivability), and Balanced (mix of both).

Primary API:
    calculate_metric(build: BuildData, metric_type: str, baseline: BuildData = None) -> float

Supported Metrics:
    - "dps": Maximize total DPS output
    - "ehp": Maximize effective hit points (survivability)
    - "balanced": Weighted average (60% DPS, 40% EHP)

Architecture:
    - Calls Epic 1 calculate_build_stats() API for BuildStats
    - Extracts relevant stats for each metric type
    - Normalizes metrics for cross-scale comparison
    - Returns float (higher = better)

Performance:
    - Metric calculation: ~0.01ms (negligible vs 2ms PoB calc)
    - No caching (unique mutations per evaluation)

Story 2.6 Implementation:
    - AC-2.6.1: DPS metric (extract total_dps from BuildStats)
    - AC-2.6.2: EHP metric (Life + ES base formula)
    - AC-2.6.3: Balanced metric (60/40 weighted average)
    - AC-2.6.4: Extract correct stats from PoB results
    - AC-2.6.5: Normalization for comparison

References:
    - Tech Spec Epic 2: Lines 277-299 (Metrics API)
    - Tech Spec Epic 2: Lines 640-647 (Acceptance Criteria)
    - Story 2.6: Metric Selection and Evaluation
"""

import logging
import math
from typing import Optional

from ..models.build_data import BuildData
from ..models.build_stats import BuildStats
from ..calculator.build_calculator import calculate_build_stats
from ..calculator.exceptions import CalculationError, CalculationTimeout

logger = logging.getLogger(__name__)

# Supported metric types
METRIC_DPS = "dps"
METRIC_EHP = "ehp"
METRIC_BALANCED = "balanced"

VALID_METRICS = {METRIC_DPS, METRIC_EHP, METRIC_BALANCED}


def calculate_metric(
    build: BuildData,
    metric_type: str,
    baseline: Optional[BuildData] = None
) -> float:
    """
    Calculate optimization metric for a build.

    Evaluates build performance using specified metric type. Calls Epic 1
    calculate_build_stats() API to get BuildStats, then extracts and
    processes relevant stats for the chosen metric.

    Args:
        build: BuildData object to evaluate
        metric_type: Metric type ("dps", "ehp", or "balanced")
        baseline: Optional baseline build for normalization (required for "balanced")
                  Note: If "balanced" metric is used without baseline, falls back to
                  unnormalized weighted average (0.6*DPS + 0.4*EHP), which operates
                  on vastly different scales than normalized version. Provide baseline
                  for consistent comparison.

    Returns:
        float: Metric score (higher = better)
               Returns -infinity if PoB calculation fails

    Raises:
        ValueError: If metric_type is not valid

    Example:
        >>> from src.models.build_data import BuildData
        >>> build = BuildData(...)
        >>> score = calculate_metric(build, "dps")
        >>> print(f"DPS Score: {score}")

    Story 2.6 Coverage:
        - AC-2.6.1: DPS metric extracts total_dps
        - AC-2.6.2: EHP metric calculates Life + ES
        - AC-2.6.3: Balanced metric applies 60/40 weighting
        - AC-2.6.4: Extracts stats from PoB results
        - AC-2.6.5: Normalizes metrics for comparison

    References:
        - Tech Spec Epic 2: Lines 277-299 (Metrics API)
        - Story 2.6 AC-2.6.1 through AC-2.6.5
    """
    # Validate metric type
    if metric_type not in VALID_METRICS:
        raise ValueError(
            f"Invalid metric_type '{metric_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_METRICS))}"
        )

    try:
        # Calculate build stats using Epic 1 API
        stats = calculate_build_stats(build)

        # Calculate metric based on type
        if metric_type == METRIC_DPS:
            return _calculate_dps_metric(stats)
        elif metric_type == METRIC_EHP:
            return _calculate_ehp_metric(stats)
        elif metric_type == METRIC_BALANCED:
            # Balanced metric requires baseline for normalization
            if baseline is None:
                logger.warning(
                    "Balanced metric requested without baseline. "
                    "Using raw DPS+EHP average (normalization disabled)"
                )
                # Fall back to unnormalized average
                dps = _calculate_dps_metric(stats)
                ehp = _calculate_ehp_metric(stats)
                return 0.6 * dps + 0.4 * ehp
            else:
                return _calculate_balanced_metric(stats, build, baseline)

    except (CalculationError, CalculationTimeout) as e:
        # PoB calculation failed - log and return -infinity
        # This allows hill climbing to reject bad neighbors gracefully
        logger.error(
            "Failed to calculate metric '%s' for build: %s",
            metric_type,
            e
        )
        return float('-inf')

    except Exception as e:
        # Unexpected error - log with full traceback and return -infinity
        logger.error(
            "Unexpected error calculating metric '%s': %s",
            metric_type,
            e,
            exc_info=True
        )
        return float('-inf')


def _calculate_dps_metric(stats: BuildStats) -> float:
    """
    Calculate DPS metric (AC-2.6.1).

    Extracts total_dps directly from BuildStats. This is the raw DPS
    output from PoB calculation engine.

    Args:
        stats: BuildStats from calculate_build_stats()

    Returns:
        float: Total DPS (higher = better)

    Example:
        >>> stats = BuildStats(total_dps=125000.5, ...)
        >>> _calculate_dps_metric(stats)
        125000.5

    References:
        - Story 2.6 AC-2.6.1: Support metric "Maximize DPS"
        - Tech Spec Epic 2: Lines 283-284 (DPS metric definition)
    """
    return stats.total_dps


def _calculate_ehp_metric(stats: BuildStats) -> float:
    """
    Calculate EHP metric (AC-2.6.2).

    Calculates effective hit points as Life + Energy Shield. This is the
    base formula for MVP. Full mitigation calculation (armor, evasion, block)
    is deferred to post-MVP.

    Args:
        stats: BuildStats from calculate_build_stats()

    Returns:
        float: Effective HP (higher = better)

    Example:
        >>> stats = BuildStats(life=4500, energy_shield=2000, ...)
        >>> _calculate_ehp_metric(stats)
        6500.0

    References:
        - Story 2.6 AC-2.6.2: Support metric "Maximize EHP"
        - Tech Spec Epic 2: Lines 285-286 (EHP metric definition)
        - Story Context: EHP = Life + ES (base formula for MVP)
    """
    # Base EHP formula for MVP: Life + Energy Shield
    # Full mitigation formula (armor, evasion, block, resistances) deferred to post-MVP
    return float(stats.life + stats.energy_shield)


def _calculate_balanced_metric(
    stats: BuildStats,
    build: BuildData,
    baseline: BuildData
) -> float:
    """
    Calculate balanced metric (AC-2.6.3, AC-2.6.5).

    Computes weighted average of normalized DPS and EHP. Normalization
    ensures DPS improvements (thousands) and EHP improvements (hundreds)
    are comparable despite different scales.

    Formula:
        normalized_value = (current - baseline) / baseline
        balanced_score = 0.6 * normalized_dps + 0.4 * normalized_ehp

    Args:
        stats: BuildStats for current build
        build: BuildData for current build (currently unused, reserved for future
               normalization enhancements like per-class baselines or advanced metrics)
        baseline: BuildData for baseline build (for normalization)

    Returns:
        float: Balanced score (higher = better)

    Example:
        >>> current_stats = BuildStats(total_dps=150000, life=5000, energy_shield=2000, ...)
        >>> # Baseline: DPS=100000, EHP=6000
        >>> # normalized_dps = (150000 - 100000) / 100000 = 0.5
        >>> # normalized_ehp = (7000 - 6000) / 6000 = 0.167
        >>> # score = 0.6 * 0.5 + 0.4 * 0.167 = 0.367
        >>> _calculate_balanced_metric(current_stats, current_build, baseline_build)
        0.367

    References:
        - Story 2.6 AC-2.6.3: Balanced metric with 60/40 weighting
        - Story 2.6 AC-2.6.5: Normalize metrics for comparison
        - Tech Spec Epic 2: Lines 287-291 (Balanced metric definition)
        - Story Context: normalized = (current - baseline) / baseline
    """
    # Calculate baseline stats for normalization
    try:
        baseline_stats = calculate_build_stats(baseline)
    except (CalculationError, CalculationTimeout) as e:
        logger.error("Failed to calculate baseline stats: %s", e)
        # If baseline calculation fails, fall back to unnormalized average
        return 0.6 * stats.total_dps + 0.4 * _calculate_ehp_metric(stats)

    # Extract metric values
    current_dps = stats.total_dps
    current_ehp = _calculate_ehp_metric(stats)
    baseline_dps = baseline_stats.total_dps
    baseline_ehp = _calculate_ehp_metric(baseline_stats)

    # Normalize metrics: (current - baseline) / baseline
    # Handle division by zero - if baseline is 0, current value is the improvement
    if baseline_dps > 0:
        normalized_dps = (current_dps - baseline_dps) / baseline_dps
    else:
        # Baseline has no DPS, treat current DPS as pure improvement
        # Scale by 1000.0 to normalize typical DPS values (thousands) to 0-1 range
        # matching the scale of percentage improvements from non-zero baselines
        normalized_dps = current_dps / 1000.0

    if baseline_ehp > 0:
        normalized_ehp = (current_ehp - baseline_ehp) / baseline_ehp
    else:
        # Baseline has no EHP, treat current EHP as pure improvement
        # Scale by 1000.0 to normalize typical EHP values (thousands) to 0-1 range
        # matching the scale of percentage improvements from non-zero baselines
        normalized_ehp = current_ehp / 1000.0

    # Apply weights: 60% DPS, 40% EHP
    balanced_score = 0.6 * normalized_dps + 0.4 * normalized_ehp

    logger.debug(
        "Balanced metric: DPS=%.1f (baseline=%.1f, norm=%.3f), "
        "EHP=%.1f (baseline=%.1f, norm=%.3f), score=%.3f",
        current_dps, baseline_dps, normalized_dps,
        current_ehp, baseline_ehp, normalized_ehp,
        balanced_score
    )

    return balanced_score
