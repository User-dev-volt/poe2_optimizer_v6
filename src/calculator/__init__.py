"""
Calculator Module - Python-Lua Bridge for PoB Calculations

This module provides the integration layer between Python and Path of Building's
Lua calculation engine via Lupa/LuaJIT bindings.

Architecture:
    - Position: Integration layer between parsers/ (data) and optimizer/ (business logic)
    - Dependencies: parsers/ module (receives BuildData objects)
    - Provides API to: optimizer/ module (future Epic 2)

Implementation Status (Epic 1):
    - Story 1.2: Lupa/LuaJIT integration foundation ✓
    - Story 1.3: Python stub functions (Deflate, Inflate, ConPrintf, etc.) ✓
    - Story 1.4: Load MinimalCalc.lua and PoB modules ✓
    - Story 1.5: Execute BuildData → BuildStats calculations ✓
    - Story 1.7: PassiveTreeGraph data model and loader ✓

Usage:
    # Recommended high-level API (Story 1.5+)
    from calculator import calculate_build_stats
    stats = calculate_build_stats(build_data)

    # Or low-level engine API
    from calculator.pob_engine import PoBCalculationEngine
    engine = PoBCalculationEngine()
    stats = engine.calculate(build_data)

References:
    - Tech Spec Epic 1: Lines 354-386 (Calculator Module API)
    - Solution Architecture: Lines 714-741 (Calculator Component Architecture)
    - PRD: Lines 334-394 (FR-3.x PoB Calculation Engine Integration)
"""

__version__ = "0.3.0"
__all__ = [
    "PoBCalculationEngine",
    "calculate_build_stats",
    "get_pob_engine",
    "CalculationError",
    "CalculationTimeout",
    "Deflate",
    "Inflate",
    "ConPrintf",
    "ConPrintTable",
    "SpawnProcess",
    "OpenURL",
    # Story 1.7: Passive Tree
    "PassiveNode",
    "PassiveTreeGraph",
    "load_passive_tree",
    "get_passive_tree",
    "clear_passive_tree_cache",
]

# Story 1.7: Passive Tree Graph (import first - no dependencies)
from .passive_tree import (
    PassiveNode,
    PassiveTreeGraph,
    load_passive_tree,
    get_passive_tree,
    clear_passive_tree_cache,
)

# Import other modules with graceful failure handling
try:
    from .pob_engine import PoBCalculationEngine
    from .build_calculator import calculate_build_stats, get_pob_engine
    from .exceptions import CalculationError, CalculationTimeout
    from .stub_functions import (
        Deflate,
        Inflate,
        ConPrintf,
        ConPrintTable,
        SpawnProcess,
        OpenURL,
    )
except ImportError as e:
    # If other modules fail to import, passive_tree can still be used
    import warnings
    warnings.warn(f"Some calculator modules failed to import: {e}", ImportWarning)
