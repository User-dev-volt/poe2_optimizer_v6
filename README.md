# PoE2 Build Optimizer

A Python-based optimizer for Path of Exile 2 builds, leveraging Path of Building's calculation engine.

## Installation

### Prerequisites

- Python 3.10+ (tested with Python 3.12)
- pip package manager

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd poe2_optimizer_v6
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Platform-Specific Notes

#### Lupa/LuaJIT Installation

The project uses **Lupa** (Python-LuaJIT bindings) to execute Path of Building's Lua calculation engine.

**Windows:**
- Lupa 2.5+ includes pre-built wheels with LuaJIT 2.1 support
- Use `from lupa.luajit21 import LuaRuntime` for LuaJIT (recommended)
- Default `from lupa import LuaRuntime` uses standard Lua 5.4

**macOS:**
- Pre-built wheels available for most architectures
- Apple Silicon (M1/M2): LuaJIT support included in lupa>=2.0

**Linux:**
- Pre-built wheels available for common distributions
- If building from source is required, ensure `pkg-config` and development headers are installed:
  ```bash
  # Debian/Ubuntu
  sudo apt-get install build-essential pkg-config

  # Fedora/RHEL
  sudo dnf install gcc pkg-config
  ```

#### Verifying LuaJIT Installation

To verify LuaJIT is working correctly:

```bash
python -c "from lupa.luajit21 import LuaRuntime; lua = LuaRuntime(); print(lua.eval('jit.version'))"
```

Expected output: `LuaJIT 2.1.1748459687` (or similar LuaJIT 2.1+ version)

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run only unit tests (fast)
pytest tests/unit/

# Run integration tests (slower, requires Lupa/LuaJIT)
pytest tests/integration/

# Skip slow tests during development
pytest -m "not slow"

# Run optimizer tests (Epic 2)
pytest tests/unit/optimizer/                              # Unit tests (fast, <1s)
pytest -n 1 tests/integration/optimizer/                  # Integration tests with process isolation
```

**Note for Epic 2 Integration Tests:** The optimizer integration tests require `pytest -n 1` for process isolation due to LuaJIT Windows cleanup issues. See "Known Testing Issues" section below for details.

### Parity Testing (Story 1.6)

Parity tests validate calculation accuracy against PoB baseline stats with 0.1% tolerance:

```bash
# Run only parity tests
pytest -m parity -v

# Run specific parity test categories
pytest tests/integration/test_pob_parity.py::TestParityBasic -v
pytest tests/integration/test_pob_parity.py::TestParityCoverage -v
pytest tests/integration/test_pob_parity.py::TestParityPerformance -v

# Generate parity analysis report
# (report is automatically generated at tests/integration/parity_analysis.md)
```

**Continuous Monitoring and Monthly Re-validation:**

To maintain calculation accuracy as the PoB engine evolves, perform monthly re-validation:

1. **Check for PoB Updates:**
   ```bash
   cd external/pob-engine
   git fetch origin
   git log HEAD..origin/main --oneline  # Check for new commits
   ```

2. **Update PoB Engine (if updates available):**
   ```bash
   git pull origin main
   cd ../..
   # Update POB_VERSION.txt with new commit hash
   ```

3. **Run Full Parity Test Suite:**
   ```bash
   pytest -m parity -v
   ```

4. **If Tests Pass:** No action needed. Calculation engine remains accurate.

5. **If Tests Fail (discrepancies found):**
   - Review failure messages to identify which stats diverged
   - Check `tests/integration/parity_analysis.md` for detailed analysis
   - Investigate root cause: PoB formula changes, rounding differences, new constants
   - **Option A:** Update expected baselines if PoB engine legitimately changed:
     ```bash
     python tests/fixtures/parity_builds/generate_expected_stats.py
     pytest -m parity -v  # Verify tests pass with new baseline
     ```
   - **Option B:** Fix calculation engine integration if our implementation drifted
   - Document findings in `parity_analysis.md` with date, PoB version, and resolution

6. **Record Validation:**
   - Add entry to Story 1.6 Change Log documenting re-validation date and outcome
   - Commit updated baselines (if regenerated) with descriptive message

**Baseline Regeneration (when needed):**
```bash
# Generate fresh baseline stats from current PoB engine
cd tests/fixtures/parity_builds
python generate_expected_stats.py

# Verify new baseline matches current calculations
cd ../../..
pytest -m parity -v
```

**Recommended Schedule:**
- Monthly validation: 1st week of each month
- After major PoB updates: Within 1 week of release
- Before production deployments: Always run parity tests

### Known Testing Issues

#### Windows LuaJIT Exception Messages (Expected Behavior)

**Background:** On Windows x64, LuaJIT uses structured exception handling (SEH) for normal JIT operations. Exception code `0xe24c4a02` is thrown and caught internally during trace compilation - this is **normal LuaJIT behavior**, not a bug.

**Impact on Testing:**

Python's fault handler sees these first-chance exceptions and reports them as "Windows fatal exception" messages. While visually noisy, these do not prevent tests from completing successfully.

**SOLUTION - Automated Testing with pytest-xdist (✅ RECOMMENDED FOR EPIC 2):**

pytest-xdist isolates tests in worker processes, allowing automated test execution with proper exit codes:

```bash
# Integration tests (Story 1.5, 1.6, 1.7) - AUTOMATED ✅
pytest -n 1 tests/integration/

# Specific test file
pytest -n 1 tests/integration/test_single_calculation.py

# Full regression suite for Epic 2
pytest -n auto tests/integration/  # Parallel execution
```

**Result:**
- ✅ Tests run automatically (no manual intervention)
- ✅ All tests report pass/fail correctly
- ✅ Exit code 0 on success (CI/CD compatible)
- ⚠️ Exception messages appear in output (cosmetic, can be ignored)

**Performance Benchmarks - Manual Execution:**

pytest-benchmark is incompatible with pytest-xdist. For performance tests, use direct Python execution:

```bash
# Story 1.8 performance benchmarks
python -m pytest tests/performance/test_batch_calculation.py --benchmark-only

# Or run benchmark scripts directly
python measure_batch_perf.py
```

**Status:**
- **Integration testing:** ✅ RESOLVED with pytest-xdist (Epic 2 ready)
- **Performance benchmarking:** Manual execution acceptable (run less frequently)
- Exception messages are expected LuaJIT behavior on Windows x64

## Project Structure

```
poe2_optimizer_v6/
├── src/
│   ├── parsers/          # PoB import code parsing (Story 1.1)
│   ├── models/           # Data models (BuildData, etc.)
│   └── calculator/       # Lua calculation engine integration (Story 1.2+)
├── tests/
│   ├── unit/            # Fast unit tests
│   ├── integration/     # Integration tests (Lupa/LuaJIT)
│   └── fixtures/        # Test data and fixtures
├── requirements.txt     # Production dependencies
└── README.md           # This file
```

## Development Status

**Epic 1: Foundation - PoB Calculation Engine Integration**
- ✅ Story 1.1: Parse PoB Import Code (Complete)
- ✅ Story 1.2: Setup Lupa + LuaJIT Runtime (Complete)
- ⏳ Story 1.3: Implement Required Stub Functions (Pending)
- ⏳ Story 1.4: Load HeadlessWrapper.lua and PoB Modules (Pending)
- ⏳ Story 1.5: Execute Single Build Calculation (Pending)

## License

[License information to be added]
