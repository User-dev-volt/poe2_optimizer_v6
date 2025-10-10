# Solution Architecture: PoE 2 Passive Tree Optimizer - Detailed Technical Specification

**Project:** poe2_optimizer_v6
**Author:** Winston (System Architect)
**Date:** 2025-10-09
**Version:** 1.0 - Comprehensive Architecture

---

## Executive Summary

The **PoE 2 Passive Tree Optimizer** is a local Flask web application that automates the optimization of Path of Exile 2 passive skill trees using headless Path of Building calculations. The system discovers mathematically superior tree configurations through a hill climbing algorithm, delivering 5-15% performance improvements in under 5 minutes.

**Core Architecture:** Modular monolith with clean separation between PoB calculation engine integration, optimization algorithm, and web interface. Python 3.10+ backend with embedded LuaJIT via Lupa library for in-process PoB calculations. Server-side rendering with Bootstrap 5 for user-friendly progress visualization.

**Deployment Model:** Local-only (localhost:5000) for MVP validation phase. Zero external dependencies, no cloud services, no database—pure in-memory session state with file-based logging.

**Key Innovation:** In-process Lua integration achieves 150-500ms batch calculation performance (1000 calculations) enabling practical passive tree optimization that would take humans 3+ hours to explore manually.

---

## 1. Technology Stack and Library Decisions

### 1.1 Complete Technology Table with Specific Versions

| Category | Technology | Version | Justification |
|----------|------------|---------|-----------|
| **Backend Framework** | Flask | 3.0.0 | Lightweight Python web framework perfect for local MVP. Simple request/response model, easy to understand for beginners. Supports background threading and Server-Sent Events without async complexity. Widely documented, mature ecosystem. |
| **Programming Language** | Python | 3.10+ | Required for Lupa library compatibility (LuaJIT bindings). Strong standard library (threading, zlib, base64). Type hints support for maintainability. Excellent for algorithm development and data processing. |
| **Lua Integration** | Lupa | 2.0 | Provides LuaJIT bindings for Python, enabling in-process execution of PoB's Lua calculation engine. Critical for performance (<100ms per calculation). No subprocess overhead, shared memory space. |
| **Template Engine** | Jinja2 | 3.1.2 | Built into Flask. Server-side HTML rendering with template inheritance, filters, and control structures. Familiar Django-like syntax. Enables reusable components (base.html, macros). |
| **Frontend Styling** | Bootstrap | 5.3.2 (CDN) | Professional UI components out of the box. Built-in progress bars, spinners, alerts perfect for optimization progress display. WCAG 2.1 AA accessible by default. No build step (CDN), no npm complexity. Grid system for responsive layouts. |
| **Frontend JavaScript** | Vanilla JavaScript | ES2020+ | Minimal JavaScript needs: SSE connection for progress updates, form validation, loading states. No framework overhead. Modern browser features (EventSource API, fetch, async/await) sufficient. |
| **XML Parsing** | xmltodict | 0.13.0 | Converts PoB's XML format to Python dicts for easy manipulation. Simple API: `xmltodict.parse(xml_string)`. Handles Base64 → zlib → XML pipeline. |
| **HTTP Server** | Werkzeug | 3.0.1 | Flask's underlying WSGI server. Built-in development server perfect for local MVP. Supports threading for concurrent requests. Automatic reloader for development. |
| **Testing Framework** | pytest | 7.4.3 | De facto Python testing standard. Fixtures for test setup, parametrize for multiple test cases, coverage reporting. Simple assert syntax. Plugins for Flask testing (pytest-flask). |
| **Type Checking** | mypy | 1.7.1 | Static type analysis for Python. Catches bugs before runtime. Enforces type hints across codebase. Configured in strict mode for maximum safety. |
| **Code Formatting** | black | 23.11.0 | Opinionated code formatter. Zero configuration, deterministic output. Enforces PEP 8 automatically. Consistent style across codebase. |
| **Linting** | ruff | 0.1.6 | Fast Python linter (Rust-based). Replaces flake8, isort, pylint. Catches unused imports, undefined variables, style issues. 10-100x faster than traditional linters. |

---

## 2. Proposed Source Tree

```
poe2_optimizer_v6/
├── src/                                  # Application source code
│   ├── __init__.py
│   ├── main.py                          # Flask app entry point
│   │
│   ├── parsers/                         # FR-1.x: PoB Code Parsing
│   │   ├── __init__.py
│   │   ├── pob_parser.py                # Base64 → zlib → XML → BuildData
│   │   ├── pob_generator.py             # BuildData → XML → zlib → Base64
│   │   ├── xml_utils.py                 # XML parsing helpers
│   │   └── exceptions.py                # PoBParseError, InvalidFormatError
│   │
│   ├── calculator/                      # FR-3.x: PoB Calculation Engine
│   │   ├── __init__.py
│   │   ├── pob_engine.py                # Lupa integration, HeadlessWrapper
│   │   ├── stub_functions.py            # Python stubs (Deflate, Inflate, ConPrintf)
│   │   ├── passive_tree.py              # PassiveTree.lua loader, graph structure
│   │   └── build_calculator.py          # BuildData → BuildStats via PoB
│   │
│   ├── optimizer/                       # FR-4.x: Optimization Algorithm
│   │   ├── __init__.py
│   │   ├── hill_climbing.py             # Hill climbing implementation
│   │   ├── tree_validator.py            # Connectivity validation (BFS)
│   │   ├── neighbor_generator.py        # Generate 1-hop neighbors
│   │   ├── budget_tracker.py            # Dual budget constraint enforcement
│   │   └── convergence.py               # Detect optimization completion
│   │
│   ├── web/                             # Flask web application
│   │   ├── __init__.py
│   │   ├── app.py                       # Flask app factory
│   │   ├── routes.py                    # HTTP routes (/, /optimize, /progress, /results)
│   │   ├── sse.py                       # Server-Sent Events implementation
│   │   ├── session_manager.py           # Session dict, threading.Lock, cleanup
│   │   └── forms.py                     # Flask-WTF forms (optional, for CSRF)
│   │
│   ├── frontend/                        # Static assets and templates
│   │   ├── templates/
│   │   │   ├── base.html                # Base template (Bootstrap CDN, navbar)
│   │   │   ├── index.html               # Home page (form)
│   │   │   ├── progress.html            # Progress page (SSE connection)
│   │   │   ├── results.html             # Results page (before/after comparison)
│   │   │   └── error.html               # Error page (FR-1.3 structured errors)
│   │   │
│   │   └── static/
│   │       ├── css/
│   │       │   └── custom.css           # Custom styles on top of Bootstrap
│   │       ├── js/
│   │       │   ├── progress.js          # SSE connection, progress bar updates
│   │       │   └── copy-code.js         # Copy PoB code to clipboard
│   │       └── img/
│   │           └── favicon.ico
│   │
│   ├── models/                          # Data models (dataclasses)
│   │   ├── __init__.py
│   │   ├── build_data.py                # BuildData, CharacterClass enum
│   │   ├── build_stats.py               # BuildStats (DPS, EHP, resistances)
│   │   └── optimization_config.py       # OptimizationConfig (goal, budgets)
│   │
│   └── utils/                           # Shared utilities
│       ├── __init__.py
│       ├── logging_config.py            # Structured logging setup
│       └── performance.py               # Performance monitoring, timeouts
│
├── external/                            # External dependencies
│   └── pob-engine/                      # Git submodule (Path of Building)
│       ├── HeadlessWrapper.lua
│       ├── src/
│       │   ├── Data/
│       │   │   ├── PassiveTree.lua
│       │   │   └── Classes.lua
│       │   └── Modules/
│       │       └── CalcPerform.lua
│       └── ... (full PoB codebase)
│
├── tests/                               # Test suite (pytest)
│   ├── __init__.py
│   ├── conftest.py                      # Pytest fixtures
│   │
│   ├── unit/                            # Unit tests (isolated modules)
│   │   ├── test_pob_parser.py
│   │   ├── test_pob_generator.py
│   │   ├── test_tree_validator.py
│   │   ├── test_hill_climbing.py
│   │   └── test_budget_tracker.py
│   │
│   ├── integration/                     # Integration tests (module interaction)
│   │   ├── test_pob_engine_integration.py
│   │   ├── test_optimization_pipeline.py
│   │   └── test_session_management.py
│   │
│   └── e2e/                             # End-to-end tests (full workflow)
│       └── test_optimization_workflow.py
│
├── logs/                                # Application logs
│   └── optimizer.log                    # Rotating log file
│
├── docs/                                # Documentation
│   ├── PRD.md                           # Product Requirements Document
│   ├── solution-architecture.md         # This document
│   ├── ADRs/                            # Architecture Decision Records
│   │   ├── ADR-001-flask-over-fastapi.md
│   │   ├── ADR-002-threading-over-asyncio.md
│   │   └── ADR-003-bootstrap-styling.md
│   └── project-workflow-analysis.md
│
├── scripts/                             # Utility scripts
│   ├── setup_pob_submodule.sh           # Initialize Git submodule
│   └── run_tests.sh                     # Test execution script
│
├── .gitignore                           # Git ignore patterns
├── .gitmodules                          # Git submodule config
├── requirements.txt                     # Production dependencies
├── requirements-dev.txt                 # Development dependencies (pytest, mypy, black)
├── pyproject.toml                       # Python project config (black, mypy, ruff)
├── README.md                            # Project overview, setup instructions
├── LICENSE                              # MIT License
└── POB_VERSION.txt                      # Pinned PoB commit hash

```

**Critical Folders Explained:**

- **src/parsers/**: Handles all PoB code encoding/decoding. Isolated module with no dependencies on calculator or optimizer. Can be tested independently with sample PoB codes.

- **src/calculator/**: Bridges Python and Lua (PoB engine). Loads HeadlessWrapper.lua once at startup, caches passive tree graph in memory. All optimization sessions reuse same Lua runtime pool (up to 10 instances for concurrency).

- **src/optimizer/**: Pure algorithm logic. Takes BuildData input, uses calculator for stat calculations, uses passive tree graph for validation. No web/HTTP concerns. Can run standalone for algorithm testing.

- **src/web/**: Flask application layer. Routes, session management, SSE streaming. Orchestrates parsers → calculator → optimizer pipeline. Handles HTTP request/response, progress updates, error rendering.

- **src/frontend/**: All user-facing code. Jinja2 templates for SSR, Bootstrap for styling, minimal JavaScript for interactivity (SSE connection, copy buttons, form validation).

- **external/pob-engine/**: Git submodule tracking official Path of Building repository. Pinned to specific commit (documented in POB_VERSION.txt). Never modified directly—treated as read-only dependency.

- **tests/**: Three-tier testing strategy:
  - Unit tests: Fast, isolated, mock dependencies (e.g., mock PoB engine)
  - Integration tests: Test module interactions (e.g., parser → calculator → optimizer)
  - E2E tests: Full workflow simulation (submit PoB code → get optimized result)

---

## 3. System Architecture Diagrams

### 3.1 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (User)                           │
│  ┌────────────┐  ┌───────────────┐  ┌───────────────────────┐  │
│  │  Form UI   │  │ Progress Page │  │  Results Display      │  │
│  │ (index.html)│  │  (SSE stream) │  │ (before/after compare)│  │
│  └────────────┘  └───────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                     │                      │
         │ HTTP POST           │ HTTP GET (SSE)       │ HTTP GET
         │ /optimize           │ /sse/<session_id>    │ /results/<session_id>
         ↓                     ↓                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Flask Web Server (src/web/)                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Routes (routes.py)                                      │   │
│  │  - POST /optimize → parse, create session, start thread │   │
│  │  - GET /sse/<id> → stream progress updates              │   │
│  │  - GET /results/<id> → render results page              │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Session Manager (session_manager.py)                   │   │
│  │  - sessions: Dict[str, SessionData]                     │   │
│  │  - session_lock: threading.Lock                         │   │
│  │  - Background thread pool (max 10 concurrent)           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │                          │
         │ Parse PoB code           │ Optimize tree (background thread)
         ↓                          ↓
┌──────────────────────┐   ┌────────────────────────────────────┐
│  Parsers Module      │   │  Optimizer Module                  │
│  (src/parsers/)      │   │  (src/optimizer/)                  │
│                      │   │                                    │
│  Base64 → zlib →    │   │  Hill Climbing Algorithm:          │
│  XML → BuildData     │   │  1. Load passive tree graph        │
│                      │   │  2. Calculate baseline stats       │
│                      │   │  3. Loop:                          │
│                      │   │     - Generate neighbor            │
│                      │   │     - Validate connectivity        │
│                      │   │     - Calculate stats              │
│                      │   │     - Keep if improved             │
│                      │   │  4. Convergence check              │
└──────────────────────┘   └────────────────────────────────────┘
                                       │
                                       │ Calculate stats
                                       ↓
                           ┌──────────────────────────────────┐
                           │  Calculator Module               │
                           │  (src/calculator/)               │
                           │                                  │
                           │  PoB Engine (Lupa/LuaJIT):      │
                           │  - Load HeadlessWrapper.lua      │
                           │  - Execute PoB calculations      │
                           │  - Return DPS, EHP, resistances  │
                           │                                  │
                           │  Python Stubs:                   │
                           │  - Deflate/Inflate (zlib)        │
                           │  - ConPrintf (no-op logging)     │
                           └──────────────────────────────────┘
                                       │
                                       │ Read Lua files
                                       ↓
                           ┌──────────────────────────────────┐
                           │  Path of Building Engine         │
                           │  (external/pob-engine/)          │
                           │                                  │
                           │  - HeadlessWrapper.lua           │
                           │  - PassiveTree.lua (tree graph)  │
                           │  - CalcPerform.lua (DPS formulas)│
                           │  - Classes.lua (starting nodes)  │
                           └──────────────────────────────────┘
```

### 3.2 Data Flow: Request to Response

```
User Action: Paste PoB code, select goal, click "Optimize"
    ↓
[1] Browser sends POST /optimize with form data
    ↓
[2] Flask routes.py receives request
    ↓
[3] Validate input size (<100KB, FR-1.1)
    │
    ├─ If >100KB → Render error page
    │
    └─ If valid ↓
    ↓
[4] parsers/pob_parser.py:
    - Base64 decode
    - zlib decompress
    - xmltodict.parse()
    - Extract BuildData (class, level, tree nodes, items, skills)
    │
    ├─ If parse fails → Render structured error (FR-1.3)
    │
    └─ If success ↓
    ↓
[5] Generate session_id (UUID)
    ↓
[6] session_manager.create_optimization_session():
    - Create background thread
    - Store in sessions dict with lock
    - Start thread
    ↓
[7] Return 202 Accepted + redirect to /progress/<session_id>
    ↓
[Browser navigates to /progress/<session_id>]
    ↓
[8] Render progress.html with JavaScript
    ↓
[9] JavaScript establishes SSE connection: GET /sse/<session_id>
    ↓
    ┌─────────────────────────────────────────────────────────┐
    │  Background Thread (Optimization Worker)                │
    │                                                          │
    │  [10] calculator/passive_tree.py:                       │
    │       - Load PassiveTree.lua (if not cached)            │
    │       - Build node graph (adjacency list)               │
    │                                                          │
    │  [11] calculator/build_calculator.py:                   │
    │       - Convert BuildData → Lua tables                  │
    │       - Call pobCalculator.calculateBuild()             │
    │       - Parse results → BuildStats (baseline)           │
    │                                                          │
    │  [12] optimizer/hill_climbing.py:                       │
    │       Loop (max 1000 iterations or convergence):        │
    │         a) optimizer/neighbor_generator.py:             │
    │            - Generate neighbor tree (±1 node)           │
    │         b) optimizer/tree_validator.py:                 │
    │            - BFS connectivity check                     │
    │         c) calculator/build_calculator.py:              │
    │            - Calculate stats for neighbor               │
    │         d) Compare: neighbor vs current_best            │
    │         e) If improved → update current_best            │
    │         f) optimizer/budget_tracker.py:                 │
    │            - Verify budget not exceeded                 │
    │         g) Every 2s or 100 iterations:                  │
    │            - Update session["progress"]                 │
    │            - Update session["message"]                  │
    │                                                          │
    │  [13] Convergence detected (no improvement in 50 iters) │
    │       - Set session["status"] = "complete"              │
    │       - Store optimized BuildData in session["result"]  │
    │                                                          │
    └─────────────────────────────────────────────────────────┘
    ↓ (SSE endpoint streams updates in parallel)
    ↓
[14] web/sse.py streams progress to browser:
     - Every 2s: Send progress update message
     - Format: data: {"status": "running", "progress": 0.42, "message": "..."}
     ↓
[15] JavaScript receives messages, updates progress bar
     ↓
[16] When status="complete", JavaScript redirects to /results/<session_id>
     ↓
[17] routes.py /results handler:
     - Fetch optimized BuildData from session
     - parsers/pob_generator.py:
       * BuildData → XML → zlib compress → Base64 encode
       * Output: New PoB code string
     - Render results.html with:
       * Before/after stats comparison table
       * List of nodes added/removed
       * Copy button for new PoB code
     ↓
[18] User clicks "Copy Code" button
     ↓
[19] JavaScript copies code to clipboard
     ↓
[User pastes into Path of Building → Sees improvements!]
```

---

## 4. Component Details and Integration

### 4.1 PoB Calculation Engine Integration (Epic 1)

**Purpose:** Enable accurate Path of Building calculations in headless Python environment.

**Key Files:**
- `src/calculator/pob_engine.py` - Main integration point
- `src/calculator/stub_functions.py` - Python implementations of Lua dependencies
- `src/calculator/passive_tree.py` - PassiveTree.lua loader and graph structure

**How Lupa Integration Works:**

```python
# src/calculator/pob_engine.py

from lupa import LuaRuntime, LuaError
import os
from pathlib import Path
from typing import Dict, Any

class PoBCalculationEngine:
    """
    Wraps Path of Building's Lua calculation engine using Lupa.

    Singleton pattern: One instance per thread to avoid state conflicts.
    """

    def __init__(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self._initialized = False
        self._pob_path = Path(__file__).parent.parent.parent / "external" / "pob-engine"

    def initialize(self):
        """
        Load HeadlessWrapper.lua and required modules.

        Called once at startup or on first use per thread.
        """
        if self._initialized:
            return

        # Inject Python stub functions into Lua global namespace
        from .stub_functions import create_stubs
        stubs = create_stubs()

        for func_name, func_impl in stubs.items():
            self.lua.globals()[func_name] = func_impl

        # Load HeadlessWrapper.lua
        wrapper_path = self._pob_path / "HeadlessWrapper.lua"
        with open(wrapper_path, 'r', encoding='utf-8') as f:
            wrapper_code = f.read()

        try:
            self.lua.execute(wrapper_code)
        except LuaError as e:
            raise RuntimeError(f"Failed to load HeadlessWrapper.lua: {e}")

        # Verify loadBuildFromXML function exists
        if not self.lua.globals().loadBuildFromXML:
            raise RuntimeError("loadBuildFromXML function not found in HeadlessWrapper")

        self._initialized = True

    def calculate_build(self, build_xml: str) -> Dict[str, Any]:
        """
        Calculate build stats from XML string.

        Args:
            build_xml: PoB build XML (after decompression)

        Returns:
            Dict with keys: totalDPS, totalEHP, life, energyShield, mana, resistances

        Raises:
            LuaError: If PoB calculation fails
        """
        if not self._initialized:
            self.initialize()

        try:
            # Call Lua function: loadBuildFromXML(xmlString)
            build_table = self.lua.globals().loadBuildFromXML(build_xml)

            # Call Lua function: performCalcs(build)
            calc_results = self.lua.globals().performCalcs(build_table)

            # Extract results from Lua table
            stats = {
                "totalDPS": float(calc_results.totalDPS or 0),
                "totalEHP": float(calc_results.totalEHP or 0),
                "life": int(calc_results.life or 0),
                "energyShield": int(calc_results.energyShield or 0),
                "mana": int(calc_results.mana or 0),
                "resistances": {
                    "fire": int(calc_results.fireRes or 0),
                    "cold": int(calc_results.coldRes or 0),
                    "lightning": int(calc_results.lightningRes or 0),
                    "chaos": int(calc_results.chaosRes or 0),
                }
            }

            return stats

        except LuaError as e:
            # Log error with context
            import logging
            logging.error(f"PoB calculation failed: {e}")
            raise


# Thread-local storage for per-thread engine instances
import threading
_thread_local = threading.local()

def get_pob_engine() -> PoBCalculationEngine:
    """
    Get PoB engine for current thread.

    Each optimization thread gets its own engine instance to avoid state conflicts.
    """
    if not hasattr(_thread_local, "pob_engine"):
        _thread_local.pob_engine = PoBCalculationEngine()
        _thread_local.pob_engine.initialize()

    return _thread_local.pob_engine
```

**Python Stub Functions:**

```python
# src/calculator/stub_functions.py

import zlib
import base64
from typing import Dict, Callable

def create_stubs() -> Dict[str, Callable]:
    """
    Create Python implementations of Lua dependencies.

    These functions are called by HeadlessWrapper.lua when it needs
    functionality not available in pure Lua (compression, console output, etc.).
    """

    def Deflate(data: bytes) -> bytes:
        """zlib compression (for PoB code generation)."""
        return zlib.compress(data)

    def Inflate(data: bytes) -> bytes:
        """zlib decompression (for PoB code parsing)."""
        return zlib.decompress(data)

    def ConPrintf(message: str):
        """Console print - logged instead of printed."""
        import logging
        logging.debug(f"[PoB Console] {message}")

    def ConPrintTable(table):
        """Console print table - no-op for headless mode."""
        pass

    def SpawnProcess(*args):
        """Spawn external process - no-op (not needed headless)."""
        pass

    def OpenURL(url: str):
        """Open URL in browser - no-op (not needed headless)."""
        pass

    return {
        "Deflate": Deflate,
        "Inflate": Inflate,
        "ConPrintf": ConPrintf,
        "ConPrintTable": ConPrintTable,
        "SpawnProcess": SpawnProcess,
        "OpenURL": OpenURL,
    }
```

**Why This Design?**

1. **Thread-local engines:** Each optimization thread gets its own `PoBCalculationEngine` instance. Lua state is not thread-safe, so this prevents race conditions.

2. **Lazy initialization:** Engine loads HeadlessWrapper.lua on first use, not at import time. Faster startup, only pays cost if actually calculating.

3. **Stub functions:** Lua can't directly call Python, so we inject Python functions into Lua's global namespace. PoB code calls these when it needs compression, console output, etc.

4. **Error handling:** Wrap Lua calls in try/except. If PoB calculation fails (invalid build, missing data), we catch LuaError and return structured error to user.

### 4.2 Hill Climbing Optimization Algorithm (Epic 2)

**Purpose:** Discover superior passive tree configurations within budget constraints.

**Algorithm Pseudocode:**

```
function HILL_CLIMBING(initial_build, goal, budgets):
    current_build = initial_build
    current_stats = CALCULATE_STATS(current_build)
    current_score = OBJECTIVE_FUNCTION(current_stats, goal)

    iterations = 0
    no_improvement_count = 0
    MAX_NO_IMPROVEMENT = 50  # Convergence threshold

    while iterations < MAX_ITERATIONS and no_improvement_count < MAX_NO_IMPROVEMENT:
        # Generate all valid neighbors (1-hop changes)
        neighbors = []

        # Try adding each unallocated neighbor node
        for node in GET_UNALLOCATED_NEIGHBORS(current_build):
            if BUDGET_ALLOWS_ALLOCATION(node, budgets):
                neighbor = ALLOCATE_NODE(current_build, node)
                if TREE_IS_CONNECTED(neighbor):
                    neighbors.append(neighbor)

        # Try removing each allocated node (if respec budget available)
        if budgets.respec_points > 0:
            for node in current_build.passive_nodes:
                if BUDGET_ALLOWS_DEALLOCATION(node, budgets):
                    neighbor = DEALLOCATE_NODE(current_build, node)
                    if TREE_IS_CONNECTED(neighbor):
                        neighbors.append(neighbor)

        # Try swapping: deallocate 1, allocate 1 different
        # (More complex, implement in V2)

        # Evaluate all neighbors
        best_neighbor = None
        best_neighbor_score = current_score

        for neighbor in neighbors:
            neighbor_stats = CALCULATE_STATS(neighbor)
            neighbor_score = OBJECTIVE_FUNCTION(neighbor_stats, goal)

            if neighbor_score > best_neighbor_score:
                best_neighbor = neighbor
                best_neighbor_score = neighbor_score

        # If found improvement, move to neighbor
        if best_neighbor is not None:
            current_build = best_neighbor
            current_stats = CALCULATE_STATS(current_build)
            current_score = best_neighbor_score
            no_improvement_count = 0
        else:
            # No improvement, increment counter
            no_improvement_count += 1

        iterations += 1

        # Report progress every 100 iterations
        if iterations % 100 == 0:
            REPORT_PROGRESS(iterations, current_score)

    return current_build, current_stats
```

**Objective Function:**

```python
# src/optimizer/objective_function.py

from src.models.build_stats import BuildStats
from src.models.optimization_config import OptimizationGoal

def calculate_objective_score(stats: BuildStats, goal: OptimizationGoal) -> float:
    """
    Calculate objective function score for optimization.

    Higher score = better build for the given goal.
    """

    if goal == OptimizationGoal.MAXIMIZE_DPS:
        return stats.total_dps

    elif goal == OptimizationGoal.MAXIMIZE_EHP:
        return stats.effective_hp

    elif goal == OptimizationGoal.BALANCED:
        # Weighted combination: prioritize DPS, but maintain defense
        dps_weight = 0.7
        ehp_weight = 0.3

        # Normalize to similar scales (DPS often 100k+, EHP often 50k+)
        normalized_dps = stats.total_dps / 100000.0
        normalized_ehp = stats.effective_hp / 50000.0

        return (dps_weight * normalized_dps) + (ehp_weight * normalized_ehp)

    else:
        raise ValueError(f"Unknown optimization goal: {goal}")
```

### 4.3 Progress Reporting with SSE

**Server-Side (Flask):**

```python
# src/web/sse.py

from flask import Response
import json
import time
from typing import Generator

def stream_optimization_progress(session_id: str) -> Response:
    """
    Stream optimization progress via Server-Sent Events.

    Returns:
        Flask Response with text/event-stream mimetype
    """

    def generate() -> Generator[str, None, None]:
        """Generator yields SSE-formatted messages."""

        from .session_manager import get_session, session_lock

        # Check session exists
        with session_lock:
            session = get_session(session_id)
            if not session:
                yield f"data: {json.dumps({'error': 'Session not found'})}\n\n"
                return

        # Stream updates until complete
        last_progress = 0.0

        while True:
            with session_lock:
                session = get_session(session_id)
                if not session:
                    break

                status = session["status"]
                progress = session.get("progress", 0.0)
                message = session.get("message", "")
                iterations = session.get("iterations", 0)
                best_improvement = session.get("best_improvement", 0.0)

            # Only send if progress changed (avoid spam)
            if progress != last_progress or status != "running":
                data = {
                    "status": status,
                    "progress": progress,
                    "message": message,
                    "iterations": iterations,
                    "best_improvement": best_improvement
                }

                yield f"data: {json.dumps(data)}\n\n"
                last_progress = progress

            # Close stream if optimization complete/error
            if status in ["complete", "error", "cancelled"]:
                break

            # Wait 2 seconds before next update (FR-4.4)
            time.sleep(2)

    return Response(generate(), mimetype="text/event-stream")
```

**Client-Side (JavaScript):**

```javascript
// src/frontend/static/js/progress.js

/**
 * Establish SSE connection and update progress bar.
 * Falls back to polling if SSE not supported.
 */
function connectToProgressStream(sessionId) {
    // Check SSE support
    if (typeof(EventSource) === "undefined") {
        console.warn("SSE not supported, falling back to polling");
        pollProgress(sessionId);
        return;
    }

    // Create EventSource connection
    const eventSource = new EventSource(`/sse/${sessionId}`);

    // Handle messages
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);

        // Update progress bar
        updateProgressBar(data.progress);

        // Update status message
        updateStatusMessage(data.message);

        // Update stats display
        if (data.iterations) {
            document.getElementById('iterations').textContent = data.iterations;
        }
        if (data.best_improvement) {
            document.getElementById('improvement').textContent =
                `+${(data.best_improvement * 100).toFixed(1)}%`;
        }

        // Handle completion
        if (data.status === "complete") {
            eventSource.close();
            showSuccessMessage("Optimization complete! Redirecting...");
            setTimeout(() => {
                window.location.href = `/results/${sessionId}`;
            }, 2000);
        }

        // Handle errors
        if (data.status === "error") {
            eventSource.close();
            showErrorMessage(data.message);
        }
    };

    // Handle connection errors
    eventSource.onerror = function(error) {
        console.error("SSE error:", error);
        eventSource.close();

        // Fall back to polling
        console.log("Falling back to polling");
        pollProgress(sessionId);
    };
}

/**
 * Polling fallback if SSE not supported or connection fails.
 */
function pollProgress(sessionId) {
    const pollInterval = 2000; // 2 seconds

    function poll() {
        fetch(`/api/progress/${sessionId}`)
            .then(response => response.json())
            .then(data => {
                updateProgressBar(data.progress);
                updateStatusMessage(data.message);

                if (data.status === "complete") {
                    window.location.href = `/results/${sessionId}`;
                } else if (data.status === "error") {
                    showErrorMessage(data.message);
                } else {
                    // Continue polling
                    setTimeout(poll, pollInterval);
                }
            })
            .catch(error => {
                console.error("Polling error:", error);
                showErrorMessage("Connection lost. Please refresh the page.");
            });
    }

    poll();
}

/**
 * Update Bootstrap progress bar.
 */
function updateProgressBar(progress) {
    const percent = Math.round(progress * 100);
    const progressBar = document.getElementById('progress-bar');

    progressBar.style.width = `${percent}%`;
    progressBar.setAttribute('aria-valuenow', percent);
    progressBar.textContent = `${percent}%`;

    // Change color based on progress
    if (percent < 33) {
        progressBar.className = 'progress-bar bg-info';
    } else if (percent < 66) {
        progressBar.className = 'progress-bar bg-primary';
    } else {
        progressBar.className = 'progress-bar bg-success';
    }
}
```

---

## 5. Testing Strategy

### 5.1 Testing Pyramid

```
                  /\
                 /  \
                /E2E \       10% - Full workflow tests (slow, brittle)
               /______\
              /        \
             /Integration\   30% - Module interaction tests
            /____________\
           /              \
          /  Unit Tests    \  60% - Fast, isolated, mocked dependencies
         /__________________\
```

**Coverage Target:** >80% overall, >90% for critical paths (calculator, optimizer, parsers)

### 5.2 Unit Tests (src/tests/unit/)

**Test Philosophy:** Fast, isolated, no external dependencies. Mock everything.

**Example: Test PoB Parser**

```python
# tests/unit/test_pob_parser.py

import pytest
from src.parsers.pob_parser import parse_pob_code, PoBParseError

def test_parse_valid_pob_code():
    """Test parsing a valid PoB code returns BuildData."""

    # Sample valid PoB code (Base64-encoded)
    pob_code = "eNqVVktv...valid_code...QLMRqgA="

    build_data = parse_pob_code(pob_code)

    assert build_data.level == 90
    assert build_data.character_class == "Witch"
    assert len(build_data.passive_nodes) > 0

def test_parse_invalid_base64():
    """Test invalid Base64 raises PoBParseError."""

    invalid_code = "not-valid-base64!!!"

    with pytest.raises(PoBParseError) as exc_info:
        parse_pob_code(invalid_code)

    assert "Invalid Base64" in str(exc_info.value)

def test_parse_corrupted_xml():
    """Test corrupted XML raises PoBParseError with helpful message."""

    # Valid Base64 but invalid XML inside
    corrupted_code = "eNqVVktv...corrupted...QLMRqgA="

    with pytest.raises(PoBParseError) as exc_info:
        parse_pob_code(corrupted_code)

    assert "Unable to parse XML" in exc_info.value.user_message

def test_parse_oversized_code():
    """Test code >100KB rejected (FR-1.1)."""

    # Generate 101KB of data
    oversized_code = "A" * (101 * 1024)

    with pytest.raises(PoBParseError) as exc_info:
        parse_pob_code(oversized_code)

    assert "too large" in exc_info.value.user_message
```

**Example: Test Tree Validator**

```python
# tests/unit/test_tree_validator.py

import pytest
from src.optimizer.tree_validator import is_tree_connected
from src.calculator.passive_tree import PassiveTreeGraph

@pytest.fixture
def mock_tree_graph():
    """Create a simple mock tree for testing."""

    graph = PassiveTreeGraph()

    # Simple linear tree: Start → 1 → 2 → 3
    graph.nodes = {
        0: MockNode(out_connections=[1]),  # Start node
        1: MockNode(out_connections=[0, 2]),
        2: MockNode(out_connections=[1, 3]),
        3: MockNode(out_connections=[2]),
    }
    graph.starting_nodes = {"TestClass": 0}

    return graph

def test_connected_tree_valid(mock_tree_graph):
    """Test connected tree returns True."""

    allocated_nodes = {0, 1, 2}  # Start → 1 → 2
    starting_class = "TestClass"

    result = is_tree_connected(allocated_nodes, starting_class, mock_tree_graph)

    assert result is True

def test_disconnected_tree_invalid(mock_tree_graph):
    """Test disconnected tree returns False."""

    allocated_nodes = {0, 3}  # Start + isolated node 3 (not connected!)
    starting_class = "TestClass"

    result = is_tree_connected(allocated_nodes, starting_class, mock_tree_graph)

    assert result is False

def test_empty_tree_valid(mock_tree_graph):
    """Test tree with only starting node is valid."""

    allocated_nodes = {0}  # Just start
    starting_class = "TestClass"

    result = is_tree_connected(allocated_nodes, starting_class, mock_tree_graph)

    assert result is True
```

### 5.3 Integration Tests (src/tests/integration/)

**Test Philosophy:** Test module interactions with real dependencies (not mocked).

**Example: PoB Engine Integration Test**

```python
# tests/integration/test_pob_engine_integration.py

import pytest
from src.calculator.pob_engine import get_pob_engine
from src.parsers.pob_parser import parse_pob_code

@pytest.mark.slow  # Mark as slow test (skipped in quick runs)
def test_pob_calculation_accuracy():
    """
    Test PoB engine calculates stats matching official PoB GUI.

    Requires: external/pob-engine/ submodule initialized.
    """

    # Load a known build (from fixtures/sample-builds/)
    with open("tests/fixtures/sample_warrior_build.txt") as f:
        pob_code = f.read().strip()

    build_data = parse_pob_code(pob_code)

    # Get PoB engine and calculate
    engine = get_pob_engine()
    stats = engine.calculate_build_stats(build_data)

    # Expected values (verified in PoB GUI)
    assert abs(stats.total_dps - 125430) < 100  # Within 0.1%
    assert abs(stats.effective_hp - 42150) < 100
    assert stats.life == 4500
    assert stats.resistances["fire"] == 75

def test_batch_calculation_performance():
    """
    Test batch calculation meets performance target (FR-3.3).

    Target: 1000 calculations in <1 second (150-500ms).
    """

    import time
    from src.parsers.pob_parser import parse_pob_code

    # Load sample build
    with open("tests/fixtures/sample_warrior_build.txt") as f:
        pob_code = f.read().strip()

    build_data = parse_pob_code(pob_code)

    engine = get_pob_engine()

    # Warm-up (first calculation slower due to Lua JIT compilation)
    engine.calculate_build_stats(build_data)

    # Time 1000 calculations
    start_time = time.time()

    for _ in range(1000):
        engine.calculate_build_stats(build_data)

    elapsed_ms = (time.time() - start_time) * 1000

    # Assert performance target met
    assert elapsed_ms < 1000, f"1000 calculations took {elapsed_ms:.0f}ms (target: <1000ms)"

    print(f"Performance: {elapsed_ms:.0f}ms for 1000 calculations ({elapsed_ms/1000:.2f}ms per calc)")
```

### 5.4 End-to-End Tests (src/tests/e2e/)

**Test Philosophy:** Test complete user workflows in a simulated environment.

```python
# tests/e2e/test_optimization_workflow.py

import pytest
from flask import Flask
from src.web.app import create_app
import time

@pytest.fixture
def client():
    """Create Flask test client."""

    app = create_app(testing=True)
    with app.test_client() as client:
        yield client

def test_full_optimization_workflow(client):
    """
    Test complete workflow: submit PoB code → optimize → get results.

    This is the primary E2E test validating the entire system.
    """

    # Load sample PoB code
    with open("tests/fixtures/sample_warrior_build.txt") as f:
        pob_code = f.read().strip()

    # [1] Submit optimization request
    response = client.post('/optimize', data={
        'pob_code': pob_code,
        'goal': 'maximize_dps',
        'unallocated_points': 10,
        'respec_points': 5
    }, follow_redirects=False)

    # Should redirect to progress page
    assert response.status_code == 302
    assert '/progress/' in response.location

    # Extract session_id from redirect URL
    session_id = response.location.split('/')[-1]

    # [2] Poll progress until complete (simulating SSE)
    max_wait = 60  # 1 minute timeout
    start_time = time.time()

    while time.time() - start_time < max_wait:
        response = client.get(f'/api/progress/{session_id}')
        data = response.get_json()

        if data['status'] == 'complete':
            break

        if data['status'] == 'error':
            pytest.fail(f"Optimization failed: {data['message']}")

        time.sleep(2)
    else:
        pytest.fail("Optimization timed out after 60 seconds")

    # [3] Fetch results
    response = client.get(f'/results/{session_id}')
    assert response.status_code == 200

    # Parse HTML to verify results displayed
    html = response.data.decode()
    assert "Optimization Complete" in html
    assert "DPS Improvement" in html
    assert "New PoB Code" in html

    # [4] Verify new PoB code is valid
    # (Extract from HTML, parse, verify it's valid)
    # Implementation: Use BeautifulSoup to extract code from HTML
    # Then parse with pob_parser and verify no errors
```

### 5.5 Running Tests

```bash
# Run all tests
pytest

# Run only unit tests (fast)
pytest tests/unit/

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_pob_parser.py

# Run tests matching pattern
pytest -k "test_parse"

# Run with verbose output
pytest -v

# Skip slow tests (integration/E2E)
pytest -m "not slow"
```

**Coverage Configuration** (pyproject.toml):

```toml
[tool.pytest.ini_options]
minversion = "7.0"
addopts = "--strict-markers --tb=short"
testpaths = ["tests"]
markers = [
    "slow: marks tests as slow (integration/E2E)",
    "unit: fast unit tests",
]

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/conftest.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

---

## 6. DevOps and Local Development

### 6.1 Local Setup Instructions

**Prerequisites:**
- Python 3.10 or higher
- Git 2.40+
- Modern browser (Chrome 90+, Firefox 88+)

**Setup Steps:**

```bash
# 1. Clone repository
git clone https://github.com/yourusername/poe2_optimizer_v6.git
cd poe2_optimizer_v6

# 2. Initialize Git submodule (Path of Building engine)
git submodule init
git submodule update

# 3. Verify PoB submodule loaded
ls external/pob-engine/HeadlessWrapper.lua  # Should exist

# 4. Create Python virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 5. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development tools

# 6. Verify installation
python -c "import lupa; print('Lupa version:', lupa.LuaRuntime().lua_version)"

# 7. Run tests to verify setup
pytest tests/unit/  # Should pass

# 8. Start application
python src/main.py

# Should see:
#  * Running on http://127.0.0.1:5000
#  * Press CTRL+C to quit
```

**Open browser:**
Navigate to `http://localhost:5000`

### 6.2 Development Workflow

```bash
# Terminal 1: Run application with auto-reload
python src/main.py

# Terminal 2: Run tests in watch mode
pytest-watch tests/

# Terminal 3: Code formatting and linting
black src/ tests/  # Format code
ruff check src/    # Lint and fix issues
mypy src/          # Type check
```

### 6.3 Logging Configuration

**Log Levels:**
- DEBUG: Detailed PoB engine calls, algorithm iterations
- INFO: Optimization started/completed, session created
- WARNING: Parse errors, calculation timeouts
- ERROR: Unexpected failures, Lua errors

**Log Location:** `logs/optimizer.log`

**Log Format:**
```
2025-10-09 14:32:15,123 [INFO] session_manager.py:45 - Created optimization session: abc-123
2025-10-09 14:32:15,456 [DEBUG] pob_engine.py:78 - Calculating stats for build (level 90, Witch)
2025-10-09 14:32:15,567 [DEBUG] pob_engine.py:92 - Calculation result: DPS=125430, EHP=42150
2025-10-09 14:32:15,789 [INFO] hill_climbing.py:123 - Iteration 100: +8.2% DPS improvement found
2025-10-09 14:33:42,012 [INFO] hill_climbing.py:234 - Optimization complete: final improvement +12.5% DPS
```

---

## 7. Security Considerations (Local Deployment)

### 7.1 Input Validation

**PoB Code Validation:**
- Size limit: 100KB (FR-1.1)
- Format validation: Must be valid Base64
- Content validation: Must decompress to valid XML
- Sanitization: Escape HTML in error messages (prevent XSS)

**Form Input Validation:**
- Goal: Must be one of ["maximize_dps", "maximize_ehp", "balanced"]
- Unallocated points: Integer, 0-120 range
- Respec points: Integer, 0-1000 range (reasonable upper bound)

### 7.2 Dependency Security

**Automated Scanning:**

```bash
# Check for known vulnerabilities
pip-audit

# Update vulnerable dependencies
pip install --upgrade package-name
```

**Pinned Versions:**
All dependencies in `requirements.txt` use exact versions (`==`) to prevent unexpected updates.

### 7.3 Local-Only Security

**Network Binding:**
Flask configured to bind to `127.0.0.1` only (localhost), not `0.0.0.0` (all interfaces).

```python
# src/main.py

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",  # Localhost only, not accessible from network
        port=5000,
        debug=False,  # Debug mode disabled (prevents code execution exploits)
        threaded=True   # Enable threading for concurrent requests
    )
```

**Data Privacy:**
- No permanent storage of PoB codes
- Session data cleared after 15 minutes
- No external analytics or tracking
- No network requests to third parties

---

## 8. Performance Optimization

### 8.1 Passive Tree Graph Caching

**Strategy:** Load once at startup, keep in memory, share across all sessions.

**Memory Trade-off:**
- Loading PassiveTree.lua takes ~2 seconds
- Cached graph uses ~300KB RAM
- Trade-off: 300KB RAM for 2-second speedup per optimization = worth it

### 8.2 Lua Runtime Pooling

**Strategy:** Maintain pool of pre-initialized Lua runtimes (one per thread).

**Why?**
- Creating new LuaRuntime + loading HeadlessWrapper = ~1 second overhead
- Reusing runtime across calculations = 0 overhead
- Pool size = max 10 (concurrent optimization limit)

### 8.3 Calculation Batching

**Optimization:** Hill climbing makes 1000+ stat calculations. Batch where possible.

**Current:** Calculate one tree configuration at a time
**Future V2:** Batch 10 configurations into single Lua call (10x speedup potential)

---

## 9. Future Enhancements (Post-MVP)

### 9.1 Deferred to V2

**Algorithm Improvements:**
- Simulated annealing layer (better global optima)
- Multi-start hill climbing (try multiple initial states)
- Genetic algorithm exploration

**UI Enhancements:**
- Tree visualization (d3.js interactive graph)
- Comparison mode (compare multiple optimizations)
- History tracking (save past optimizations)

**Infrastructure:**
- Docker containerization
- Cloud deployment (AWS/Vercel)
- Horizontal scaling (Redis for session state)
- Database for analytics (PostgreSQL)

### 9.2 Explicitly Out of Scope

- AI chat features
- Item optimization
- Skill gem suggestions
- Full build generation
- Crafting recommendations

**Why excluded:** Ruthless scope discipline. Do ONE thing perfectly.

---

## 10. Architecture Decision Records (ADRs)

### ADR-001: Flask over FastAPI

**Date:** 2025-10-09
**Status:** Accepted

**Context:**
Need web framework for local MVP. Options: Flask, FastAPI, Django.

**Decision:**
Use Flask 3.0.

**Rationale:**
- Simplicity: Minimal boilerplate, easy to understand
- Synchronous model: Matches Lupa's blocking Lua calls
- Mature ecosystem: Extensive documentation, large community
- Threading support: Built-in for concurrent requests
- SSE support: Possible with generators

**Alternatives Considered:**
- FastAPI: Requires async/await (complicates Lupa integration), over-engineering for local MVP
- Django: Too heavyweight, includes unused features (ORM, admin, auth)

**Consequences:**
- Simpler codebase, faster development
- Limited async capabilities (acceptable for local use)
- May need migration if scaling to thousands of concurrent users (V2 concern)

---

### ADR-002: Bootstrap 5 for Styling

**Date:** 2025-10-09
**Status:** Accepted

**Context:**
Need clean, professional UI with progress visualization and accessibility.

**Decision:**
Use Bootstrap 5 via CDN.

**Rationale:**
- Time savings: Professional components out-of-the-box
- Accessibility: WCAG 2.1 AA compliance by default (FR-1.7 requirement)
- Progress UI: Built-in progress bars, spinners, alerts
- No build step: Include via CDN (simpler than npm + webpack)
- Responsive: Grid system handles different screen sizes

**Alternatives Considered:**
- Tailwind CSS: Utility-first approach, but requires build step (npm, PostCSS)
- Plain CSS: Maximum control, but weeks of development time for progress bars, responsive grid
- Material-UI: React-based, requires SPA (over-engineering)

**Consequences:**
- Larger initial page load (~200KB CSS from CDN), acceptable for local
- Less customization flexibility (Bootstrap look-and-feel)
- Easy for beginners to understand and modify

---

### ADR-003: Server-Sent Events (SSE) for Progress

**Date:** 2025-10-09
**Status:** Accepted

**Context:**
Need real-time progress updates during optimization (FR-4.4). Options: SSE, WebSockets, polling.

**Decision:**
Use SSE with polling fallback.

**Rationale:**
- SSE perfect for one-way server→client streaming
- Built into browsers (EventSource API)
- Simpler than WebSockets (no bidirectional communication needed)
- Automatic reconnection on disconnect
- HTTP/1.1 compatible (no HTTP/2 requirement)

**Alternatives Considered:**
- WebSockets: Bidirectional, but we only need server→client. More complex setup.
- Polling: Simpler, but higher overhead (client requests every 2s). Used as fallback only.

**Consequences:**
- Efficient real-time updates
- One persistent connection per optimization (acceptable for 10 concurrent users)
- Fallback ensures compatibility with all browsers

---

## 11. Implementation Timeline

### Epic 1: PoB Calculation Engine Integration (Weeks 1-2)

**Week 1:**
- Set up repository structure
- Initialize PoB submodule
- Implement Base64 → zlib → XML parsing
- Write unit tests for parser

**Week 2:**
- Lupa integration: Load HeadlessWrapper.lua
- Implement Python stub functions
- Test single build calculation
- Verify accuracy against PoB GUI (±0.1%)
- Batch performance optimization

**Deliverable:** Can parse PoB code and calculate stats with 100% accuracy

---

### Epic 2: Core Optimization Engine (Weeks 3-4)

**Week 3:**
- Load passive tree graph (PassiveTree.lua)
- Implement tree connectivity validation (BFS)
- Implement neighbor generation logic
- Write unit tests for tree validator

**Week 4:**
- Implement hill climbing algorithm
- Dual budget constraint tracking
- Convergence detection
- Integration tests: Full optimization pipeline

**Deliverable:** Optimization algorithm produces improved builds within budget

---

### Epic 3: User Experience & Reliability (Weeks 5-6)

**Week 5:**
- Flask application structure
- HTML templates (Bootstrap 5)
- Form submission → session creation → background thread
- SSE progress streaming
- Results page with before/after comparison

**Week 6:**
- Error handling (FR-1.3 structured errors)
- Session timeout and cleanup
- Optimization cancellation
- File-based logging
- E2E testing

**Deliverable:** Complete local web application, ready for personal use

---

### Weeks 7-8: Polish and Validation

- Run 50+ test optimizations with personal builds
- Fix bugs discovered during testing
- Performance tuning (if needed)
- Documentation updates
- Optional: Package as executable (PyInstaller)

---

## 12. Success Metrics

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Calculation Accuracy** | ±0.1% vs PoB GUI | Integration tests with known builds |
| **Batch Performance** | <1s for 1000 calculations | Performance benchmarks |
| **Optimization Quality** | 8%+ median improvement | Test on 20+ sample builds |
| **Valid Tree Rate** | 100% importable to PoB | Round-trip validation tests |
| **Test Coverage** | >80% overall | pytest --cov report |
| **Startup Time** | <5 seconds | Time from `python main.py` to ready |
| **Memory Usage** | <1GB for 10 concurrent sessions | Memory profiling |

### User Experience Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Parse Success Rate** | 95%+ for valid codes | Error rate tracking |
| **Completion Rate** | 95%+ optimizations complete | Success vs timeout/error ratio |
| **Optimization Time** | <5 min for complex builds | Timing logs |
| **First-Time Usability** | Complete workflow without docs | Personal testing |

---

## 13. Glossary

**Terms for Beginners:**

- **Base64:** Encoding scheme converting binary data to text (ASCII). PoB codes use this.
- **zlib:** Compression library. Makes PoB codes smaller (reduces file size).
- **XML:** eXtensible Markup Language. PoB stores build data in XML format.
- **Flask:** Python web framework. Handles HTTP requests, renders HTML.
- **Jinja2:** Template engine for Flask. Lets you embed Python in HTML.
- **SSE (Server-Sent Events):** Protocol for server→client streaming over HTTP.
- **Threading:** Running multiple tasks concurrently in same process.
- **LuaJIT:** Just-In-Time compiler for Lua. Makes Lua code run fast.
- **Lupa:** Python library providing LuaJIT bindings (lets Python call Lua).
- **Hill Climbing:** Optimization algorithm that incrementally improves solutions.
- **Monolith:** Single application (opposite of microservices).
- **Modular:** Code organized into separate modules with clear responsibilities.
- **Git Submodule:** Way to include one Git repository inside another.

---

_End of Comprehensive Solution Architecture Document_

---

**Next Steps:**

1. Review this architecture document
2. Set up development environment (follow Setup Instructions in Section 6.1)
3. Initialize PoB submodule: `git submodule init && git submodule update`
4. Start Epic 1 implementation (PoB Calculation Engine Integration)
5. Run tests frequently to ensure accuracy
6. Refer back to this document for design decisions and rationale

**Questions or Need Clarification?**

This document is your comprehensive guide. If anything is unclear, revisit the relevant section. Each design decision includes detailed rationale for beginners.

**Remember:** Build incrementally, test frequently, validate accuracy. PoB calculation accuracy is non-negotiable—verify every step against official PoB GUI.

Good luck with your MVP development! 🚀
