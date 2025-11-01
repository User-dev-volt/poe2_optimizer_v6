"""
PoB Calculation Engine - LuaJIT Integration via Lupa

This module encapsulates the Path of Building (PoB) calculation engine using
Lupa Python-LuaJIT bindings. It provides a clean Python API for executing
PoB's Lua-based build calculations.

Architecture (Updated 2025-10-17):
    MinimalCalc.lua custom bootstrap replaces HeadlessWrapper.lua (which had
    GUI dependencies). Loads only calculation modules without GUI: Common.lua,
    Data/Global.lua, Data/Misc.lua, and Modules/Calcs.lua.

Thread Safety:
    Lua state is NOT thread-safe. This module uses thread-local storage pattern
    (implemented in Stories 1.4-1.5) to ensure one LuaRuntime instance per thread.

Performance:
    - First call: ~200ms (Lua function compilation overhead)
    - Subsequent calls: <1ms (after JIT compilation)
    - Target: 1000 calculations in <1 second (Story 1.8 optimization)

Implementation History:
    - Story 1.2: Established Lupa/LuaJIT integration foundation
    - Story 1.3: Python stub functions registered in Lua globals
    - Story 1.4: MinimalCalc.lua loads calculation engine without GUI
    - Story 1.5: Execute BuildData → BuildStats calculation (pending)

References:
    - Tech Spec Epic 1: Lines 876-885 (Story 1.2 Acceptance Criteria)
    - Tech Spec Epic 1: Lines 354-386 (Calculator Module API)
    - Solution Architecture: Lines 714-741 (Calculator Component Architecture)
    - story-1.4-breakthrough-summary.md (MinimalCalc.lua architecture)
"""

import os
import logging
from typing import Optional
from lupa.luajit21 import LuaRuntime
import lupa

from .exceptions import CalculationError, CalculationTimeout
from .passive_tree import get_passive_tree

logger = logging.getLogger(__name__)


class PoBCalculationEngine:
    """
    Path of Building calculation engine wrapper using LuaJIT via Lupa.

    This class encapsulates the Lupa LuaRuntime and provides a Python API
    for executing PoB's Lua calculation modules.

    Thread-Local Pattern (Story 1.4+):
        One instance per thread for session isolation. Use get_pob_engine()
        factory function to retrieve thread-local instance.

    Implementation Stages:
        - Story 1.2: Placeholder class with basic LuaRuntime initialization
        - Story 1.3: Add Python stub functions to Lua global namespace
        - Story 1.4: Load HeadlessWrapper.lua and PoB modules via Lupa
        - Story 1.5: Implement calculate(build: BuildData) -> BuildStats

    Example (Story 1.5+):
        >>> from calculator import PoBCalculationEngine
        >>> from models.build_data import BuildData
        >>>
        >>> engine = PoBCalculationEngine()
        >>> stats = engine.calculate(build_data)
        >>> print(stats.total_dps)

    References:
        - Tech Spec Epic 1: Lines 354-386 (API specification)
        - Solution Architecture: Lines 714-741 (Architecture patterns)
    """

    def __init__(self) -> None:
        """
        Initialize PoB calculation engine with LuaJIT runtime.

        Story 1.2: Basic initialization only (verifies Lupa works).
        Story 1.3: Will add Python stub functions to Lua globals.
        Story 1.4: Will load HeadlessWrapper.lua and PoB modules.
        Story 1.8 Task 2: Pre-compile Lua functions (store Calculate reference).

        Raises:
            RuntimeError: If LuaJIT runtime initialization fails.
        """
        self._lua: Optional[LuaRuntime] = None
        self._initialized = False
        self._passive_node_count: Optional[int] = None
        self._lua_calculate_func = None  # Story 1.8 Task 2: Pre-compiled Calculate function
        self._tree_data_lua = None  # Story 1.8 Task 3: Pre-converted passive tree Lua table

    def _ensure_initialized(self) -> None:
        """
        Lazy initialization of LuaJIT runtime.

        Story 1.2: Creates LuaRuntime instance only.
        Story 1.3: Injects Python stub functions into Lua global namespace.
        Story 1.4+: Will also load PoB Lua modules.

        Stub functions registered:
            - Deflate(data) -> bytes: Compress data using zlib
            - Inflate(data) -> bytes: Decompress zlib data
            - ConPrintf(*args) -> None: Log debug messages
            - ConPrintTable(table) -> None: Log Lua table structures
            - SpawnProcess(*args) -> None: No-op (security)
            - OpenURL(url) -> None: No-op (security)
        """
        if not self._initialized:
            try:
                # Initialize LuaJIT 2.1 runtime via Lupa
                self._lua = LuaRuntime()

                # Story 1.3: Register Python stub functions in Lua global namespace
                # This enables HeadlessWrapper.lua to call Python implementations
                # of PoB's external dependencies (Story 1.4+)
                from .stub_functions import (
                    Deflate,
                    Inflate,
                    ConPrintf,
                    ConPrintTable,
                    SpawnProcess,
                    OpenURL,
                )

                lua_globals = self._lua.globals()
                lua_globals.Deflate = Deflate
                lua_globals.Inflate = Inflate
                lua_globals.ConPrintf = ConPrintf
                lua_globals.ConPrintTable = ConPrintTable
                lua_globals.SpawnProcess = SpawnProcess
                lua_globals.OpenURL = OpenURL

                # Story 1.4: Configure Lua package path and load PoB modules
                self._configure_lua_package_path()
                logger.debug("Configured Lua package.path for PoB modules")

                self._load_headless_wrapper()
                logger.info("MinimalCalc.lua loaded successfully")

                # MinimalCalc.lua handles all module loading internally
                # No need to call _load_pob_data_modules() or _initialize_pob_context()
                # Those methods were designed for HeadlessWrapper.lua approach

                # Story 1.8 Task 2: Pre-compile Lua functions
                # Cache Calculate function reference to avoid globals lookup on each call
                self._lua_calculate_func = self._lua.globals().Calculate
                if not self._lua_calculate_func:
                    raise RuntimeError(
                        "MinimalCalc.lua Calculate() function not found after loading. "
                        "MinimalCalc.lua may have failed to expose Calculate()."
                    )
                logger.debug("Pre-compiled Calculate() function cached")

                # Story 1.8 Task 3: Pre-convert passive tree to Python dict (CRITICAL optimization)
                # Profiling showed to_lua_table() takes 69.5% of runtime (11.39ms per call)
                # Cache the Python dict (not Lua table) to avoid mutation issues
                # Convert to fresh Lua table on each calculate() call
                logger.debug("Pre-converting passive tree data to Python dict...")
                passive_tree = get_passive_tree()
                self._tree_data_lua = passive_tree.to_lua_table()  # Cache Python dict, not Lua table
                logger.info("Passive tree converted to dict and cached (one-time cost)")

                self._passive_node_count = 0  # Placeholder for now
                logger.info("PoB calculation engine initialized")

                self._initialized = True
            except Exception as e:
                raise RuntimeError(f"Failed to initialize LuaJIT runtime: {e}") from e

    def calculate(self, build: 'BuildData') -> 'BuildStats':  # type: ignore
        """
        Calculate build statistics using PoB's Lua engine.

        Story 1.5 Implementation: Full calculation pipeline
            - Task 4: Convert BuildData to Lua table
            - Task 5: Extract results from Lua
            - Task 6: Error handling and timeout

        Args:
            build: BuildData object containing character, tree, items, skills

        Returns:
            BuildStats object containing calculated DPS, life, ES, resistances, etc.

        Raises:
            CalculationError: If Lua calculation fails or invalid input
            CalculationTimeout: If calculation exceeds 5 seconds

        Performance:
            First call: ~200ms (Lua compilation overhead)
            Subsequent calls: <100ms (Story 1.5 target - AC-1.5.4)

        Story 1.5 Scope:
            Supports character class, level, passive nodes. Items and skills
            deferred to Story 1.6 or Epic 2. DPS may be 0 without skills.

        References:
            - Tech Spec Epic 1: Lines 318-353 (Calculator API)
            - Story 1.5 Tasks 4, 5, 6
        """
        import signal
        import time
        from ..models.build_stats import BuildStats

        # Ensure Lua runtime initialized
        self._ensure_initialized()

        # Task 4: Convert BuildData to Lua table
        # Simplified approach: pass structured data directly to Lua
        # (avoiding XML parsing complexity in Lua)
        try:
            # Convert character class enum to string
            character_class_str = build.character_class.value

            # Convert passive nodes set to Lua table
            # Story 1.8 Task 3: Convert to Lua table to avoid Python list access issues
            passive_nodes_python_list = list(build.passive_nodes)
            passive_nodes_list = self._lua.table_from(passive_nodes_python_list)

            logger.debug(
                "Converting BuildData to Lua: class=%s, level=%d, nodes=%d",
                character_class_str,
                build.level,
                len(passive_nodes_python_list)
            )

            # Story 1.8 Task 3: Use pre-converted passive tree dict (cached at init)
            # This was the PRIMARY bottleneck - 69.5% of runtime (11.39ms per call)
            # Cache dict, convert to FRESH Lua table each time (avoids mutation issues)
            # Expected savings: ~11.4 seconds for batch 1000 calculations

            # Construct Lua table for buildData parameter
            # MinimalCalc.lua Calculate() expects:
            #   - characterClass: string
            #   - level: number
            #   - passiveNodes: table/array of node IDs
            #   - treeData: PassiveTree structure from Story 1.7 (REQUIRED for calcs.initEnv)
            # Recursively convert nested config dict to Lua tables
            def dict_to_lua_table(d):
                if not isinstance(d, dict):
                    return d
                lua_tbl = self._lua.table()
                for k, v in d.items():
                    if isinstance(v, dict):
                        lua_tbl[k] = dict_to_lua_table(v)
                    elif isinstance(v, list):
                        lua_tbl[k] = [dict_to_lua_table(item) if isinstance(item, dict) else item for item in v]
                    else:
                        lua_tbl[k] = v
                return lua_tbl

            # Story 1.8 Task 3: Convert cached dict to fresh Lua table (avoids mutation)
            # Use dict_to_lua_table() for recursive conversion (handles nested node dicts)
            tree_data_lua_table = dict_to_lua_table(self._tree_data_lua)

            lua_build_data = self._lua.table(
                characterClass=character_class_str,
                level=build.level,
                passiveNodes=passive_nodes_list,
                treeData=tree_data_lua_table,  # Story 1.8 Task 3: Fresh Lua table from cached dict
                config=dict_to_lua_table(build.config)  # Enemy/calculation configuration from PoB
            )

            # Task 6: Implement 5-second timeout
            # Note: signal.alarm() only works on Unix. For cross-platform,
            # we'll use a simple time-based check with a fallback.
            start_time = time.time()
            timeout_seconds = 5.0

            # Call MinimalCalc.lua Calculate() function
            logger.debug("Calling MinimalCalc.lua Calculate() function")

            # Story 1.8 Task 2: Use pre-compiled Calculate function (cached during init)
            # Avoids globals lookup overhead on each calculation
            # Execute calculation with timeout check
            # (Actual timeout enforcement would require threading or async,
            # but for MVP we'll just check elapsed time after)
            try:
                lua_results = self._lua_calculate_func(lua_build_data)
            except lupa.LuaError as e:
                # Task 6: Wrap Lua errors in CalculationError
                logger.error("Lua calculation error: %s", e)
                raise CalculationError(
                    f"PoB calculation engine failed: {str(e)}"
                ) from e

            # Check if timeout exceeded
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                logger.warning(
                    "Calculation exceeded timeout: %.2fs > %.2fs",
                    elapsed_time,
                    timeout_seconds
                )
                raise CalculationTimeout(
                    f"Calculation exceeded {timeout_seconds}s timeout "
                    f"(took {elapsed_time:.2f}s)"
                )

            logger.debug("Calculation completed in %.3fs", elapsed_time)

            # Task 5: Extract results from Lua table and construct BuildStats
            if not lua_results:
                raise CalculationError("MinimalCalc.lua returned nil/empty results")

            # Helper to safely extract numeric values from Lua table
            def get_lua_num(table, key, default=0):
                """Safely extract number from Lua table, return default if missing/nil"""
                try:
                    value = table[key]
                    if value is None:
                        return default
                    # Lupa converts Lua numbers to Python float/int automatically
                    return float(value) if isinstance(value, (int, float)) else default
                except (KeyError, TypeError):
                    return default

            # Extract core stats
            total_dps = get_lua_num(lua_results, 'TotalDPS', 0.0)
            life = int(get_lua_num(lua_results, 'Life', 0))
            energy_shield = int(get_lua_num(lua_results, 'EnergyShield', 0))
            mana = int(get_lua_num(lua_results, 'Mana', 0))
            ehp = get_lua_num(lua_results, 'EHP', float(life))  # Fallback to life

            # Extract resistances
            resistances = {
                'fire': int(get_lua_num(lua_results, 'FireResist', 0)),
                'cold': int(get_lua_num(lua_results, 'ColdResist', 0)),
                'lightning': int(get_lua_num(lua_results, 'LightningResist', 0)),
                'chaos': int(get_lua_num(lua_results, 'ChaosResist', 0))
            }

            # Extract optional defense stats
            armour = int(get_lua_num(lua_results, 'Armour', 0))
            evasion = int(get_lua_num(lua_results, 'Evasion', 0))
            block_chance = get_lua_num(lua_results, 'BlockChance', 0.0)
            spell_block_chance = get_lua_num(lua_results, 'SpellBlockChance', 0.0)
            movement_speed = get_lua_num(lua_results, 'MovementSpeed', 0.0)

            # Construct BuildStats object
            # This validates numeric types and checks for NaN/infinity
            stats = BuildStats(
                total_dps=total_dps,
                effective_hp=ehp,
                life=life,
                energy_shield=energy_shield,
                mana=mana,
                resistances=resistances,
                armour=armour,
                evasion=evasion,
                block_chance=block_chance,
                spell_block_chance=spell_block_chance,
                movement_speed=movement_speed
            )

            # Log warning if suspicious values detected
            if life == 0 and energy_shield == 0:
                logger.warning(
                    "Build has 0 life and 0 ES - calculation may have failed. "
                    "Check MinimalCalc.lua output for errors."
                )

            if total_dps == 0:
                logger.info(
                    "Build has 0 DPS (expected if no skills configured). "
                    "Story 1.5 scope: passive tree only, items/skills deferred."
                )

            return stats

        except CalculationError:
            # Re-raise CalculationError as-is
            raise
        except CalculationTimeout:
            # Re-raise CalculationTimeout as-is
            raise
        except Exception as e:
            # Wrap unexpected errors
            logger.error("Unexpected error in calculate(): %s", e, exc_info=True)
            raise CalculationError(
                f"Unexpected calculation error: {str(e)}"
            ) from e

    def _configure_lua_package_path(self) -> None:
        """
        Configure Lua package.path to find PoB modules.

        Story 1.4 Task 2: Sets lua_globals.package.path with paths to
        external/pob-engine/ directories. Must be called BEFORE loading
        HeadlessWrapper.lua to ensure Lua can locate required modules.

        Path structure:
            - {pob_engine_dir}/?.lua (root level)
            - {pob_engine_dir}/src/?.lua (source files)
            - {pob_engine_dir}/src/Data/?.lua (data files)
            - {pob_engine_dir}/src/Modules/?.lua (calculation modules)
            - {pob_engine_dir}/src/Classes/?.lua (PoB class files)
            - {pob_engine_dir}/runtime/lua/?.lua (xml parser and runtime)

        Rationale:
            Lua's require() searches package.path for modules. Without this
            configuration, PoB modules fail with "module not found" errors.

        References:
            - Tech Spec Epic 1: Lines 479-509 (Workflow 3: Load Passive Tree Graph)
            - Story Context: constraint id="lua-package-path"
        """
        pob_engine_dir = os.path.abspath("external/pob-engine")
        # Replace backslashes with forward slashes for Lua compatibility on Windows
        pob_engine_dir = pob_engine_dir.replace('\\', '/')
        lua_globals = self._lua.globals()

        # Prepend PoB paths to Lua's package.path
        # runtime/lua path added for xml module required by Launch.lua
        lua_globals.package.path = (
            f"{pob_engine_dir}/?.lua;"
            f"{pob_engine_dir}/src/?.lua;"
            f"{pob_engine_dir}/src/Data/?.lua;"
            f"{pob_engine_dir}/src/Modules/?.lua;"
            f"{pob_engine_dir}/src/Classes/?.lua;"
            f"{pob_engine_dir}/runtime/lua/?.lua;"
            + lua_globals.package.path
        )

    def _load_headless_wrapper(self) -> None:
        """
        Load MinimalCalc.lua - our minimal PoB calculation bootstrap.

        Story 1.4 Review Fix: HeadlessWrapper.lua is designed for the full PoB
        GUI application with C++ bindings and causes fatal exceptions in headless
        environments. Instead, we created MinimalCalc.lua which loads only the
        calculation modules we need without GUI dependencies.

        File location:
            src/calculator/MinimalCalc.lua (our custom bootstrap)

        Approach:
            - MinimalCalc.lua defines LoadModule() and PLoadModule() functions
            - Loads Common.lua, Data.lua, and Calcs.lua directly
            - Exposes a Calculate() function to Python
            - Avoids Launch.lua, Main.lua, and all GUI-related modules

        Error handling:
            - FileNotFoundError: If MinimalCalc.lua missing
            - CalculationError: If Lua errors during module loading

        References:
            - Tech Spec Epic 1: Lines 356-386 (Calculator Module API)
            - Story 1.4 Review: [H1] Abandon HeadlessWrapper.lua approach
        """
        minimal_calc_path = os.path.join("src", "calculator", "MinimalCalc.lua")

        if not os.path.exists(minimal_calc_path):
            raise FileNotFoundError(
                f"MinimalCalc.lua not found at {minimal_calc_path}. "
                "This is our custom PoB calculation bootstrap."
            )

        try:
            # Set working directory to PoB engine src for module loading
            pob_engine_dir = os.path.abspath("external/pob-engine")
            pob_src_dir = os.path.join(pob_engine_dir, "src")
            pob_src_dir = pob_src_dir.replace('\\', '/')

            # Tell Lua where to find PoB modules
            # Include Modules directory pattern so MinimalCalc.lua can detect pob_src_dir
            self._lua.execute(f'''
                package.path = "{pob_src_dir}/Modules/?.lua;" .. "{pob_src_dir}/?.lua;" .. package.path
            ''')

            # Load our minimal bootstrap
            minimal_calc_path = minimal_calc_path.replace('\\', '/')
            logger.debug(f"Loading minimal PoB bootstrap from {minimal_calc_path}")
            self._lua.execute(f'dofile("{minimal_calc_path}")')
            logger.info("MinimalCalc.lua loaded - PoB calculation modules initialized")

        except lupa.LuaError as e:
            raise CalculationError(
                f"Failed to load MinimalCalc.lua: {e}. "
                "Check that PoB engine modules are accessible."
            ) from e

    # Note: _load_pob_data_modules() and _initialize_pob_context() methods removed
    # Architecture Update (2025-10-17): MinimalCalc.lua handles all module loading internally
    # Old methods were designed for HeadlessWrapper.lua approach which was abandoned

    def collect_garbage(self) -> None:
        """
        Explicitly trigger Lua garbage collection.

        Story 1.8 Task 4: Call after batch operations to free Lua memory.
        Recommended after processing 100-1000+ calculations.

        Performance:
            - GC typically takes <1ms
            - Reduces memory footprint by releasing unused Lua objects

        References:
            - Tech Spec Epic 1: Lines 553-557 (Memory Management)
            - Story 1.8 AC-1.8.5 (No memory leaks)
        """
        if self._lua is not None:
            logger.debug("Triggering Lua garbage collection")
            self._lua.execute("collectgarbage('collect')")

    def cleanup(self) -> None:
        """
        Clean up Lua runtime resources.

        Releases LuaRuntime instance and clears state.
        Called when thread-local engine is no longer needed.

        Story 1.8 Task 4: Added explicit Lua GC before cleanup.
        """
        if self._lua is not None:
            # Story 1.8 Task 4: Explicit Lua garbage collection before cleanup
            logger.debug("Cleaning up Lua runtime (with GC)")
            try:
                self._lua.execute("collectgarbage('collect')")
            except Exception as e:
                logger.warning(f"Failed to run Lua GC during cleanup: {e}")

            self._lua = None
            self._initialized = False
