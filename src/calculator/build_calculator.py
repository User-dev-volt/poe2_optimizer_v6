"""
High-level API for PoB build calculations.

This module provides the calculate_build_stats() function, the primary
API for the optimization algorithm (Epic 2).

Architecture:
    - Thread-local PoBCalculationEngine instances for session isolation
    - BuildData (input) → BuildStats (output) transformation
    - Lua Calculate() function called via Lupa bindings

Performance:
    - First call per thread: ~200ms (Lua compilation overhead)
    - Subsequent calls: <100ms (Story 1.5 target)
    - Batch 1000 calculations: ~2s (Story 1.8 - approved performance target)

Thread Safety:
    - Uses thread-local storage pattern
    - One LuaRuntime instance per thread
    - Safe for concurrent calculations in Epic 3

Story 1.5 Implementation:
    - Tasks 3, 4, 5: High-level API, data conversion, result extraction
    - Task 6: Error handling and timeout (5 seconds)

References:
    - Tech Spec Epic 1: Lines 318-386 (Calculator Module API)
    - Tech Spec Epic 1: Lines 428-475 (Workflow 2: Calculate Build Stats)
"""

import logging
import threading
from typing import Optional

from ..models.build_data import BuildData
from ..models.build_stats import BuildStats
from .pob_engine import PoBCalculationEngine
from .subprocess_calculator import SubprocessCalculator
from .exceptions import CalculationError, CalculationTimeout

logger = logging.getLogger(__name__)

# Thread-local storage for calculator instances
# Story 2.9.1 Task 6: Hybrid routing with MinimalCalc + SubprocessCalculator
_thread_local = threading.local()


def get_pob_engine() -> PoBCalculationEngine:
    """
    Get thread-local PoB calculation engine instance.

    Uses thread-local storage to ensure one LuaRuntime instance per thread.
    Creates new instance on first call per thread, caches for subsequent calls.

    Returns:
        PoBCalculationEngine instance for current thread

    Thread Safety:
        Each thread gets isolated LuaRuntime instance. Safe for concurrent
        calculations across multiple threads.

    Example:
        >>> engine = get_pob_engine()
        >>> stats = engine.calculate(build_data)

    References:
        - Tech Spec Epic 1: Lines 354-386 (Thread-local pattern)
        - Story 1.5 Task 3: Create calculate_build_stats() High-Level API
    """
    if not hasattr(_thread_local, 'pob_engine'):
        logger.debug("Creating new PoBCalculationEngine for thread %s", threading.current_thread().name)
        _thread_local.pob_engine = PoBCalculationEngine()
    return _thread_local.pob_engine


def get_subprocess_calculator() -> SubprocessCalculator:
    """
    Get thread-local subprocess calculator instance.

    Story 2.9.1 Task 6: Provides fallback calculator for spell/DOT/totem skills.
    Uses thread-local storage pattern same as get_pob_engine().

    Returns:
        SubprocessCalculator instance for current thread

    Thread Safety:
        Each thread gets isolated calculator instance with its own PoB engine.

    References:
        - Story 2.9.1 AC-2.9.1.7: Hybrid routing logic
    """
    if not hasattr(_thread_local, 'subprocess_calculator'):
        logger.debug("Creating new SubprocessCalculator for thread %s", threading.current_thread().name)
        _thread_local.subprocess_calculator = SubprocessCalculator()
    return _thread_local.subprocess_calculator


def calculate_build_stats(build: BuildData) -> BuildStats:
    """
    Calculate character statistics using hybrid routing.

    Story 2.9.1 Phase 2 - Task 6: Hybrid calculation approach.
    Routes builds to optimal calculator based on skill type:
    - Attack skills → MinimalCalc (fast path, ~10ms)
    - Spell/DOT/totem skills → SubprocessCalculator (~50-100ms)

    Args:
        build: BuildData object with character, passive tree, items, skills

    Returns:
        BuildStats object with calculated DPS, EHP, life, resistances, etc.

    Raises:
        CalculationError: If PoB engine fails (Lua error, invalid build)
        CalculationTimeout: If calculation exceeds timeout

    Performance:
        - Attack builds: ~10ms (MinimalCalc fast path)
        - Spell/DOT builds: ~50-100ms (Subprocess fallback)
        - Optimization (200 iters): 20s (attack) or 150s (spell), both <300s target

    Hybrid Routing Logic (AC-2.9.1.7):
        1. Detect skill type using is_attack_skill()
        2. Attack → MinimalCalc (engine.calculate)
        3. Spell/DOT/totem → SubprocessCalculator
        4. Fallback: MinimalCalc error → retry with Subprocess

    Example:
        >>> # Attack build (fast path)
        >>> build_attack = BuildData(...)
        >>> stats = calculate_build_stats(build_attack)  # Uses MinimalCalc
        >>>
        >>> # Spell build (subprocess path)
        >>> build_spell = BuildData(...)
        >>> stats = calculate_build_stats(build_spell)  # Uses SubprocessCalculator

    References:
        - Story 2.9.1 AC-2.9.1.7: Hybrid routing logic
        - Story 2.9.1 AC-2.9.1.10: Performance validation
    """
    logger.debug(
        "Calculating stats for build: %s level %d, %d passive nodes",
        build.character_class.value,
        build.level,
        len(build.passive_nodes)
    )

    # Get thread-local calculator instances
    engine = get_pob_engine()
    subprocess_calc = get_subprocess_calculator()

    # Determine calculation path based on skill type
    # Story 2.9.1 Task 6.2: Routing logic
    use_minimalcalc = False

    if build.skills:
        # Check if primary active skill is attack-based
        active_skill = next((s for s in build.skills if s.enabled), None)

        if active_skill:
            use_minimalcalc = engine.is_attack_skill(active_skill)
            path_name = "MinimalCalc (attack)" if use_minimalcalc else "Subprocess (spell/DOT/totem)"
            logger.info(
                f"Routing '{active_skill.name}' to {path_name}"
            )
        else:
            # No active skill, use MinimalCalc (will calculate defenses only)
            use_minimalcalc = True
            logger.debug("No active skill found, using MinimalCalc for defense calculation")
    else:
        # No skills at all, use MinimalCalc
        use_minimalcalc = True
        logger.debug("No skills configured, using MinimalCalc")

    try:
        if use_minimalcalc:
            # Fast path: Attack skills with MinimalCalc
            # Story 2.9.1 Task 6.2: Attack → MinimalCalc
            logger.debug("Using MinimalCalc (fast path)")
            stats = engine.calculate(build)
        else:
            # Subprocess path: Spell/DOT/totem skills
            # Story 2.9.1 Task 6.2: Spell/DOT/totem → Subprocess
            logger.debug("Using SubprocessCalculator (spell/DOT/totem path)")
            stats = subprocess_calc.calculate(build)

        logger.debug(
            "Calculation successful: DPS=%.1f, Life=%d, EHP=%.1f",
            stats.total_dps,
            stats.life,
            stats.effective_hp
        )

        return stats

    except CalculationError as e:
        # Story 2.9.1 Task 6.3: Fallback mechanism
        # If MinimalCalc fails and we haven't tried subprocess yet, retry
        if use_minimalcalc:
            logger.warning(
                "MinimalCalc failed: %s. Retrying with SubprocessCalculator...", e
            )
            try:
                stats = subprocess_calc.calculate(build)
                logger.info(
                    "Fallback successful: DPS=%.1f (subprocess path)",
                    stats.total_dps
                )
                return stats
            except Exception as fallback_error:
                logger.error(
                    "Subprocess fallback also failed: %s", fallback_error
                )
                raise CalculationError(
                    f"Both MinimalCalc and Subprocess failed. "
                    f"MinimalCalc: {e}, Subprocess: {fallback_error}"
                ) from fallback_error
        else:
            # Subprocess already failed, no fallback available
            logger.error("SubprocessCalculator failed: %s", e)
            raise

    except CalculationTimeout as e:
        logger.error("Calculation timeout: %s", e)
        raise

    except Exception as e:
        # Wrap unexpected errors in CalculationError
        logger.error("Unexpected error during calculation: %s", e, exc_info=True)
        raise CalculationError(f"Unexpected calculation error: {e}") from e
