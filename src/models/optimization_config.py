"""Data models for optimization configuration and results"""

from dataclasses import dataclass, field
from typing import Optional, Callable, Set
from src.models.build_data import BuildData
from src.models.build_stats import BuildStats


@dataclass
class OptimizationConfiguration:
    """
    Input configuration for optimize_build() function.

    Defines the optimization parameters including the starting build,
    optimization objective, budget constraints, and algorithm limits.

    Fields:
        build: Starting BuildData to optimize from (immutable baseline)
        metric: Optimization objective - "dps", "ehp", or "balanced"
        unallocated_points: Available free passive points to allocate
        respec_points: Optional points available for respeccing (None = unlimited deallocate)
        max_iterations: Maximum optimization iterations (default: 600)
        max_time_seconds: Timeout limit in seconds (default: 300 = 5 minutes)
        convergence_patience: Iterations without improvement before stopping (default: 3)
        progress_callback: Optional callback function for progress updates

    Validation:
        - build must be valid BuildData instance
        - metric must be one of: "dps", "ehp", "balanced"
        - unallocated_points must be >= 0
        - respec_points must be >= 0 if provided
        - max_iterations must be > 0
        - max_time_seconds must be > 0
        - convergence_patience must be > 0

    Example:
        >>> config = OptimizationConfiguration(
        ...     build=my_build,
        ...     metric="dps",
        ...     unallocated_points=15,
        ...     respec_points=10,
        ...     max_iterations=600,
        ...     max_time_seconds=300
        ... )

    References:
        - Tech Spec Epic 2 - Section 7.2: Data Models and Contracts
        - Story 2.1 Task 1: Design core algorithm structure
    """

    # Required fields
    build: BuildData
    metric: str
    unallocated_points: int

    # Optional budget
    respec_points: Optional[int] = None

    # Algorithm limits (with defaults from Tech Spec)
    max_iterations: int = 600
    max_time_seconds: int = 300
    convergence_patience: int = 3

    # Progress reporting
    progress_callback: Optional[Callable[[int, float, str], None]] = None

    def __post_init__(self):
        """
        Validate configuration parameters after initialization.

        Raises:
            ValueError: If any validation fails
            TypeError: If types are incorrect
        """
        # Validate build (check class name to handle different import paths)
        if not (hasattr(self.build, '__class__') and
                self.build.__class__.__name__ == 'BuildData'):
            raise TypeError(f"build must be BuildData, got {type(self.build)}")

        # Validate metric
        valid_metrics = {"dps", "ehp", "balanced"}
        if self.metric not in valid_metrics:
            raise ValueError(
                f"metric must be one of {valid_metrics}, got '{self.metric}'"
            )

        # Validate budget
        if self.unallocated_points < 0:
            raise ValueError(
                f"unallocated_points must be >= 0, got {self.unallocated_points}"
            )

        if self.respec_points is not None and self.respec_points < 0:
            raise ValueError(
                f"respec_points must be >= 0 or None, got {self.respec_points}"
            )

        # Validate limits
        if self.max_iterations <= 0:
            raise ValueError(
                f"max_iterations must be > 0, got {self.max_iterations}"
            )

        if self.max_time_seconds <= 0:
            raise ValueError(
                f"max_time_seconds must be > 0, got {self.max_time_seconds}"
            )

        if self.convergence_patience <= 0:
            raise ValueError(
                f"convergence_patience must be > 0, got {self.convergence_patience}"
            )


@dataclass
class OptimizationResult:
    """
    Output of optimize_build() function.

    Contains the optimized build, statistics comparison, improvement metrics,
    budget usage tracking, convergence information, and node change summary.

    Fields:
        optimized_build: Best BuildData found during optimization
        baseline_stats: Statistics of original build (before optimization)
        optimized_stats: Statistics of optimized build (after optimization)
        improvement_pct: Percentage improvement in target metric (e.g., 12.5 = +12.5%)
        unallocated_used: Number of unallocated points spent
        respec_used: Number of respec points spent
        iterations_run: Total iterations executed
        convergence_reason: Why optimization stopped (e.g., "converged", "max_iterations", "timeout")
        time_elapsed_seconds: Total optimization time in seconds
        nodes_added: Set of node IDs added during optimization
        nodes_removed: Set of node IDs removed during optimization
        nodes_swapped: Count of swap operations performed (add + remove in same iteration)

    Example:
        >>> result = OptimizationResult(
        ...     optimized_build=new_build,
        ...     baseline_stats=baseline,
        ...     optimized_stats=optimized,
        ...     improvement_pct=15.3,
        ...     unallocated_used=10,
        ...     respec_used=5,
        ...     iterations_run=45,
        ...     convergence_reason="converged",
        ...     time_elapsed_seconds=18.5,
        ...     nodes_added={1234, 5678},
        ...     nodes_removed={9012},
        ...     nodes_swapped=1
        ... )

    References:
        - Tech Spec Epic 2 - Section 7.2: Data Models and Contracts
        - Story 2.1 Task 3: Implement result generation
    """

    # Builds and stats
    optimized_build: BuildData
    baseline_stats: BuildStats
    optimized_stats: BuildStats

    # Improvement metrics
    improvement_pct: float

    # Budget usage
    unallocated_used: int
    respec_used: int

    # Convergence info
    iterations_run: int
    convergence_reason: str
    time_elapsed_seconds: float

    # Node changes
    nodes_added: Set[int] = field(default_factory=set)
    nodes_removed: Set[int] = field(default_factory=set)
    nodes_swapped: int = 0

    def __post_init__(self):
        """
        Validate result fields after initialization.

        Raises:
            ValueError: If any validation fails
            TypeError: If types are incorrect
        """
        # Validate types (check class names to handle different import paths)
        if not (hasattr(self.optimized_build, '__class__') and
                self.optimized_build.__class__.__name__ == 'BuildData'):
            raise TypeError(
                f"optimized_build must be BuildData, got {type(self.optimized_build)}"
            )

        if not (hasattr(self.baseline_stats, '__class__') and
                self.baseline_stats.__class__.__name__ == 'BuildStats'):
            raise TypeError(
                f"baseline_stats must be BuildStats, got {type(self.baseline_stats)}"
            )

        if not (hasattr(self.optimized_stats, '__class__') and
                self.optimized_stats.__class__.__name__ == 'BuildStats'):
            raise TypeError(
                f"optimized_stats must be BuildStats, got {type(self.optimized_stats)}"
            )

        # Validate numeric ranges
        if self.unallocated_used < 0:
            raise ValueError(
                f"unallocated_used must be >= 0, got {self.unallocated_used}"
            )

        if self.respec_used < 0:
            raise ValueError(f"respec_used must be >= 0, got {self.respec_used}")

        if self.iterations_run < 0:
            raise ValueError(f"iterations_run must be >= 0, got {self.iterations_run}")

        if self.time_elapsed_seconds < 0:
            raise ValueError(
                f"time_elapsed_seconds must be >= 0, got {self.time_elapsed_seconds}"
            )

        if self.nodes_swapped < 0:
            raise ValueError(f"nodes_swapped must be >= 0, got {self.nodes_swapped}")

    def to_dict(self) -> dict:
        """
        Convert OptimizationResult to dictionary for serialization.

        Returns:
            Dictionary with all result fields in JSON-serializable format

        Example:
            >>> result.to_dict()
            {
                'improvement_pct': 15.3,
                'baseline_stats': {...},
                'optimized_stats': {...},
                'budget_usage': {'unallocated': 10, 'respec': 5},
                'convergence': {'reason': 'converged', 'iterations': 45, 'time': 18.5},
                'node_changes': {'added': [1234, 5678], 'removed': [9012], 'swapped': 1}
            }
        """
        return {
            'improvement_pct': self.improvement_pct,
            'baseline_stats': self.baseline_stats.to_dict(),
            'optimized_stats': self.optimized_stats.to_dict(),
            'budget_usage': {
                'unallocated_used': self.unallocated_used,
                'respec_used': self.respec_used
            },
            'convergence': {
                'reason': self.convergence_reason,
                'iterations_run': self.iterations_run,
                'time_elapsed_seconds': self.time_elapsed_seconds
            },
            'node_changes': {
                'added': sorted(list(self.nodes_added)),
                'removed': sorted(list(self.nodes_removed)),
                'swapped': self.nodes_swapped
            }
        }
