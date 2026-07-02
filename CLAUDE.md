# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PoE2 Build Optimizer - A Python optimizer that parses Path of Building (PoB) import codes and uses hill climbing to discover superior passive tree configurations. Leverages PoB's Lua calculation engine via Lupa (Python-LuaJIT bindings).

## Commands

### Setup
```bash
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python scripts/setup_pob.py  # THE setup command: submodule @ pin + patches + POB_VERSION.txt
```

### Testing
```bash
# Unit tests (fast, <1s)
pytest tests/unit/

# Integration tests - MUST use -n 1 on Windows (LuaJIT cleanup issue)
pytest -n 1 tests/integration/

# Parity tests (validate against PoB baselines, ±0.1% tolerance)
pytest -m parity -v

# Single test file
pytest -n 1 tests/integration/test_file.py -v

# Skip slow tests during development
pytest -m "not slow"

# Coverage
pytest --cov=src --cov-report=html
```

### Performance Benchmarks (incompatible with pytest-xdist)
```bash
python -m pytest tests/performance/test_batch_calculation.py --benchmark-only
python measure_batch_perf.py
```

### Verify LuaJIT
```bash
python -c "from lupa.luajit21 import LuaRuntime; lua = LuaRuntime(); print(lua.eval('jit.version'))"
```

## Architecture

### Data Flow
```
PoB Code (Base64) → parse_pob_code() → BuildData
BuildData → calculate_build_stats() → BuildStats
BuildStats → optimize_build() → OptimizationResult
```

### Source Layout
- `src/parsers/` - PoB code parsing: Base64 → zlib → XML → BuildData
- `src/calculator/` - LuaJIT wrapper executing PoB Lua calculations
- `src/optimizer/` - Hill climbing algorithm, neighbor generation, budget tracking
- `src/models/` - Data structures (BuildData, BuildStats, OptimizationConfig)

### Key Files
- `src/optimizer/hill_climbing.py` - Main optimization algorithm
- `src/calculator/pob_engine.py` - Lupa/LuaJIT integration
- `src/calculator/build_calculator.py` - High-level calculation API (thread-local)
- `src/calculator/passive_tree.py` - Tree graph and BFS connectivity validation
- `src/optimizer/budget_tracker.py` - Dual budget system (points + respecs)

### External Dependencies
- `external/pob-engine/` - Git submodule containing Path of Building PoE2 engine
- `external/patches/` - Patches for submodule (see ADR-004)

## Critical Constraints

### Thread Safety
- LuaJIT is NOT thread-safe
- One `PoBCalculationEngine` per thread (uses `threading.local()`)
- Never share calculator instances across threads

### Windows LuaJIT
- Exception code `0xe24c4a02` during tests is normal LuaJIT SEH behavior
- Always use `pytest -n 1` for integration tests (process isolation)
- See `docs/decisions/ADR-003-windows-luajit-cleanup-mitigation.md`

### Budget Enforcement
- Hard constraints: invalid moves are filtered, not penalized
- `unallocated_points` - free allocations
- `respec_points` - costly deallocations (None = unlimited)

### Passive Tree
- Pre-built from `PassiveTree.lua`, immutable during optimization
- All allocated nodes must be connected (BFS validation from start node)

### Spell/DOT Builds (Story 2.9)
- Hybrid routing: Attack skills → MinimalCalc (fast), Spell/DOT → subprocess (accurate)
- Global.lua nil-safety patch required (ADR-004)

## Test Markers
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.parity` - PoB baseline validation
- `@pytest.mark.gui_parity` - GUI parity tests
- `@pytest.mark.performance` - Benchmarks

**Environment guard:** `parity`/`gui_parity` tests are gated by an autouse
fixture (`tests/conftest.py` → `src/pob_env.verify()`) that FAILS them — never
skips — if the PoB environment is drifted (fake submodule, HEAD != gitlink,
hand-edited `external/POB_VERSION.txt`, unflagged stale baselines, unapplied
patches). `scripts/run_epic2_validation_isolated.py` runs the same check at
startup (exit 2). Fix: `python scripts/setup_pob.py`.

## Documentation
- Tech specs: `docs/tech-spec-epic-1.md`, `docs/tech-spec-epic-2.md`
- Architecture: `docs/solution-architecture.md`
- ADRs: `docs/decisions/ADR-*.md`
- Stories: `docs/stories/`
