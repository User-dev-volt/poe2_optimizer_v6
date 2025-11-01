"""
Integration Tests for PoB Stub Functions (Lupa Integration)

Tests stub functions integrated with Lupa/Lua runtime. These tests verify
that Python stub functions can be called from Lua code and behave correctly
in the Lua-Python boundary.

These tests are SLOWER than unit tests (require Lupa initialization) and
are marked with @pytest.mark.slow for optional execution during development.

Test Coverage:
    - AC-1.3.5: All stubs accessible from Lua global namespace
    - AC-1.3.6: No errors when calling stubs from Lua
    - Round-trip Python → Lua → Python for all stub functions

Story Context:
    Story 1.3 integrates stubs with Lupa. Story 1.4 will load HeadlessWrapper.lua
    which will use these stubs. These tests verify the integration foundation.

References:
    - Story 1.3: Lines 112-151 (Task 3: Integrate with Lupa Runtime)
    - Story 1.3: Lines 152-165 (Task 4: Test with Simulated HeadlessWrapper)
    - Tech Spec Epic 1: Lines 888-898 (Story 1.3 Acceptance Criteria)
"""

import logging
import pytest

# Lupa imports
try:
    from lupa.luajit21 import LuaRuntime
    LUPA_AVAILABLE = True
except ImportError:
    LUPA_AVAILABLE = False

from src.calculator.stub_functions import (
    Deflate,
    Inflate,
    ConPrintf,
    ConPrintTable,
    SpawnProcess,
    OpenURL,
)


# Skip all tests in this file if Lupa not available
pytestmark = [
    pytest.mark.skipif(not LUPA_AVAILABLE, reason="Lupa not installed"),
    pytest.mark.slow,  # Integration tests are slower
]


# ============================================================================
# AC-1.3.5: Stubs Accessible from Lua Global Namespace
# ============================================================================

class TestLuaGlobalRegistration:
    """Test stub function registration in Lua global namespace."""

    def test_register_stubs_in_lua_globals(self):
        """
        Verify Python stubs can be registered in Lua globals (AC-1.3.5).

        This is the core integration pattern used in pob_engine.py:
        lua.globals().FunctionName = python_function
        """
        lua = LuaRuntime(encoding='latin-1')  # Binary-safe encoding for Deflate/Inflate
        lua_globals = lua.globals()

        # Register all stub functions in Lua global namespace
        lua_globals.Deflate = Deflate
        lua_globals.Inflate = Inflate
        lua_globals.ConPrintf = ConPrintf
        lua_globals.ConPrintTable = ConPrintTable
        lua_globals.SpawnProcess = SpawnProcess
        lua_globals.OpenURL = OpenURL

        # Verify functions are accessible from Lua
        assert lua_globals.Deflate is not None
        assert lua_globals.Inflate is not None
        assert lua_globals.ConPrintf is not None
        assert lua_globals.ConPrintTable is not None
        assert lua_globals.SpawnProcess is not None
        assert lua_globals.OpenURL is not None

    def test_lua_can_call_deflate(self):
        """
        Verify Lua code can call Deflate stub (AC-1.3.5).

        Tests Python → Lua → Python round-trip for Deflate.
        """
        lua = LuaRuntime(encoding='latin-1')  # Binary-safe encoding for Deflate/Inflate
        lua.globals().Deflate = Deflate

        # Lua calls Deflate
        result = lua.execute('''
            local data = "test data"
            local compressed = Deflate(data)
            return compressed ~= nil
        ''')

        assert result is True, "Lua should be able to call Deflate"

    def test_lua_can_call_inflate(self):
        """
        Verify Lua code can call Inflate stub (AC-1.3.5).
        """
        lua = LuaRuntime(encoding='latin-1')  # Binary-safe encoding for Deflate/Inflate
        lua.globals().Deflate = Deflate
        lua.globals().Inflate = Inflate

        # Lua calls Deflate → Inflate round-trip
        result = lua.execute('''
            local original = "test data"
            local compressed = Deflate(original)
            local decompressed = Inflate(compressed)
            return decompressed == original
        ''')

        assert result is True, "Lua Deflate → Inflate round-trip failed"

    def test_lua_can_call_conprintf(self, caplog):
        """
        Verify Lua code can call ConPrintf stub (AC-1.3.5).
        """
        lua = LuaRuntime()
        lua.globals().ConPrintf = ConPrintf

        with caplog.at_level(logging.DEBUG):
            # Lua calls ConPrintf with multiple arguments
            lua.execute('''
                ConPrintf("DPS:", 12543.5, "for build:", "Witch")
            ''')

        assert "ConPrintf:" in caplog.text
        assert "DPS:" in caplog.text
        assert "12543.5" in caplog.text

    def test_lua_can_call_conprinttable(self, caplog):
        """
        Verify Lua code can call ConPrintTable stub (AC-1.3.5).
        """
        lua = LuaRuntime()
        lua.globals().ConPrintTable = ConPrintTable

        with caplog.at_level(logging.DEBUG):
            # Lua creates table and passes to ConPrintTable
            lua.execute('''
                local build_info = {name="Witch", level=90}
                ConPrintTable(build_info)
            ''')

        assert "ConPrintTable:" in caplog.text

    def test_lua_can_call_spawnprocess(self, caplog):
        """
        Verify Lua code can call SpawnProcess stub (AC-1.3.5).
        """
        lua = LuaRuntime()
        lua.globals().SpawnProcess = SpawnProcess

        with caplog.at_level(logging.WARNING):
            # Lua calls SpawnProcess (should be no-op)
            lua.execute('''
                SpawnProcess("cmd", "/c", "echo test")
            ''')

        assert "SpawnProcess called in headless mode" in caplog.text

    def test_lua_can_call_openurl(self, caplog):
        """
        Verify Lua code can call OpenURL stub (AC-1.3.5).
        """
        lua = LuaRuntime()
        lua.globals().OpenURL = OpenURL

        with caplog.at_level(logging.WARNING):
            # Lua calls OpenURL (should be no-op)
            lua.execute('''
                OpenURL("https://pathofbuilding.community")
            ''')

        assert "OpenURL called in headless mode" in caplog.text


# ============================================================================
# AC-1.3.6: No Errors When HeadlessWrapper Calls Stubs
# ============================================================================

class TestLuaStubExecution:
    """Test stub functions execute without errors from Lua."""

    def test_deflate_from_lua_no_errors(self):
        """
        Verify Deflate executes without errors when called from Lua (AC-1.3.6).
        """
        lua = LuaRuntime(encoding='latin-1')  # Binary-safe encoding for Deflate/Inflate
        lua.globals().Deflate = Deflate

        # Should not raise LuaError or Python exception
        compressed = lua.execute('''
            local data = "Hello, Path of Building!"
            return Deflate(data)
        ''')

        assert compressed is not None
        # Note: With encoding='latin-1', Lupa returns str instead of bytes
        assert isinstance(compressed, (bytes, str))
        assert len(compressed) > 0

    def test_inflate_from_lua_no_errors(self):
        """
        Verify Inflate executes without errors when called from Lua (AC-1.3.6).
        """
        lua = LuaRuntime(encoding='latin-1')  # Binary-safe encoding for Deflate/Inflate
        lua.globals().Deflate = Deflate
        lua.globals().Inflate = Inflate

        # Should not raise LuaError or Python exception
        decompressed = lua.execute('''
            local original = "Hello, Path of Building!"
            local compressed = Deflate(original)
            return Inflate(compressed)
        ''')

        assert decompressed is not None
        # Note: With encoding='latin-1', Lupa returns str instead of bytes
        assert isinstance(decompressed, (bytes, str))

    def test_conprintf_from_lua_no_errors(self):
        """
        Verify ConPrintf executes without errors when called from Lua (AC-1.3.6).
        """
        lua = LuaRuntime()
        lua.globals().ConPrintf = ConPrintf

        # Should not raise LuaError or Python exception
        lua.execute('''
            ConPrintf("Test message", 123)
        ''')

    def test_conprinttable_from_lua_no_errors(self):
        """
        Verify ConPrintTable executes without errors when called from Lua (AC-1.3.6).
        """
        lua = LuaRuntime()
        lua.globals().ConPrintTable = ConPrintTable

        # Should not raise LuaError or Python exception
        lua.execute('''
            local table = {name="Witch", level=90}
            ConPrintTable(table)
        ''')

    def test_spawnprocess_from_lua_no_errors(self):
        """
        Verify SpawnProcess executes without errors when called from Lua (AC-1.3.6).
        """
        lua = LuaRuntime()
        lua.globals().SpawnProcess = SpawnProcess

        # Should not raise LuaError or Python exception
        lua.execute('''
            SpawnProcess("cmd", "/c", "echo test")
        ''')

    def test_openurl_from_lua_no_errors(self):
        """
        Verify OpenURL executes without errors when called from Lua (AC-1.3.6).
        """
        lua = LuaRuntime()
        lua.globals().OpenURL = OpenURL

        # Should not raise LuaError or Python exception
        lua.execute('''
            OpenURL("https://pathofbuilding.community")
        ''')


# ============================================================================
# Round-Trip Integration Tests
# ============================================================================

class TestRoundTripIntegration:
    """Test complex round-trip scenarios Python → Lua → Python."""

    def test_deflate_inflate_roundtrip_via_lua(self):
        """
        Verify Deflate/Inflate round-trip through Lua preserves data.

        Simulates HeadlessWrapper.lua compressing/decompressing PoB codes.
        """
        lua = LuaRuntime(encoding='latin-1')  # Binary-safe encoding for Deflate/Inflate
        lua.globals().Deflate = Deflate
        lua.globals().Inflate = Inflate

        # Python data → Lua → Python
        original = b"<Build><Tree>tree_data</Tree></Build>"

        # Lua performs compression and decompression
        result = lua.execute('''
            function roundtrip(data)
                local compressed = Deflate(data)
                local decompressed = Inflate(compressed)
                return decompressed
            end
            return roundtrip
        ''')

        decompressed = result(original)
        # Note: With encoding='latin-1', Lupa returns str. Convert for comparison.
        if isinstance(decompressed, str):
            decompressed = decompressed.encode('latin-1')
        assert decompressed == original, "Round-trip via Lua failed"

    def test_large_data_through_lua(self):
        """
        Verify large data (>100KB) passes through Lua without corruption.

        Realistic scenario: Typical PoB codes are 50-100KB XML.
        """
        lua = LuaRuntime(encoding='latin-1')  # Binary-safe encoding for Deflate/Inflate
        lua.globals().Deflate = Deflate
        lua.globals().Inflate = Inflate

        # Generate 150KB data
        original = b"x" * (150 * 1024)

        decompressed = lua.execute('''
            function process(data)
                return Inflate(Deflate(data))
            end
            return process
        ''')(original)

        # Note: With encoding='latin-1', Lupa returns str. Convert for comparison.
        if isinstance(decompressed, str):
            decompressed = decompressed.encode('latin-1')
        assert decompressed == original, "Large data corrupted via Lua"

    def test_multiple_sequential_calls(self):
        """
        Verify multiple sequential stub calls work correctly.

        Simulates HeadlessWrapper.lua making multiple calls during processing.
        """
        lua = LuaRuntime(encoding='latin-1')  # Binary-safe encoding for Deflate/Inflate
        lua.globals().Deflate = Deflate
        lua.globals().Inflate = Inflate
        lua.globals().ConPrintf = ConPrintf

        # Multiple calls in sequence
        result = lua.execute('''
            ConPrintf("Starting compression")
            local data1 = "first data"
            local compressed1 = Deflate(data1)
            ConPrintf("Compressed first data")

            local data2 = "second data"
            local compressed2 = Deflate(data2)
            ConPrintf("Compressed second data")

            local decompressed1 = Inflate(compressed1)
            local decompressed2 = Inflate(compressed2)

            return decompressed1 == data1 and decompressed2 == data2
        ''')

        assert result is True, "Sequential calls failed"

    def test_lua_error_handling_for_invalid_input(self):
        """
        Verify Python TypeError is properly raised in Lua context.

        When Lua passes invalid input, Python exception should propagate.
        """
        lua = LuaRuntime()
        lua.globals().Deflate = Deflate

        # Lua passes number instead of string - should raise error
        with pytest.raises(Exception):  # LuaError wrapping TypeError
            lua.execute('''
                Deflate(12345)  -- Invalid type
            ''')


# ============================================================================
# Performance Baseline Tests
# ============================================================================

class TestPerformance:
    """
    Performance baseline tests for stub functions.

    These tests establish performance baselines for Story 1.8 optimization.
    """

    def test_deflate_inflate_performance_baseline(self):
        """
        Measure Deflate/Inflate performance through Lua.

        Target: <100ms per calculation (Story 1.5 target includes all steps).
        Baseline: Typical PoB code (50KB) should compress in <10ms.
        """
        import time

        lua = LuaRuntime(encoding='latin-1')  # Binary-safe encoding for Deflate/Inflate
        lua.globals().Deflate = Deflate
        lua.globals().Inflate = Inflate

        # Simulate typical PoB code size (50KB)
        data = b"<Build><Tree>tree_data</Tree></Build>" * 1000

        start = time.time()
        lua.execute('''
            function process(data)
                return Inflate(Deflate(data))
            end
            return process
        ''')(data)
        elapsed = time.time() - start

        # Performance baseline: Should complete in <50ms
        assert elapsed < 0.050, f"Performance regression: {elapsed*1000:.1f}ms > 50ms"


# ============================================================================
# Test Organization Notes
# ============================================================================

"""
Integration Test Strategy:

Marking Tests as Slow:
    All tests in this file are marked with @pytest.mark.slow via pytestmark.
    This allows developers to skip these tests during rapid development:

    # Run fast tests only
    pytest tests/ -v -m "not slow"

    # Run all tests including slow Lupa tests
    pytest tests/ -v

Running These Tests:
    # Run this file specifically
    pytest tests/integration/test_stub_functions.py -v

    # Run with coverage
    pytest tests/integration/test_stub_functions.py -v --cov=calculator.stub_functions

Performance Considerations:
    Each test creates a new LuaRuntime instance (~20ms overhead).
    Total test suite execution: ~1-2 seconds.
    Unit tests (test_stub_functions_unit.py) are much faster (~100ms).

Relationship to Other Tests:
    - test_stub_functions_unit.py: Fast unit tests (Python-only)
    - test_stub_functions.py (THIS FILE): Lupa integration tests
    - test_headlesswrapper_stubs.py: Simulated HeadlessWrapper calls

Coverage Target:
    Combined with unit tests, achieve >90% coverage for stub_functions.py.
"""
