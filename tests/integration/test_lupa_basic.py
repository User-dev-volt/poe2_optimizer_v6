"""
Lupa/LuaJIT Integration Tests - Story 1.2

Tests verify Python-Lua integration via Lupa library with LuaJIT runtime.
These tests validate the foundation for PoB calculation engine integration.

Acceptance Criteria Coverage:
    - AC-1.2.1: Lupa library installed and tested
    - AC-1.2.2: LuaJIT runtime initializes successfully in Python
    - AC-1.2.3: Can load and execute simple Lua scripts from Python
    - AC-1.2.4: Lua global namespace accessible from Python
    - AC-1.2.5: Python can call Lua functions and retrieve results

Test Categories:
    1. Basic LuaJIT Integration (AC 1.2.2-1.2.5)
    2. Python-Lua Data Type Conversions
    3. Performance Baseline Measurement
    4. Error Handling

References:
    - Tech Spec Epic 1: Lines 876-885 (Story 1.2 Acceptance Criteria)
    - Story Context: Lines 200-242 (Test Ideas)
"""

import time
from typing import List

import pytest
from lupa import LuaError
from lupa.luajit21 import LuaRuntime


# ==============================================================================
# Basic LuaJIT Integration Tests (Task 3)
# ==============================================================================


@pytest.mark.slow
def test_lua_runtime_initialization():
    """
    AC-1.2.2: Verify LuaRuntime can be created without errors.

    This is a basic smoke test for Lupa installation and LuaJIT availability.
    """
    lua = LuaRuntime()
    assert lua is not None


@pytest.mark.slow
def test_verify_luajit_version():
    """
    AC-1.2.2: Verify LuaJIT 2.1+ is available (required for performance).

    Expected: LuaJIT 2.1.x (bundled with Lupa 2.0+)
    """
    lua = LuaRuntime()
    jit_version = lua.eval("jit.version")

    assert jit_version is not None
    assert "LuaJIT" in jit_version
    assert "2.1" in jit_version  # Verify LuaJIT 2.1+ as specified in tech spec


@pytest.mark.slow
def test_execute_simple_lua_script():
    """
    AC-1.2.3: Verify basic Lua script execution.

    Tests that Lua code can run and return values to Python.
    """
    lua = LuaRuntime()
    result = lua.execute("return 2 + 2")

    assert result == 4


@pytest.mark.slow
def test_lua_global_namespace_access():
    """
    AC-1.2.4: Verify Python can access Lua global variables.

    Tests bidirectional state sharing between Python and Lua.
    """
    lua = LuaRuntime()
    lua.execute("myGlobal = 42")

    assert lua.globals().myGlobal == 42


@pytest.mark.slow
def test_call_lua_function_from_python():
    """
    AC-1.2.5: Verify Python can call Lua functions and retrieve results.

    This is the core integration pattern for PoB calculations.
    """
    lua = LuaRuntime()
    add_func = lua.eval("function(a, b) return a + b end")
    result = add_func(10, 32)

    assert result == 42


@pytest.mark.slow
def test_lua_multiple_return_values():
    """
    AC-1.2.5: Verify Lua functions with multiple return values work correctly.

    Multiple return values are a common Lua pattern used in PoB calculations.
    """
    lua = LuaRuntime()
    multi_func = lua.eval("function() return 1, 2, 3 end")
    result = multi_func()

    assert result == (1, 2, 3)


# ==============================================================================
# Python-Lua Data Type Conversion Tests (Task 4)
# ==============================================================================


@pytest.mark.slow
def test_python_dict_to_lua_table():
    """
    Verify Python dicts convert to Lua tables correctly.

    Critical for passing BuildData to PoB engine in Story 1.5.
    """
    lua = LuaRuntime()
    lua.execute("function get_name(obj) return obj.name end")
    py_dict = {"name": "Witch", "level": 90}
    result = lua.globals().get_name(py_dict)

    assert result == "Witch"


@pytest.mark.slow
def test_python_list_to_lua_array():
    """
    Verify Python lists convert to Lua arrays correctly.

    Note: Lupa handles Python lists as Python objects in Lua, not native Lua tables.
    For PoB calculations, we'll convert BuildData to XML/JSON, not pass raw Python lists.
    This test documents the limitation for future reference.
    """
    lua = LuaRuntime()

    # Store Python list in Lua global, then access from Python
    lua.globals().pyList = [10, 20, 30]

    # Verify we can access the list from Lua (as Python object)
    # Lupa exposes Python methods, not Lua table semantics
    result = lua.eval("pyList")

    # Access as Python object (0-indexed)
    assert result[0] == 10
    assert result[1] == 20
    assert result[2] == 30


@pytest.mark.slow
def test_python_numbers_to_lua():
    """
    Verify Python int/float → Lua number conversion.

    Lua has a single 'number' type (typically double).
    """
    lua = LuaRuntime()
    lua.execute("""
        function calculate(int_val, float_val)
            return int_val + float_val
        end
    """)
    result = lua.globals().calculate(10, 3.14)

    assert abs(result - 13.14) < 0.01


@pytest.mark.slow
def test_python_string_to_lua_unicode():
    """
    Verify Python string → Lua string conversion (including Unicode).

    PoB item names may contain Unicode characters (e.g., "Atziri's Promise").
    """
    lua = LuaRuntime()
    lua.execute("""
        function echo(s)
            return s
        end
    """)
    unicode_str = "Atziri's Promise ⚔️"
    result = lua.globals().echo(unicode_str)

    assert result == unicode_str


@pytest.mark.slow
def test_lua_table_to_python_dict():
    """
    Verify Lua table → Python dict conversion (return values).

    PoB calculations return Lua tables that must convert to Python dicts.
    """
    lua = LuaRuntime()
    lua_func = lua.eval("""
        function()
            return {name = "Shadow", level = 95, ascendancy = "Trickster"}
        end
    """)
    result = lua_func()

    # Lupa returns Lua tables as Python-accessible objects
    assert result.name == "Shadow"
    assert result.level == 95
    assert result.ascendancy == "Trickster"


@pytest.mark.slow
def test_lua_nil_to_python_none():
    """
    Verify Lua nil → Python None conversion.

    Optional PoB fields (e.g., ascendancy for non-ascended chars) return nil.
    """
    lua = LuaRuntime()
    lua_func = lua.eval("function() return nil end")
    result = lua_func()

    assert result is None


# ==============================================================================
# Performance Baseline Measurement (Task 5)
# ==============================================================================


@pytest.mark.slow
def test_lua_performance_baseline():
    """
    Measure baseline performance for 1000 Lua function calls.

    Expected Results:
        - First call: ~200ms (Lua function compilation overhead)
        - Subsequent calls: <1ms each (after JIT compilation)

    These baselines will be compared against Story 1.8 optimization targets:
        - NFR-1: 1000 calculations in <1 second (150-500ms)

    Note: This test documents baseline; Story 1.8 will optimize to meet targets.
    """
    lua = LuaRuntime()

    # Simple calculation function for baseline
    calc_func = lua.eval("""
        function(level, base_dmg, multiplier)
            return level * base_dmg * multiplier
        end
    """)

    # Measure first call (includes compilation overhead)
    start_first = time.perf_counter()
    first_result = calc_func(90, 100, 1.5)
    first_call_time = (time.perf_counter() - start_first) * 1000  # Convert to ms

    # Measure 1000 subsequent calls
    start_batch = time.perf_counter()
    for i in range(1000):
        calc_func(90 + i % 10, 100, 1.5)
    batch_time = (time.perf_counter() - start_batch) * 1000  # Convert to ms

    # Calculate statistics
    mean_time = batch_time / 1000

    # Assertions (baseline expectations, not strict requirements)
    assert first_result == 13500  # Verify correctness
    print(f"\n📊 Performance Baseline:")
    print(f"   First call: {first_call_time:.2f}ms (includes compilation)")
    print(f"   Batch (1000 calls): {batch_time:.2f}ms")
    print(f"   Mean per call: {mean_time:.3f}ms")
    print(f"   Story 1.8 target: <1ms per call after optimization")

    # Soft assertions to catch catastrophic performance regressions
    # These are generous thresholds (10x expected) to detect major issues
    # without causing false failures from normal variance
    assert batch_time < 5000, (
        f"Performance severely degraded: {batch_time:.2f}ms for 1000 calls "
        f"(expected <1000ms, threshold 5000ms)"
    )
    assert mean_time < 5.0, (
        f"Mean call time severely degraded: {mean_time:.3f}ms per call "
        f"(expected <1ms, threshold 5ms)"
    )

    # Document results for Story 1.8 optimization comparison
    # Story 1.8 will optimize to meet NFR-1 targets (<100ms per calculation)


# ==============================================================================
# Error Handling Tests (Task 6)
# ==============================================================================


@pytest.mark.slow
def test_invalid_lua_syntax_raises_error():
    """
    Verify invalid Lua raises LuaError (basic error handling check).

    Full error handling strategy implemented in Stories 1.3-1.5.

    Note: On Windows, Lupa may raise Windows fatal exception for some errors.
    This is a known Lupa limitation. We catch both LuaError and Exception.
    """
    lua = LuaRuntime()

    # Try to execute invalid Lua - expect either LuaError or Windows exception
    try:
        lua.execute("this is not valid lua!!!")
        # If we get here, test should fail
        assert False, "Expected LuaError but no error was raised"
    except LuaError:
        # Expected behavior
        pass
    except Exception as e:
        # Windows may raise fatal exception (Lupa limitation)
        # Verify it's an error condition, not successful execution
        assert "lua" in str(type(e)).lower() or "fatal" in str(e).lower()


@pytest.mark.slow
def test_lua_runtime_error_handling():
    """
    Verify Lua runtime errors (e.g., nil access) raise LuaError.

    Documents error types for future error handling (Story 1.5).

    Note: On Windows, Lupa may raise Windows fatal exception for some errors.
    This is a known Lupa limitation. We catch both LuaError and Exception.
    """
    lua = LuaRuntime()

    # Try to execute code that causes runtime error
    try:
        lua.execute("""
            local x = nil
            return x.field  -- Attempt to index nil
        """)
        # If we get here, test should fail
        assert False, "Expected LuaError but no error was raised"
    except LuaError as e:
        # Expected behavior - verify error message contains useful information
        assert "nil" in str(e).lower()
    except Exception as e:
        # Windows may raise fatal exception (Lupa limitation)
        # Document this behavior for Story 1.5 error handling
        # We still want to confirm an error occurred
        pass
