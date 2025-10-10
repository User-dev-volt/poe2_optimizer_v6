# Technical Specifications - Implementation Guide

**Project:** poe2_optimizer_v6
**Date:** 2025-10-10
**Purpose:** Consolidated technical specifications for all 3 epics

---

## Overview

This document provides implementation-ready technical specifications for all three epics. Each epic has detailed component breakdowns, API contracts, data models, and testing requirements.

**Related Documents:**
- `solution-architecture-complete.md` - High-level architecture
- `epic-alignment-matrix.md` - Epic-to-component mapping
- `cohesion-check-report.md` - Requirements coverage validation
- `implementation-guide.md` - Beginner-friendly walkthrough

---

## Epic 1: PoB Calculation Engine Integration (Weeks 1-2)

### Goal
Enable accurate PoB calculations in headless Python environment with 100% accuracy (±0.1%) and high performance (<100ms/calculation).

### Components to Implement

#### 1. **parsers/pob_parser.py**

**Purpose:** Parse PoB codes (Base64 → zlib → XML → BuildData)

**Dependencies:** xmltodict 0.13.0, base64 (stdlib), zlib (stdlib)

**API Contract:**
```python
def parse_pob_code(code: str) -> BuildData:
    """
    Parse Path of Building import code to structured BuildData.

    Args:
        code: Base64-encoded PoB code string (max 100KB)

    Returns:
        BuildData object with parsed build information

    Raises:
        PoBParseError: If code is invalid, corrupted, or oversized

    Example:
        >>> code = "eNqVVktv..."
        >>> build = parse_pob_code(code)
        >>> print(build.character_class, build.level)
        CharacterClass.WITCH 90
    """
```

**Implementation Steps:**
1. Validate input size (<100KB)
2. Decode Base64 → bytes
3. Decompress with zlib → XML string
4. Parse XML with xmltodict → dict
5. Extract BuildData fields:
   - character_class (from XML: `<Build>/<PlayerStat class="...">`)
   - level (from XML: `<Build>/<Level>`)
   - passive_nodes (from XML: `<Tree>/<Spec nodes="...">`)
   - items, skills, config (from respective XML sections)
6. Return BuildData object

**Error Handling:**
- Invalid Base64 → `PoBParseError("Invalid Base64 encoding")`
- Corrupt zlib → `PoBParseError("Failed to decompress (corrupted data)")`
- Invalid XML → `PoBParseError("Unable to parse XML structure")`
- Oversized (>100KB) → `PoBParseError("PoB code too large (X KB). Maximum: 100KB")`

**Testing:**
- Unit tests with 10+ sample PoB codes (valid, invalid, edge cases)
- Test all error conditions
- Verify parsing accuracy (manually compare with PoB GUI)

---

#### 2. **parsers/pob_generator.py**

**Purpose:** Generate PoB codes (BuildData → XML → zlib → Base64)

**API Contract:**
```python
def generate_pob_code(build: BuildData) -> str:
    """
    Generate Path of Building import code from BuildData.

    Args:
        build: BuildData object with complete build information

    Returns:
        Base64-encoded PoB code string

    Raises:
        PoBGenerateError: If XML generation fails

    Example:
        >>> optimized_build = BuildData(...)
        >>> code = generate_pob_code(optimized_build)
        >>> print(len(code))
        52341  # Base64 string length
    """
```

**Implementation Steps:**
1. Deep copy original XML structure (preserve non-tree data)
2. Modify ONLY <Tree> section with new passive_nodes
3. Convert dict → XML string (xmltodict.unparse)
4. Compress with zlib (level 9, same as PoB)
5. Encode to Base64 → string
6. Round-trip validation (parse generated code, verify stats match)

**Testing:**
- Round-trip tests: parse → generate → parse (should equal original)
- Verify only <Tree> section modified
- Integration test: Import generated code into PoB GUI (should work 100%)

---

#### 3. **calculator/pob_engine.py**

**Purpose:** Integrate PoB calculation engine via Lupa (LuaJIT bindings)

**Dependencies:** Lupa 2.0, external/pob-engine/ (Git submodule)

**API Contract:**
```python
class PoBCalculationEngine:
    """
    Wraps Path of Building Lua calculation engine.

    Thread-local singleton: One instance per thread for session isolation.
    """

    def initialize(self) -> None:
        """Load HeadlessWrapper.lua and inject Python stubs."""

    def calculate_build_stats(self, build: BuildData) -> BuildStats:
        """
        Calculate stats for a build configuration.

        Args:
            build: BuildData with passive tree, items, skills, config

        Returns:
            BuildStats with DPS, EHP, resistances, life, ES, mana

        Raises:
            LuaError: If PoB calculation fails
            TimeoutError: If calculation exceeds 5 seconds
        """

def get_pob_engine() -> PoBCalculationEngine:
    """
    Get thread-local PoB engine instance.

    Each optimization thread gets its own engine to prevent state conflicts.
    """
```

**Implementation Steps:**
1. Create LuaRuntime instance
2. Inject Python stub functions into Lua global namespace:
   - `Deflate(data) -> bytes` (using zlib.compress)
   - `Inflate(data) -> bytes` (using zlib.decompress)
   - `ConPrintf(message)` (log to Python logging)
   - `SpawnProcess()`, `OpenURL()` (no-ops)
3. Load HeadlessWrapper.lua via `lua.execute(wrapper_code)`
4. Verify `lua.globals().loadBuildFromXML` exists
5. For each calculation:
   - Convert BuildData → XML string
   - Call `loadBuildFromXML(xml)` → Lua build table
   - Call `performCalcs(build)` → Lua results table
   - Extract: totalDPS, totalEHP, life, ES, mana, resistances
   - Return BuildStats object

**Performance Optimizations:**
- Lazy initialization (load on first use)
- Thread-local storage (one engine per thread)
- Cache passive tree graph in memory (avoid repeated file reads)
- LuaJIT compilation (first call slower, subsequent calls fast)

**Error Handling:**
- Wrap all Lua calls in try/except LuaError
- 5-second timeout per calculation
- Log all errors with context

**Testing:**
- Integration tests with real PoB engine
- Accuracy tests: Compare with PoB GUI (±0.1% tolerance)
- Performance tests: 1000 calculations <1s
- Concurrent tests: 10 threads simultaneously

---

#### 4. **calculator/stub_functions.py**

**Purpose:** Provide Python implementations for Lua dependencies

**Implementation:**
```python
import zlib
import logging

def create_stubs() -> Dict[str, Callable]:
    """Create Python stubs for Lua."""

    def Deflate(data: bytes) -> bytes:
        return zlib.compress(data)

    def Inflate(data: bytes) -> bytes:
        return zlib.decompress(data)

    def ConPrintf(message: str):
        logging.debug(f"[PoB] {message}")

    def ConPrintTable(table):
        pass  # No-op

    def SpawnProcess(*args):
        pass  # No-op

    def OpenURL(url: str):
        pass  # No-op

    return {
        "Deflate": Deflate,
        "Inflate": Inflate,
        "ConPrintf": ConPrintf,
        "ConPrintTable": ConPrintTable,
        "SpawnProcess": SpawnProcess,
        "OpenURL": OpenURL,
    }
```

---

#### 5. **models/build_data.py**

**Purpose:** Data model for PoB builds

```python
from dataclasses import dataclass
from typing import Optional, Set, List
from enum import Enum

class CharacterClass(Enum):
    WITCH = "Witch"
    WARRIOR = "Warrior"
    RANGER = "Ranger"
    DUELIST = "Duelist"
    TEMPLAR = "Templar"
    SHADOW = "Shadow"

@dataclass
class BuildData:
    """Structured representation of a PoB build."""
    character_class: CharacterClass
    level: int  # 1-100
    ascendancy: Optional[str] = None  # e.g., "Elementalist"
    passive_nodes: Set[int] = field(default_factory=set)
    # items, skills, config omitted for brevity
    tree_version: str = "3_27"  # PoE 2 tree version
```

---

#### 6. **models/build_stats.py**

**Purpose:** Data model for calculated build statistics

```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class BuildStats:
    """Calculated statistics for a build."""
    total_dps: float
    effective_hp: float
    life: int
    energy_shield: int
    mana: int
    resistances: Dict[str, int]  # fire, cold, lightning, chaos

    armour: int = 0
    evasion: int = 0
    block_chance: float = 0.0
```

---

### Epic 1 Testing Strategy

**Unit Tests (tests/unit/):**
- `test_pob_parser.py` - Parse valid/invalid codes, error handling
- `test_pob_generator.py` - Generate codes, round-trip validation

**Integration Tests (tests/integration/):**
- `test_pob_engine_integration.py` - Real PoB calculations, accuracy validation
- `test_batch_performance.py` - Performance testing (1000 calcs <1s)

**Acceptance Criteria:**
- ✅ 100 sample builds calculated with 100% success rate
- ✅ <100ms per calculation (single)
- ✅ 150-500ms for 1000 calculations (batch)
- ✅ ±0.1% accuracy vs PoB GUI

---

## Epic 2: Core Optimization Engine (Weeks 3-4)

### Goal
Implement hill climbing algorithm achieving 8%+ median improvement with 100% valid tree outputs.

### Components to Implement

#### 1. **optimizer/hill_climbing.py**

**Purpose:** Main optimization algorithm

**API Contract:**
```python
class HillClimbingOptimizer:
    """Hill climbing algorithm for passive tree optimization."""

    def optimize(
        self,
        initial_build: BuildData,
        goal: OptimizationGoal,
        budgets: BudgetConstraints,
        progress_callback: Optional[Callable] = None
    ) -> OptimizedResult:
        """
        Optimize passive tree using hill climbing.

        Args:
            initial_build: Starting build configuration
            goal: MAXIMIZE_DPS, MAXIMIZE_EHP, or BALANCED
            budgets: Unallocated points + respec points
            progress_callback: Called every 100 iterations with progress

        Returns:
            OptimizedResult with improved build, stats, and metrics
        """
```

**Algorithm:**
```
1. current_build = initial_build
2. current_stats = calculate_stats(current_build)
3. current_score = objective_function(current_stats, goal)

4. Loop (max 1000 iterations):
   a. neighbors = generate_all_neighbors(current_build, budgets)
   b. For each neighbor:
      - Validate tree connectivity (BFS)
      - Calculate stats
      - Calculate score
   c. best_neighbor = neighbor with highest score
   d. If best_neighbor_score > current_score:
      - current_build = best_neighbor
      - current_score = best_neighbor_score
      - no_improvement_count = 0
   e. Else:
      - no_improvement_count += 1
   f. If no_improvement_count >= 50:
      - CONVERGE (local optimum found)
   g. Every 100 iterations:
      - Call progress_callback(current_iteration, current_score)

5. Return OptimizedResult(current_build, current_stats, improvement%)
```

**Objective Functions:**
- MAXIMIZE_DPS: `score = total_dps`
- MAXIMIZE_EHP: `score = effective_hp`
- BALANCED: `score = 0.7 * (dps/100k) + 0.3 * (ehp/50k)`

---

#### 2. **optimizer/tree_validator.py**

**Purpose:** Validate passive tree connectivity using BFS

**API Contract:**
```python
def is_tree_connected(
    allocated_nodes: Set[int],
    character_class: CharacterClass,
    tree_graph: PassiveTreeGraph
) -> bool:
    """
    Validate all allocated nodes are connected to class starting node.

    Uses Breadth-First Search (BFS) to verify connectivity.

    Returns:
        True if tree is valid (all nodes reachable from start)
        False if tree has disconnected nodes
    """
```

**Implementation:**
```
1. starting_node = tree_graph.get_starting_node(character_class)
2. visited = {starting_node}
3. queue = [starting_node]

4. While queue not empty:
   current = queue.pop(0)
   neighbors = tree_graph.get_neighbors(current)
   For each neighbor in neighbors:
      If neighbor in allocated_nodes AND neighbor not in visited:
         visited.add(neighbor)
         queue.append(neighbor)

5. Return visited == allocated_nodes
```

---

#### 3. **optimizer/neighbor_generator.py**

**Purpose:** Generate candidate trees (±1 node changes)

**API Contract:**
```python
def generate_neighbors(
    current_build: BuildData,
    budgets: BudgetConstraints,
    tree_graph: PassiveTreeGraph
) -> List[BuildData]:
    """
    Generate all valid 1-hop neighbors within budget constraints.

    Returns:
        List of candidate BuildData objects (modified trees)
    """
```

**Strategy:**
1. **Add nodes** (if unallocated_points > 0):
   - Find all unallocated nodes adjacent to allocated nodes
   - For each: Create new BuildData with node added
2. **Remove nodes** (if respec_points > 0):
   - For each allocated node: Create new BuildData with node removed
3. **Swap nodes** (if respec_points > 0):
   - Deallocate 1 node, allocate 1 different node

---

#### 4. **optimizer/budget_tracker.py**

**Purpose:** Track and enforce dual budget constraints

```python
@dataclass
class BudgetConstraints:
    unallocated_points: int  # Free allocations
    respec_points: int  # Costly deallocations

class BudgetTracker:
    def can_allocate_node(self, node_id: int) -> bool:
        """Check if can allocate node (uses unallocated point)."""

    def can_deallocate_node(self, node_id: int) -> bool:
        """Check if can deallocate node (uses respec point)."""

    def get_usage_summary(self) -> Dict[str, int]:
        """Return budget usage statistics."""
```

---

### Epic 2 Testing Strategy

**Unit Tests:**
- `test_tree_validator.py` - Connected/disconnected trees, edge cases
- `test_hill_climbing.py` - Mock calculator, algorithm logic
- `test_budget_tracker.py` - Budget enforcement

**Integration Tests:**
- `test_optimization_pipeline.py` - Full optimization with real calculator

**Acceptance Criteria:**
- ✅ 8%+ median improvement on 20+ test builds
- ✅ 100% of outputs are valid trees (importable to PoB)
- ✅ Budget constraints never violated
- ✅ <5 minute completion time

---

## Epic 3: User Experience & Local Reliability (Weeks 5-6)

### Goal
Deliver complete local web UI with real-time progress updates and robust error handling.

### Components to Implement

#### 1. **web/app.py**

**Purpose:** Flask application factory

```python
def create_app(testing=False) -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev'  # Change for production

    # Register routes
    from . import routes
    app.register_blueprint(routes.bp)

    # Initialize logging
    from ..utils.logging_config import setup_logging
    setup_logging()

    return app
```

---

#### 2. **web/routes.py**

**Purpose:** HTTP endpoints

```python
@bp.route('/', methods=['GET'])
def index():
    """Home page with form."""
    return render_template('index.html')

@bp.route('/optimize', methods=['POST'])
def optimize():
    """
    Submit optimization request.

    Form Data:
        pob_code: Base64 PoB code
        goal: maximize_dps | maximize_ehp | balanced
        unallocated_points: int
        respec_points: int (optional)

    Returns:
        Redirect to /progress/<session_id>
    """
    # 1. Parse form data
    # 2. Parse PoB code
    # 3. Create session
    # 4. Start background thread
    # 5. Redirect to progress page

@bp.route('/sse/<session_id>')
def sse_progress(session_id):
    """Server-Sent Events stream for progress updates."""
    return stream_optimization_progress(session_id)

@bp.route('/results/<session_id>')
def results(session_id):
    """Display optimization results."""
    # 1. Fetch results from session
    # 2. Generate optimized PoB code
    # 3. Render results template
```

---

#### 3. **web/sse.py**

**Purpose:** Server-Sent Events for real-time progress

```python
def stream_optimization_progress(session_id: str) -> Response:
    """
    Stream optimization progress via SSE.

    Yields:
        SSE messages every 2s with progress updates
    """
    def generate():
        while True:
            with session_lock:
                session = get_session(session_id)
                if not session:
                    break

                data = {
                    "status": session["status"],
                    "progress": session["progress"],
                    "message": session["message"],
                    "iterations": session["iterations"]
                }

            yield f"data: {json.dumps(data)}\n\n"

            if data["status"] in ["complete", "error"]:
                break

            time.sleep(2)

    return Response(generate(), mimetype="text/event-stream")
```

---

#### 4. **frontend/templates/base.html**

**Purpose:** Base template with Bootstrap 5

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}PoE 2 Passive Tree Optimizer{% endblock %}</title>

    <!-- Bootstrap 5 CDN -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- Custom CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/custom.css') }}">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">PoE 2 Passive Tree Optimizer</a>
        </div>
    </nav>

    <main class="container my-5">
        {% block content %}{% endblock %}
    </main>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

---

#### 5. **frontend/static/js/progress.js**

**Purpose:** SSE client for progress updates

```javascript
function connectToProgressStream(sessionId) {
    const eventSource = new EventSource(`/sse/${sessionId}`);

    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);

        // Update progress bar
        updateProgressBar(data.progress);

        // Update status message
        document.getElementById('status-message').textContent = data.message;

        // Handle completion
        if (data.status === "complete") {
            eventSource.close();
            window.location.href = `/results/${sessionId}`;
        }
    };

    eventSource.onerror = function() {
        eventSource.close();
        // Fall back to polling
        pollProgress(sessionId);
    };
}
```

---

### Epic 3 Testing Strategy

**Integration Tests:**
- `test_session_management.py` - Concurrent sessions, cleanup

**E2E Tests:**
- `test_optimization_workflow.py` - Full workflow: submit → progress → results

**Acceptance Criteria:**
- ✅ 95%+ parse success rate
- ✅ Clear error messages
- ✅ 50+ consecutive optimizations without leaks
- ✅ Progress updates <10s lag

---

## Implementation Priorities

### P0 - Critical (Must Have)
- FR-1.2: PoB parsing (`parsers/pob_parser.py`)
- FR-3.1: Lupa integration (`calculator/pob_engine.py`)
- FR-3.2: Build calculation (`calculator/build_calculator.py`)
- FR-4.1: Hill climbing (`optimizer/hill_climbing.py`)
- FR-4.2: Tree validation (`optimizer/tree_validator.py`)
- FR-4.4: Progress reporting (`web/sse.py`)

### P1 - High (Should Have)
- FR-3.3: Batch performance (optimizations)
- FR-3.4: Timeout/error recovery
- FR-4.3: Budget enforcement
- FR-5.2: PoB code generation
- FR-1.7: Accessibility (Bootstrap defaults)

### P2 - Medium (Nice to Have)
- FR-1.5: Version detection
- FR-1.6: Unsupported build detection
- FR-4.5: Confidence score
- FR-5.5: Round-trip validation

---

## Quick Start Commands

```bash
# Epic 1: Setup
git submodule init && git submodule update
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Epic 1: Verify PoB engine
ls external/pob-engine/HeadlessWrapper.lua

# Epic 2: Run tests
pytest tests/unit/ -v

# Epic 3: Start dev server
python src/main.py

# Access at http://localhost:5000
```

---

**Document Status:** ✅ Complete - Ready for Implementation
**Next Steps:** Review individual tech specs, begin Epic 1 Week 1

---

_End of Technical Specifications Summary_
