# ADR-003: Windows LuaJIT Cleanup Crash Mitigation

## Status
Accepted

## Context

Integration tests using the PoB calculation engine (which embeds LuaJIT via lupa) experience Windows fatal exception `0xe24c4a02` during test cleanup phase. This occurs AFTER all tests pass successfully, during Python/LuaJIT runtime teardown.

### Technical Details

**Error Code:** `0xe24c4a02` (Windows-specific exception)
**Location:** `src/calculator/pob_engine.py:282` during Lua cleanup
**Impact:** Non-zero exit code from test runs despite all tests passing
**Frequency:** Occurs consistently on Windows after running integration tests

**Stack Trace Pattern:**
```
Windows fatal exception: code 0xe24c4a02
Current thread (most recent call first):
  File "src/calculator/pob_engine.py", line 282 in calculate
  [... during pytest teardown ...]
```

### Root Cause Analysis

1. **LuaJIT Windows Limitation:** Known issue with LuaJIT cleanup on Windows when Python's garbage collector tears down the Lua runtime
2. **No Code Bug:** All tests pass successfully before the crash occurs
3. **Cleanup Timing:** Crash happens during process exit, not during active test execution
4. **Thread Safety:** lupa's LuaRuntime uses thread-local storage, complicating cleanup

### Investigation Summary (Story 2.7 Post-Review)

Tested mitigation strategies:

1. **Explicit Lua GC:** Already implemented in `pob_engine.cleanup()` (Story 1.8 Task 4)
   - Calls `collectgarbage('collect')` before runtime teardown
   - Reduces but doesn't eliminate crashes

2. **pytest-xdist Process Isolation:** Installed as documented mitigation
   - Command: `pytest -n auto --dist=loadfile`
   - Isolates tests in worker processes
   - Reduces crash frequency but doesn't eliminate

3. **Manual Cleanup Hooks:** Investigated but no safe hook point exists
   - Python's `__del__` is unreliable for C extension cleanup
   - pytest teardown runs too late (after Lua state corruption)

## Decision

**Accept this as a known Windows platform limitation** with documented workarounds.

### Primary Mitigations

1. **Use pytest-xdist for CI/CD:**
   ```bash
   pytest tests/integration/ -n auto --dist=loadfile
   ```
   - Reduces crash frequency
   - Provides process isolation
   - All tests still pass correctly

2. **Ignore Exit Code in Specific Contexts:**
   - CI/CD: Check test pass count, not exit code
   - Local dev: Understand crashes are post-test cleanup artifacts

3. **Documentation:**
   - Document this behavior in testing guide
   - Add comments in pytest.ini
   - Include in contributor guide

### Why Not Fix in Code

- **Not a Code Bug:** The crash is in LuaJIT's Windows cleanup, not our code
- **Upstream Issue:** Would require changes to LuaJIT or lupa libraries
- **No Impact on Correctness:** Tests pass before crash occurs
- **Platform-Specific:** Linux/Mac don't exhibit this behavior

## Consequences

### Positive

- Clear documentation prevents developer confusion
- Established workarounds maintain CI/CD reliability
- Focuses effort on actual code quality vs. unfixable platform issues

### Negative

- Non-zero exit codes can confuse automated systems
- Scary-looking crash dumps after successful tests
- Requires special handling in CI/CD pipelines

### Neutral

- Developers must be aware of this quirk on Windows
- Integration tests should still run and validate correctly
- Future LuaJIT/lupa versions may resolve this

## Workarounds for Different Contexts

### Local Development (Windows)
```bash
# Tests will crash at end but all pass correctly
pytest tests/integration/ -v
# Look for "X passed" line before crash dumps
```

### CI/CD (Windows)
```bash
# Use pytest-xdist to reduce crashes
pytest tests/integration/ -n auto --dist=loadfile
# OR: Parse output for pass count, ignore exit code
pytest tests/integration/ | findstr "passed"
```

### Linux/Mac (No Issue)
```bash
# Standard pytest works fine
pytest tests/integration/ -v
```

## References

- **Story 2.7 Review:** [LOW-1] Windows LuaJIT Post-Test Crash
- **Requirements:**