"""
Full PoB Calculation Engine - HeadlessWrapper.lua Integration

Story 2.9: This module integrates the full Path of Building calculation engine
using HeadlessWrapper.lua, enabling accurate DPS/Life/EHP calculations that
reflect passive tree allocations, items, and skills.

Architecture:
    - Uses HeadlessWrapper.lua from PoB (external/pob-engine/src/)
    - Changes working directory during initialization to load PoB modules
    - Provides loadBuildFromXML() API for loading complete builds
    - Extracts stats from build.calcsTab.mainOutput

Thread Safety:
    Lua state is NOT thread-safe. Use thread-local storage pattern
    (one engine instance per thread) for concurrent calculations.

Performance:
    - Initialization: ~2-5 seconds (full PoB module loading)
    - Single calculation: <500ms (AC-2.9.4)
    - Batch 100 calculations: <60 seconds (AC-2.9.4)

References:
    - Story 2.9: Integrate Full PoB Calculation Engine
    - HeadlessWrapper.lua: external/pob-engine/src/HeadlessWrapper.lua
"""

import os
import logging
from typing import Optional
from contextlib import contextmanager
from lupa.luajit21 import LuaRuntime
import lupa

from .exceptions import CalculationError, CalculationTimeout
from ..models.build_stats import BuildStats

logger = logging.getLogger(__name__)


@contextmanager
def working_directory(path):
    """Context manager for temporarily changing working directory."""
    original_dir = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(original_dir)


class FullPoBEngine:
    """
    Full Path of Building calculation engine using HeadlessWrapper.lua.

    This class loads the complete PoB application via HeadlessWrapper.lua,
    enabling calculations with items, skills, and passive tree.

    Unlike PoBCalculationEngine (which uses MinimalCalc.lua), this engine:
    - Loads the full PoB application
    - Supports items and skills
    - Uses loadBuildFromXML() to load builds from PoB XML
    - Returns accurate DPS based on actual skill configurations

    Usage:
        >>> engine = FullPoBEngine()
        >>> xml_string = open("build.xml").read()
        >>> stats = engine.calculate_from_xml(xml_string)
        >>> print(f"DPS: {stats.total_dps}")
    """

    def __init__(self) -> None:
        """Initialize Full PoB engine."""
        self._lua: Optional[LuaRuntime] = None
        self._initialized = False
        self._pob_src_dir: Optional[str] = None

    def _ensure_initialized(self) -> None:
        """
        Initialize LuaJIT runtime and load HeadlessWrapper.lua.

        This method:
        1. Creates LuaRuntime instance
        2. Registers Python stub functions (Deflate, Inflate, etc.)
        3. Changes working directory to PoB src
        4. Loads HeadlessWrapper.lua which initializes full PoB
        """
        if self._initialized:
            return

        try:
            # Initialize LuaJIT 2.1 runtime via Lupa
            self._lua = LuaRuntime()

            # Register Python stub functions in Lua global namespace
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

            # Set up PoB paths
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            self._pob_src_dir = os.path.join(project_root, "external", "pob-engine", "src")
            pob_runtime_dir = os.path.join(project_root, "external", "pob-engine", "runtime", "lua")

            if not os.path.exists(self._pob_src_dir):
                raise RuntimeError(f"PoB source directory not found: {self._pob_src_dir}")

            # Configure Lua package.path
            pob_src_normalized = self._pob_src_dir.replace('\\', '/')
            pob_runtime_normalized = pob_runtime_dir.replace('\\', '/')

            lua_globals.package.path = (
                f"{pob_src_normalized}/?.lua;"
                f"{pob_src_normalized}/Modules/?.lua;"
                f"{pob_src_normalized}/Classes/?.lua;"
                f"{pob_src_normalized}/Data/?.lua;"
                f"{pob_runtime_normalized}/?.lua;"
                f"{pob_runtime_normalized}/?/init.lua;"
                + lua_globals.package.path
            )

            # Pre-load module stubs that HeadlessWrapper/Common.lua expect
            # These modules are C libraries or have complex dependencies
            self._lua.execute('''
                -- Command line args stub (Main.lua line 58 expects this)
                arg = {}

                -- UTF-8 library stub (use LuaJIT's built-in utf8 if available)
                package.loaded["lua-utf8"] = utf8 or {
                    reverse = function(s) return s:reverse() end,
                    gsub = string.gsub,
                    find = string.find,
                    sub = string.sub,
                    len = function(s) return #s end
                }

                -- HTTP library stub (not needed for calculations)
                package.loaded["lcurl.safe"] = {}

                -- Base64 encoding stub (PoB uses this for code import/export)
                package.loaded["base64"] = {
                    encode = function(s) return s end,
                    decode = function(s) return s end
                }

                -- SHA-1 hashing stub
                package.loaded["sha1"] = function(s) return s end
            ''')

            logger.info("Loading HeadlessWrapper.lua from %s", self._pob_src_dir)

            # Change to PoB src directory and load HeadlessWrapper
            with working_directory(self._pob_src_dir):
                headless_path = os.path.join(self._pob_src_dir, "HeadlessWrapper.lua")
                headless_path = headless_path.replace('\\', '/')

                # Load HeadlessWrapper.lua
                self._lua.execute(f'dofile("{headless_path}")')

            # Verify HeadlessWrapper functions are available
            if not lua_globals.loadBuildFromXML:
                raise RuntimeError("HeadlessWrapper.lua did not expose loadBuildFromXML function")

            if not lua_globals.newBuild:
                raise RuntimeError("HeadlessWrapper.lua did not expose newBuild function")

            logger.info("HeadlessWrapper.lua loaded successfully")
            self._initialized = True

        except lupa.LuaError as e:
            raise RuntimeError(f"Failed to load HeadlessWrapper.lua: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Full PoB engine: {e}") from e

    def calculate_from_xml(self, xml_string: str, build_name: str = "Optimizer Build") -> BuildStats:
        """
        Calculate build stats from PoB XML string.

        Args:
            xml_string: Complete PoB build XML (as exported from Path of Building)
            build_name: Optional name for the build

        Returns:
            BuildStats with calculated DPS, life, resistances, etc.

        Raises:
            CalculationError: If calculation fails
        """
        import time

        self._ensure_initialized()

        start_time = time.time()
        timeout_seconds = 5.0

        try:
            lua_globals = self._lua.globals()

            # Change to PoB src directory for calculation
            with working_directory(self._pob_src_dir):
                # Load build from XML
                logger.debug("Loading build from XML (%d chars)", len(xml_string))
                lua_globals.loadBuildFromXML(xml_string, build_name)

                # Get build object
                build = lua_globals.build
                if not build:
                    raise CalculationError("Build object not available after loading XML")

                # Trigger calculation by running a frame
                lua_globals.runCallback("OnFrame")

                # Extract stats from calcsTab.mainOutput
                calcs_tab = build.calcsTab
                if not calcs_tab:
                    raise CalculationError("calcsTab not available")

                main_output = calcs_tab.mainOutput
                if not main_output:
                    raise CalculationError("mainOutput not available - calculation may have failed")

            # Check timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                raise CalculationTimeout(
                    f"Calculation exceeded {timeout_seconds}s timeout (took {elapsed_time:.2f}s)"
                )

            # Extract stats
            stats = self._extract_stats(main_output)

            logger.debug("Calculation completed in %.3fs", elapsed_time)
            return stats

        except CalculationError:
            raise
        except CalculationTimeout:
            raise
        except lupa.LuaError as e:
            raise CalculationError(f"Lua error during calculation: {e}") from e
        except Exception as e:
            raise CalculationError(f"Unexpected calculation error: {e}") from e

    def _extract_stats(self, main_output) -> BuildStats:
        """Extract BuildStats from PoB mainOutput table."""

        def get_num(key: str, default: float = 0.0) -> float:
            """Safely extract number from Lua table."""
            try:
                value = main_output[key]
                if value is None:
                    return default
                return float(value)
            except (KeyError, TypeError, ValueError):
                return default

        # Core stats
        total_dps = get_num("TotalDPS") or get_num("CombinedDPS") or get_num("FullDPS")
        life = int(get_num("Life"))
        energy_shield = int(get_num("EnergyShield"))
        mana = int(get_num("Mana"))

        # EHP calculation
        ehp = get_num("TotalEHP") or get_num("EHP") or float(life)

        # Resistances
        resistances = {
            'fire': int(get_num("FireResist")),
            'cold': int(get_num("ColdResist")),
            'lightning': int(get_num("LightningResist")),
            'chaos': int(get_num("ChaosResist"))
        }

        # Defense stats
        armour = int(get_num("Armour"))
        evasion = int(get_num("Evasion"))
        block_chance = get_num("BlockChance") or get_num("EffectiveBlockChance")
        spell_block = get_num("SpellBlockChance") or get_num("EffectiveSpellBlockChance")
        movement_speed = get_num("MovementSpeed") or get_num("EffectiveMovementSpeedMod")

        return BuildStats(
            total_dps=total_dps,
            effective_hp=ehp,
            life=life,
            energy_shield=energy_shield,
            mana=mana,
            resistances=resistances,
            armour=armour,
            evasion=evasion,
            block_chance=block_chance,
            spell_block_chance=spell_block,
            movement_speed=movement_speed
        )

    def new_build(self) -> None:
        """Create a fresh empty build."""
        self._ensure_initialized()

        lua_globals = self._lua.globals()
        with working_directory(self._pob_src_dir):
            lua_globals.newBuild()

    def load_build(self, xml_string: str, build_name: str = "Optimizer Build") -> None:
        """
        Load a build from XML without calculating stats.

        Use this to set up a build before making modifications.
        Call get_stats() after modifications to get current stats.
        """
        self._ensure_initialized()

        lua_globals = self._lua.globals()
        with working_directory(self._pob_src_dir):
            lua_globals.loadBuildFromXML(xml_string, build_name)

    def get_stats(self) -> BuildStats:
        """
        Get current build stats after modifications.

        Must call load_build() first to set up a build.
        """
        self._ensure_initialized()

        lua_globals = self._lua.globals()
        build = lua_globals.build
        if not build:
            raise CalculationError("Build not loaded")

        # Set build flags to trigger recalculation
        build.buildFlag = True
        build.modFlag = True

        # Trigger recalculation (no working directory change needed after init)
        lua_globals.runCallback("OnFrame")

        if not build.calcsTab or not build.calcsTab.mainOutput:
            raise CalculationError("Calculation failed - mainOutput not available")

        return self._extract_stats(build.calcsTab.mainOutput)

    def get_allocated_nodes(self) -> set:
        """Get set of currently allocated passive node IDs."""
        self._ensure_initialized()

        lua_globals = self._lua.globals()
        build = lua_globals.build
        if not build or not build.spec:
            raise CalculationError("Build not loaded")

        nodes = set()
        alloc_nodes = build.spec.allocNodes
        if alloc_nodes:
            for node_id in alloc_nodes:
                if node_id:
                    nodes.add(int(node_id))
        return nodes

    def allocate_node(self, node_id: int) -> bool:
        """
        Allocate a passive node.

        Returns True if allocation succeeded, False if node invalid or already allocated.
        """
        self._ensure_initialized()

        lua_globals = self._lua.globals()
        build = lua_globals.build
        if not build or not build.spec:
            raise CalculationError("Build not loaded")

        with working_directory(self._pob_src_dir):
            try:
                spec = build.spec

                # Check if already allocated
                if spec.allocNodes[node_id]:
                    return False

                # Get the node from the spec's node list
                node = spec.nodes[node_id]
                if not node:
                    return False

                # Directly allocate the node (simpler approach for optimizer)
                node.alloc = True
                spec.allocNodes[node_id] = node

                # Rebuild paths and dependencies
                spec["BuildAllDependsAndPaths"](spec)

                # Set build flags
                build.buildFlag = True
                build.modFlag = True

                return True
            except Exception as e:
                logger.warning(f"Failed to allocate node {node_id}: {e}")
                return False

    def deallocate_node(self, node_id: int) -> bool:
        """
        Deallocate a passive node.

        Returns True if deallocation succeeded, False if node invalid or not allocated.
        """
        self._ensure_initialized()

        lua_globals = self._lua.globals()
        build = lua_globals.build
        if not build or not build.spec:
            raise CalculationError("Build not loaded")

        with working_directory(self._pob_src_dir):
            try:
                spec = build.spec

                # Check if allocated
                node = spec.allocNodes[node_id]
                if not node:
                    return False

                # Deallocate the node
                node.alloc = False
                spec.allocNodes[node_id] = None

                # Rebuild paths and dependencies
                spec["BuildAllDependsAndPaths"](spec)

                # Set build flags
                build.buildFlag = True
                build.modFlag = True

                return True
            except Exception as e:
                logger.warning(f"Failed to deallocate node {node_id}: {e}")
                return False

    def set_passive_nodes(self, node_ids: set) -> None:
        """
        Set the exact set of allocated passive nodes.

        This deallocates all current nodes and allocates the specified set.
        """
        self._ensure_initialized()

        lua_globals = self._lua.globals()
        build = lua_globals.build
        if not build or not build.spec:
            raise CalculationError("Build not loaded")

        with working_directory(self._pob_src_dir):
            spec = build.spec

            # Get current allocated nodes
            current_nodes = set()
            if spec.allocNodes:
                for nid in spec.allocNodes:
                    if nid:
                        current_nodes.add(int(nid))

            # Deallocate nodes not in target set
            for nid in current_nodes - node_ids:
                self.deallocate_node(nid)

            # Allocate nodes not currently allocated
            for nid in node_ids - current_nodes:
                self.allocate_node(nid)

    def cleanup(self) -> None:
        """Clean up Lua runtime resources."""
        if self._lua is not None:
            try:
                self._lua.execute("collectgarbage('collect')")
            except Exception as e:
                logger.warning(f"Failed to run Lua GC during cleanup: {e}")

            self._lua = None
            self._initialized = False


# Thread-local storage for FullPoBEngine instances
import threading
_full_engine_thread_local = threading.local()


def get_full_pob_engine() -> FullPoBEngine:
    """Get thread-local Full PoB engine instance."""
    if not hasattr(_full_engine_thread_local, 'engine'):
        logger.debug("Creating new FullPoBEngine for thread %s", threading.current_thread().name)
        _full_engine_thread_local.engine = FullPoBEngine()
    return _full_engine_thread_local.engine


def calculate_build_stats_from_xml(xml_string: str, build_name: str = "Optimizer Build") -> BuildStats:
    """
    Calculate build stats from PoB XML using full PoB engine.

    This is the Story 2.9 API that enables full PoB calculations with
    items, skills, and passive tree.

    Args:
        xml_string: Complete PoB build XML
        build_name: Optional name for the build

    Returns:
        BuildStats with accurate DPS, life, resistances based on full build

    Example:
        >>> xml = open("tests/fixtures/realistic_builds/witch_frost_mage_91.xml").read()
        >>> stats = calculate_build_stats_from_xml(xml)
        >>> print(f"Full DPS: {stats.total_dps}")
    """
    engine = get_full_pob_engine()
    return engine.calculate_from_xml(xml_string, build_name)
