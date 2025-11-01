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
from .exceptions import CalculationError, CalculationTimeout

logger = logging.getLogger(__name__)

# Thread-local storage for PoBCalculationEngine instances
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


def calculate_build_stats(build: BuildData) -> BuildStats:
    """
    Calculate character statistics using PoB engine.

    This is the primary API for the optimization algorithm. Converts BuildData
    to Lua-compatible format, executes PoB calculation engine via MinimalCalc.lua,
    and returns BuildStats with DPS, life, resistances, etc.

    Args:
        build: BuildData object with character, passive tree, items, skills

    Returns:
        BuildStats object with calculated DPS, EHP, life, resistances, etc.

    Raises:
        CalculationError: If PoB engine fails (Lua error, invalid build)
        CalculationTimeout: If calculation exceeds 5 seconds

    Performance:
        - Target: <100ms per calculation (AC-1.5.4)
        - First call per thread may take ~200ms (Lua compilation)

    Example:
        >>> from models import BuildData, CharacterClass
        >>> build = BuildData(
        ...     character_class=CharacterClass.WITCH,
        ...     level=90,
        ...     passive_nodes={12345, 12346}
        ... )
        >>> stats = calculate_build_stats(build)
        >>> print(f"DPS: {stats.total_dps}, Life: {stats.life}")

    Story 1.5 Scope:
        - Supports character class, level, passive nodes
        - Items and skills deferred to Story 1.6 or Epic 2
        - Returns basic stats (DPS may be 0 without skills)

    References:
        - Tech Spec Epic 1: Lines 318-353 (Calculator API)
        - Tech Spec Epic 1: Lines 428-475 (Workflow 2: Calculate Build Stats)
        - Story 1.5 AC-1.5.1 through AC-1.5.6
    """
    logger.debug(
        "Calculating stats for build: %s level %d, %d passive nodes",
        build.character_class.value,
        build.level,
        len(build.passive_nodes)
    )

    # Get thread-local engine instance
    engine = get_pob_engine()

    try:
        # Call engine.calculate() which handles:
        # - BuildData to Lua table conversion
        # - MinimalCalc.lua Calculate() invocation
        # - Result extraction and BuildStats construction
        # - Timeout handling (5 seconds)
        stats = engine.calculate(build)

        logger.debug(
            "Calculation successful: DPS=%.1f, Life=%d, EHP=%.1f",
            stats.total_dps,
            stats.life,
            stats.effective_hp
        )

        return stats

    except CalculationTimeout as e:
        logger.error("Calculation timeout: %s", e)
        raise

    except CalculationError as e:
        logger.error("Calculation failed: %s", e)
        raise

    except Exception as e:
        # Wrap unexpected errors in CalculationError
        logger.error("Unexpected error during calculation: %s", e, exc_info=True)
        raise CalculationError(f"Unexpected calculation error: {e}") from e
