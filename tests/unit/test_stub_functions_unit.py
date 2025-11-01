"""
Unit Tests for PoB Stub Functions (Fast, No Lupa Dependency)

Tests stub functions in isolation without Lupa/Lua integration. These tests
are FAST and focus on Python-side behavior, type checking, error handling,
and edge cases.

Integration tests with Lupa are in tests/integration/test_stub_functions.py.

Test Coverage:
    - AC-1.3.1: Deflate/Inflate round-trip, various data sizes, error handling
    - AC-1.3.2: ConPrintf logging, varargs, various types
    - AC-1.3.3: ConPrintTable logging, None handling
    - AC-1.3.4: SpawnProcess/OpenURL no-ops, warning logs

Story Context:
    Story 1.3 focuses on Python stub function implementation. Full Lua
    integration happens in Story 1.4 (HeadlessWrapper.lua loading).

References:
    - Story 1.3: Lines 63-110 (Task 2: Integration Tests)
    - Story 1.3: Lines 167-184 (Task 5: Error Handling)
    - Tech Spec Epic 1: Lines 888-898 (Story 1.3 Acceptance Criteria)
"""

import logging
import zlib
import pytest

from src.calculator.stub_functions import (
    Deflate,
    Inflate,
    ConPrintf,
    ConPrintTable,
    SpawnProcess,
    OpenURL,
)


# ============================================================================
# AC-1.3.1: Deflate/Inflate Tests
# ============================================================================

class TestDeflateInflate:
    """Test suite for Deflate/Inflate compression functions."""

    def test_deflate_inflate_roundtrip(self):
        """
        Verify Deflate → Inflate preserves data (AC-1.3.1).

        Round-trip compression test ensures Python zlib is compatible with
        PoB's Lua zlib library. Critical for PoB code parsing.
        """
        original = b"Hello, Path of Building!"
        compressed = Deflate(original)
        decompressed = Inflate(compressed)
        assert decompressed == original, "Round-trip failed: data corrupted"

    def test_deflate_reduces_size(self):
        """
        Verify Deflate compresses typical PoB data (AC-1.3.1).

        PoB codes contain repetitive XML structure, which compresses well.
        Compression ratio should be >2x for typical data.
        """
        # Simulate repetitive PoB XML data
        original = b"<Build><Tree>tree_data</Tree></Build>" * 100
        compressed = Deflate(original)

        assert len(compressed) < len(original), "Deflate did not compress data"
        compression_ratio = len(original) / len(compressed)
        assert compression_ratio > 2.0, f"Poor compression ratio: {compression_ratio:.2f}x"

    def test_deflate_handles_empty_data(self):
        """
        Verify Deflate handles empty data without errors (AC-1.3.1).

        Edge case: Empty PoB codes should compress/decompress correctly.
        """
        original = b""
        compressed = Deflate(original)
        decompressed = Inflate(compressed)
        assert decompressed == original, "Empty data round-trip failed"
        assert len(compressed) > 0, "Deflate should produce non-empty output"

    def test_deflate_handles_small_data(self):
        """
        Verify Deflate handles small data <1KB (AC-1.3.1).

        Edge case: Small PoB code fragments should compress correctly.
        """
        original = b"<Build/>"
        compressed = Deflate(original)
        decompressed = Inflate(compressed)
        assert decompressed == original, "Small data round-trip failed"

    def test_deflate_handles_large_data(self):
        """
        Verify Deflate handles large data >100KB (AC-1.3.1).

        Realistic test: Typical PoB codes are 50-100KB XML. Ensure large
        builds compress without errors or performance issues.
        """
        # Generate 150KB of data (larger than typical PoB code)
        original = b"x" * (150 * 1024)
        compressed = Deflate(original)
        decompressed = Inflate(compressed)

        assert decompressed == original, "Large data round-trip failed"
        assert len(compressed) < len(original), "Large data did not compress"

    def test_deflate_accepts_string_input(self):
        """
        Verify Deflate accepts string input and encodes as UTF-8 (AC-1.3.1).

        Lua strings may be passed as Python str. Deflate should auto-convert.
        """
        original_str = "Hello, Path of Building!"
        compressed = Deflate(original_str)
        decompressed = Inflate(compressed)

        # Verify round-trip with UTF-8 encoding
        assert decompressed == original_str.encode('utf-8')

    def test_deflate_invalid_input_raises_type_error(self):
        """
        Verify Deflate rejects non-bytes/non-str input (AC-1.3.1).

        Type safety: Lua-Python boundary requires explicit type checking.
        Invalid types should raise TypeError with clear message.
        """
        with pytest.raises(TypeError, match="Deflate expects bytes or str"):
            Deflate(12345)  # int

        with pytest.raises(TypeError, match="Deflate expects bytes or str"):
            Deflate([1, 2, 3])  # list

        with pytest.raises(TypeError, match="Deflate expects bytes or str"):
            Deflate(None)  # None

    def test_inflate_invalid_input_raises_type_error(self):
        """
        Verify Inflate rejects non-bytes/non-str input (AC-1.3.1).

        Type safety: Inflate accepts bytes or str (for Lua compatibility).
        Rejects other types like int, list, None.
        """
        with pytest.raises(TypeError, match="Inflate expects bytes or str"):
            Inflate(12345)  # int

        with pytest.raises(TypeError, match="Inflate expects bytes or str"):
            Inflate([1, 2, 3])  # list

        with pytest.raises(TypeError, match="Inflate expects bytes or str"):
            Inflate(None)  # None

    def test_inflate_corrupted_data_raises_error(self):
        """
        Verify Inflate raises zlib.error for corrupted data (AC-1.3.1).

        Error handling: Corrupted PoB codes should produce clear error message.
        Caller wraps in try/except to present user-friendly error.
        """
        with pytest.raises(zlib.error):
            Inflate(b"not compressed data!!!")

        with pytest.raises(zlib.error):
            Inflate(b"\x00\x00\x00invalid")


# ============================================================================
# AC-1.3.2: ConPrintf Tests
# ============================================================================

class TestConPrintf:
    """Test suite for ConPrintf console output stub."""

    def test_conprintf_logs_messages(self, caplog):
        """
        Verify ConPrintf logs to Python logging at DEBUG level (AC-1.3.2).

        Uses pytest caplog fixture to capture logging output.
        """
        with caplog.at_level(logging.DEBUG):
            ConPrintf("Test message", 123, 45.6)

        # Verify logging output
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "DEBUG"
        assert "ConPrintf: Test message 123 45.6" in caplog.text

    def test_conprintf_no_arguments(self, caplog):
        """
        Verify ConPrintf handles no arguments without crashing (AC-1.3.2).

        Edge case: Empty ConPrintf() call from Lua.
        """
        with caplog.at_level(logging.DEBUG):
            ConPrintf()

        assert len(caplog.records) == 1
        assert "ConPrintf: " in caplog.text  # Empty message

    def test_conprintf_single_argument(self, caplog):
        """
        Verify ConPrintf handles single argument (AC-1.3.2).
        """
        with caplog.at_level(logging.DEBUG):
            ConPrintf("Single message")

        assert "ConPrintf: Single message" in caplog.text

    def test_conprintf_multiple_arguments(self, caplog):
        """
        Verify ConPrintf handles varargs (AC-1.3.2).

        Lua varargs: ConPrintf("DPS:", 12543.5, "for build:", build_name)
        """
        with caplog.at_level(logging.DEBUG):
            ConPrintf("DPS:", 12543.5, "for build:", "Witch")

        assert "ConPrintf: DPS: 12543.5 for build: Witch" in caplog.text

    def test_conprintf_various_types(self, caplog):
        """
        Verify ConPrintf handles various data types (AC-1.3.2).

        Lua may pass strings, numbers, booleans, nil. All should convert to str.
        """
        with caplog.at_level(logging.DEBUG):
            ConPrintf("String", 42, 3.14, True, None)

        assert "ConPrintf: String 42 3.14 True None" in caplog.text

    def test_conprintf_returns_none(self):
        """
        Verify ConPrintf returns None (no-op from Lua perspective) (AC-1.3.2).
        """
        result = ConPrintf("test")
        assert result is None, "ConPrintf should return None"


# ============================================================================
# AC-1.3.3: ConPrintTable Tests
# ============================================================================

class TestConPrintTable:
    """Test suite for ConPrintTable table printing stub."""

    def test_conprinttable_logs_dict(self, caplog):
        """
        Verify ConPrintTable logs Python dict structures (AC-1.3.3).

        Lupa Lua tables with .items() method convert to Python dict.
        """
        with caplog.at_level(logging.DEBUG):
            # Simulate Lua table as Python dict with .items() method
            class LuaTableMock:
                def items(self):
                    return {"name": "Witch", "level": 90}.items()

            ConPrintTable(LuaTableMock())

        assert "ConPrintTable:" in caplog.text
        assert "name" in caplog.text
        assert "Witch" in caplog.text
        assert "level" in caplog.text
        assert "90" in caplog.text

    def test_conprinttable_handles_none(self, caplog):
        """
        Verify ConPrintTable handles None without crashing (AC-1.3.3).

        Edge case: Lua nil may be passed as Python None.
        """
        with caplog.at_level(logging.DEBUG):
            ConPrintTable(None)

        # Should log "None" without errors
        assert "ConPrintTable:" in caplog.text

    def test_conprinttable_fallback_for_non_dict(self, caplog):
        """
        Verify ConPrintTable handles non-dict objects (AC-1.3.3).

        Fallback: Convert to string representation if .items() unavailable.
        """
        with caplog.at_level(logging.DEBUG):
            ConPrintTable("not a table")

        assert "ConPrintTable: not a table" in caplog.text

    def test_conprinttable_handles_exception_gracefully(self, caplog):
        """
        Verify ConPrintTable handles exceptions without crashing (AC-1.3.3).

        Error handling: Complex nested tables may fail conversion. Log error.
        """
        class BadTable:
            def items(self):
                raise RuntimeError("Simulated error")

        with caplog.at_level(logging.DEBUG):
            ConPrintTable(BadTable())

        assert "unable to parse table" in caplog.text

    def test_conprinttable_returns_none(self):
        """
        Verify ConPrintTable returns None (no-op from Lua perspective) (AC-1.3.3).
        """
        result = ConPrintTable({"test": "data"})
        assert result is None, "ConPrintTable should return None"


# ============================================================================
# AC-1.3.4: SpawnProcess/OpenURL Tests
# ============================================================================

class TestSystemStubs:
    """Test suite for SpawnProcess/OpenURL security no-ops."""

    def test_spawnprocess_is_noop(self, caplog):
        """
        Verify SpawnProcess doesn't crash in headless mode (AC-1.3.4).

        Security: No process execution should occur. Log warning.
        """
        with caplog.at_level(logging.WARNING):
            result = SpawnProcess("cmd", "/c", "echo test")

        assert result is None, "SpawnProcess should return None"
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"
        assert "SpawnProcess called in headless mode" in caplog.text
        assert "cmd" in caplog.text

    def test_spawnprocess_no_arguments(self, caplog):
        """
        Verify SpawnProcess handles no arguments (AC-1.3.4).

        Edge case: Empty SpawnProcess() call from Lua.
        """
        with caplog.at_level(logging.WARNING):
            result = SpawnProcess()

        assert result is None
        assert "SpawnProcess called in headless mode" in caplog.text

    def test_openurl_is_noop(self, caplog):
        """
        Verify OpenURL doesn't crash in headless mode (AC-1.3.4).

        Security: No URL opening should occur. Log warning.
        """
        with caplog.at_level(logging.WARNING):
            result = OpenURL("https://pathofbuilding.community")

        assert result is None, "OpenURL should return None"
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"
        assert "OpenURL called in headless mode" in caplog.text
        assert "pathofbuilding.community" in caplog.text

    def test_openurl_empty_string(self, caplog):
        """
        Verify OpenURL handles empty URL string (AC-1.3.4).

        Edge case: Empty string URL from Lua.
        """
        with caplog.at_level(logging.WARNING):
            result = OpenURL("")

        assert result is None
        assert "OpenURL called in headless mode" in caplog.text


# ============================================================================
# Test Organization Notes
# ============================================================================

"""
Test Organization Strategy:

Unit Tests (THIS FILE):
    - Fast execution (<1s total)
    - No external dependencies (Lupa not required)
    - Test Python-side behavior only
    - Focus: Type checking, error handling, edge cases

Integration Tests (tests/integration/test_stub_functions.py):
    - Slower execution (requires Lupa initialization)
    - Test Lua calling Python stubs via lua.globals()
    - Test round-trip Python → Lua → Python
    - Mark with @pytest.mark.slow

HeadlessWrapper Simulation Tests (tests/integration/test_headlesswrapper_stubs.py):
    - Test realistic HeadlessWrapper.lua call patterns
    - Simulate PoB module usage
    - Verify no errors during Lua execution

Coverage Target:
    >90% for calculator/stub_functions.py (critical path)

Run Commands:
    # Fast unit tests only (this file)
    pytest tests/unit/test_stub_functions_unit.py -v

    # All tests (including slow Lupa tests)
    pytest tests/ -v

    # Skip slow tests during development
    pytest tests/ -v -m "not slow"
"""
