# Integration Tests

Integration tests verify the interaction between the PoE2 Optimizer and external dependencies (Lupa/LuaJIT, PoB calculation engine).

## Purpose

Integration tests are **slower** than unit tests because they:
- Require actual Lupa/LuaJIT runtime initialization
- Interact with external C libraries (LuaJIT via Lupa)
- Execute Lua code (compilation overhead on first run)

These tests validate the foundation for PoB calculation engine integration across Stories 1.2-1.5.

## Test Categories

### Story 1.2: Lupa/LuaJIT Integration (`test_lupa_basic.py`)
- **Basic LuaJIT Integration:** Runtime initialization, Lua script execution, global namespace access, function calls
- **Data Type Conversions:** Python ↔ Lua type mapping (dict/table, numbers, strings, nil/None)
- **Performance Baseline:** Measurement of 1000 Lua function calls (baseline for Story 1.8 optimization)
- **Error Handling:** LuaError exception handling (foundation for Stories 1.3-1.5)

### Future Stories
- **Story 1.4:** PoB module loading tests (HeadlessWrapper.lua, PassiveTree.lua)
- **Story 1.5:** End-to-end calculation tests (BuildData → BuildStats)

## Running Integration Tests

### Run All Integration Tests
```bash
pytest tests/integration/
```

### Run Specific Test File
```bash
pytest tests/integration/test_lupa_basic.py -v
```

### Skip Slow Tests During Development
Integration tests are marked with `@pytest.mark.slow` to allow optional skipping:

```bash
# Skip all slow tests (fast iteration during development)
pytest -m "not slow"

# Run only slow tests
pytest -m "slow"
```

## Test Markers

- **`@pytest.mark.slow`**: Tests requiring external dependencies (Lupa/LuaJIT) that are slower than unit tests

To register custom markers and avoid warnings, add to `pytest.ini`:
```ini
[pytest]
markers =
    slow: marks tests as slow (external dependencies, integration tests)
```

## Platform-Specific Notes

### Windows
- **Lupa 2.5** includes pre-built wheels with LuaJIT 2.1 support (no compilation required)
- **Known Issue:** Lupa may raise Windows fatal exceptions for some Lua errors instead of `LuaError`. Tests handle both exception types.
- **LuaJIT Access:** Use `from lupa.luajit21 import LuaRuntime` for LuaJIT (default `LuaRuntime` uses Lua 5.4)

### macOS
- Pre-built wheels available for Intel and Apple Silicon (M1/M2)
- LuaJIT 2.1 included in Lupa 2.0+

### Linux
- Pre-built wheels available for most distributions
- If building from source: ensure `pkg-config` and development headers are installed

## Performance Expectations

Integration tests are slower than unit tests:
- **First Lua call:** ~200ms (includes Lua function compilation overhead)
- **Subsequent calls:** <1ms (after JIT compilation)
- **1000 function calls:** 50-150ms (varies by system)

Story 1.8 optimizations achieved 8x improvement (2.0ms per calculation, ~2.0s for 1000 calculations). Single calculation target (<100ms) exceeded; batch target revised to <2s based on Lua execution floor.

## Acceptance Criteria Validation

Story 1.2 integration tests validate all acceptance criteria:

| AC | Description | Test Coverage |
|----|-------------|---------------|
| AC-1.2.1 | Lupa library installed and tested | `test_lua_runtime_initialization` |
| AC-1.2.2 | LuaJIT runtime initializes successfully | `test_verify_luajit_version` |
| AC-1.2.3 | Can load and execute simple Lua scripts | `test_execute_simple_lua_script` |
| AC-1.2.4 | Lua global namespace accessible from Python | `test_lua_global_namespace_access` |
| AC-1.2.5 | Python can call Lua functions and retrieve results | `test_call_lua_function_from_python` |

## References

- **Testing Pyramid:** Integration tests are 30% of Epic 1 test suite (Solution Architecture: Lines 1221-1234)
- **Story 1.2 Acceptance Criteria:** Tech Spec Epic 1: Lines 876-885
- **Performance Requirements:** Tech Spec Epic 1: Lines 516-554 (NFR-1)
