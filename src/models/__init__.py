"""
Data models for build representation

Provides data structures for:
    - Build configuration (BuildData): Input to calculation engine
    - Calculated statistics (BuildStats): Output from calculation engine
    - Optimization configuration (OptimizationConfiguration): Input to optimizer
    - Optimization results (OptimizationResult): Output from optimizer
    - Character classes, items, skills

Story 1.5 Implementation:
    - BuildStats dataclass added for calculation results

Story 2.1 Implementation:
    - OptimizationConfiguration and OptimizationResult added for optimizer

Usage:
    from models import BuildData, BuildStats, CharacterClass

    # Create build
    build = BuildData(
        character_class=CharacterClass.WITCH,
        level=90,
        passive_nodes={12345, 12346}
    )

    # Calculate stats (via calculator module)
    from calculator import calculate_build_stats
    stats = calculate_build_stats(build)

    # Optimize build (via optimizer module)
    from optimizer import optimize_build
    from models import OptimizationConfiguration
    config = OptimizationConfiguration(
        build=build,
        metric="dps",
        unallocated_points=15
    )
    result = optimize_build(config)

    # Access results
    print(f"DPS: {stats.total_dps}, Life: {stats.life}")
    print(f"Improvement: {result.improvement_pct}%")
"""

__version__ = "0.3.0"
__all__ = [
    "BuildData",
    "BuildStats",
    "CharacterClass",
    "Item",
    "Skill",
    "OptimizationConfiguration",
    "OptimizationResult",
]

from .build_data import BuildData, CharacterClass, Item, Skill
from .build_stats import BuildStats
from .optimization_config import OptimizationConfiguration, OptimizationResult
