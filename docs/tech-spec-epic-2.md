# Epic Technical Specification: Core Optimization Engine

Date: 2025-10-27
Author: Alec
Epic ID: 2
Status: Draft

---

## Overview

Epic 2 implements the core optimization engine that transforms the passive tree optimizer from a validated calculation platform (Epic 1) into a functioning optimization tool. This epic delivers the "magic" users pay for: automatic discovery of mathematically superior passive tree configurations through hill climbing algorithms operating within dual budget constraints (unallocated points and respec points).

Building on Epic 1's proven 2ms-per-calculation performance and 0% calculation error rate, Epic 2 introduces an intelligent iterative search algorithm that evaluates thousands of potential tree configurations to discover improvements users would never find through manual experimentation. The target outcome is 5-15% median improvement in user-selected metrics (DPS, EHP, or balanced) while completing within 5 minutes and never exceeding budget constraints—delivering 3+ hours of manual optimization value in under 30 seconds of automated computation.

## Objectives and Scope

### In Scope

**Core Algorithm (Stories 2.1-2.2):**
- Steepest-ascent hill climbing implementation with convergence detection
- Neighbor generation strategies (add node, swap node) with connectivity validation
- Priority-based neighbor selection (Notable/Keystone > Small > Travel nodes)
- Free-first optimization strategy (maximize unallocated point usage before respecs)

**Budget Management (Stories 2.3-2.5):**
- Auto-detection of unallocated passive points from character level and allocated nodes
- Dual budget constraint enforcement (unallocated points + respec points tracked separately)
- Hard budget limit validation preventing overspend
- Free-first prioritization maximizing user value before costly respecs

**Metric Framework (Story 2.6):**
- DPS maximization (total damage per second optimization)
- EHP maximization (effective hit points / survivability optimization)
- Balanced optimization (60% DPS / 40% EHP weighted metric)
- Normalization for cross-metric comparison

**Convergence and Progress (Stories 2.7-2.8):**
- Multi-criteria convergence detection (no improvement, max iterations, timeout, diminishing returns)
- Real-time progress tracking with iteration count, best metric, budget usage
- 5-minute hard timeout with graceful degradation (return best found)
- Progress callback API for UI integration (Epic 3)

### Out of Scope (Deferred to Post-MVP)

**Advanced Algorithm Variants:**
- Random restart (escape local maxima by exploring multiple starting points)
- Simulated annealing (probabilistic acceptance of worse neighbors)
- Genetic algorithms (population-based search with crossover)
- Parallel neighbor evaluation (multi-threading)

**Optimization Enhancements:**
- Path efficiency filtering (value-per-distance scoring)
- Calculation result caching (hash-based memoization)
- Incremental stat calculation (delta updates vs full recalculation)
- Adaptive iteration limits (dynamic adjustment based on performance)

**Feature Extensions:**
- Multi-objective Pareto frontier optimization (simultaneously optimize DPS and EHP)
- Cluster jewel socket optimization
- Ascendancy class recommendation
- Path minimization (shortest route to allocated nodes)

## System Architecture Alignment

Epic 2 introduces the `src/optimizer/` module as a new top-level component in the layered architecture established in Epic 1. This module sits at the **Application Logic Layer**, consuming services from the **Calculation Layer** (Epic 1) and will be consumed by the **Presentation Layer** (Epic 3).

**Architectural Dependencies:**

**Consumes from Epic 1:**
- `src/calculator/calculator.py::calculate_build_stats()` - PoB calculation engine (2ms per call)
- `src/calculator/passive_tree.py::PassiveTreeGraph` - Tree structure with is_connected() validation (0.0185ms avg)
- `src/models/build_data.py::BuildData` - Immutable build representation
- `src/models/build_data.py::BuildStats` - Calculation results (DPS, Life, EHP, etc.)

**Provides to Epic 3:**
- `src/optimizer/hill_climbing.py::optimize_build()` - Main optimization entry point
- `src/optimizer/progress.py::ProgressCallback` - Real-time UI update interface
- `OptimizationResult` data model - Before/after comparison with budget breakdown

**Module Isolation:**
- Zero modifications to Epic 1 code (calculator, parsers, models are stable APIs)
- No circular dependencies (optimizer depends on calculator, not vice versa)
- Clean separation: calculator = "what-if analysis", optimizer = "search strategy"

**Performance Contract:**
- Optimization completes within 5 minutes (Story 3.9 timeout requirement)
- Budget: 600 max iterations × 425ms/iteration = 255 seconds (4.25 min worst case)
- Memory: <100MB during optimization (Epic 1 baseline: 45MB, +55MB headroom)

**Constraint Adherence:**
- Thread-local LuaRuntime pattern (from Epic 1) maintained - no concurrency issues
- Resource cleanup after each optimization (prevent memory leaks)
- No external dependencies beyond Epic 1 + Python stdlib

## Detailed Design

### Services and Modules

The optimizer is implemented as a cohesive module with six specialized components, each with single responsibility:

| Module | Responsibility | Key Inputs | Key Outputs | Owner Story |
|--------|----------------|------------|-------------|-------------|
| `hill_climbing.py` | Orchestrate optimization loop, coordinate all other modules | OptimizationConfiguration | OptimizationResult | Story 2.1 |
| `neighbor_generator.py` | Generate valid tree mutations (add/swap nodes) with connectivity validation | BuildData, PassiveTreeGraph, BudgetState | List[TreeMutation] | Story 2.2 |
| `budget_tracker.py` | Enforce dual budget constraints (unallocated + respec points) | BudgetState, TreeMutation | bool (can_apply), updated state | Story 2.4 |
| `metrics.py` | Calculate optimization metrics (DPS, EHP, balanced) from build stats | BuildData, metric_type | float (metric value) | Story 2.6 |
| `convergence.py` | Detect when optimization should terminate (no improvement, timeout, etc.) | current_metric, iteration_count, time_elapsed | bool (has_converged), reason | Story 2.7 |
| `progress.py` | Track and report optimization progress for UI updates | iteration, best_metric, budget_used | ProgressUpdate (callback invocation) | Story 2.8 |

**Module Dependency Graph:**
```
hill_climbing.py (orchestrator)
├─→ neighbor_generator.py
│   ├─→ PassiveTreeGraph (Epic 1)
│   └─→ budget_tracker.py
├─→ metrics.py
│   └─→ calculator.calculate_build_stats() (Epic 1)
├─→ convergence.py (pure logic, no deps)
├─→ progress.py (pure state tracking, no deps)
└─→ budget_tracker.py (pure state management, no deps)
```

**Design Principles:**
- **No circular dependencies:** Dependency graph is acyclic (DAG)
- **Single responsibility:** Each module has one clear purpose
- **Pure utility modules:** budget_tracker, convergence, progress have zero external dependencies
- **Minimal Epic 1 coupling:** Only neighbor_generator and metrics call Epic 1 APIs

### Data Models and Contracts

**OptimizationConfiguration** (Input)
```python
@dataclass
class OptimizationConfiguration:
    """Input configuration for optimization run."""
    build: BuildData                    # Initial build to optimize
    metric: str                         # "dps" | "ehp" | "balanced"
    unallocated_points: int             # Budget: free allocations
    respec_points: Optional[int]        # Budget: costly deallocations (None = unlimited)
    max_iterations: int = 600           # Convergence: max iterations (reduced from 1000 per prep sprint)
    max_time_seconds: int = 300         # Timeout: 5 minutes
    convergence_patience: int = 3       # Convergence: iterations without improvement
    progress_callback: Optional[Callable] = None  # UI updates
```

**OptimizationResult** (Output)
```python
@dataclass
class OptimizationResult:
    """Output of optimization run."""
    optimized_build: BuildData          # Best configuration found
    baseline_stats: BuildStats          # Original build stats
    optimized_stats: BuildStats         # Optimized build stats
    improvement_pct: float              # Percentage improvement in target metric

    # Budget usage
    unallocated_used: int               # Free points spent
    respec_used: int                    # Costly respecs spent

    # Convergence info
    iterations_run: int                 # Total iterations executed
    convergence_reason: str             # "no_improvement" | "max_iterations" | "timeout"
    time_elapsed_seconds: float         # Wall-clock time

    # Change tracking
    nodes_added: Set[int]               # New allocations
    nodes_removed: Set[int]             # Deallocated nodes
    nodes_swapped: List[Tuple[int, int]]  # (removed, added) pairs
```

**BudgetState** (Internal State)
```python
@dataclass
class BudgetState:
    """Tracks budget consumption during optimization."""
    unallocated_available: int          # Initial unallocated points
    unallocated_used: int = 0           # Points spent on additions
    respec_available: Optional[int]     # Initial respec points (None = unlimited)
    respec_used: int = 0                # Respecs spent on swaps

    def can_allocate(self, count: int = 1) -> bool:
        """Check if we can allocate `count` more nodes."""
        return (self.unallocated_used + count) <= self.unallocated_available

    def can_respec(self, count: int = 1) -> bool:
        """Check if we can respec `count` more nodes."""
        if self.respec_available is None:
            return True  # Unlimited
        return (self.respec_used + count) <= self.respec_available
```

**TreeMutation** (Neighbor Representation)
```python
@dataclass
class TreeMutation:
    """Represents a single tree modification (add or swap node)."""
    mutation_type: str                  # "add" | "swap"
    nodes_added: Set[int]               # Nodes to allocate
    nodes_removed: Set[int]             # Nodes to deallocate
    unallocated_cost: int               # Budget cost: free points
    respec_cost: int                    # Budget cost: respec points

    def apply(self, build: BuildData) -> BuildData:
        """Apply mutation to build, return new BuildData."""
        new_passive_nodes = build.passive_nodes.copy()
        new_passive_nodes -= self.nodes_removed
        new_passive_nodes |= self.nodes_added
        return replace(build, passive_nodes=new_passive_nodes)
```

**Invariants:**
- `BuildData` remains immutable (use `dataclasses.replace()` for modifications)
- `TreeMutation` always produces valid connected trees (validated before creation)
- `BudgetState` constraints always enforced (no overspend possible)
- All metrics normalized to floats (higher = better)

### APIs and Interfaces

**Primary API: optimize_build()** (Story 2.1)
```python
def optimize_build(config: OptimizationConfiguration) -> OptimizationResult:
    """
    Execute hill climbing optimization on a build.

    Algorithm: Steepest-ascent hill climbing with multi-criteria convergence
    - Start with baseline build
    - Generate neighbor configurations (mutations)
    - Evaluate all neighbors (calculate stats)
    - Select best neighbor if improvement found
    - Update budget state and check convergence
    - Repeat until converged or timeout

    Args:
        config: Optimization configuration (build, metric, budgets, limits)

    Returns:
        OptimizationResult with best configuration found

    Raises:
        ValueError: If config is invalid (negative budgets, invalid metric)
        AssertionError: If budget enforcement fails (algorithm bug)
    """
```

**Neighbor Generation API** (Story 2.2)
```python
def generate_neighbors(
    build: BuildData,
    tree: PassiveTreeGraph,
    budget: BudgetState,
    prioritize_adds: bool = True
) -> List[TreeMutation]:
    """
    Generate valid neighbor configurations from current build.

    Strategies:
    1. Add Node: Allocate any unallocated connected node (uses unallocated budget)
    2. Swap Node: Remove 1 node, add 1 connected node (uses respec budget)

    Prioritization (if prioritize_adds=True):
    - Generate ALL "add node" neighbors first (free budget)
    - Only generate "swap node" neighbors if unallocated exhausted
    - Prefer high-value nodes: Notable > Keystone > Small > Travel

    Args:
        build: Current build configuration
        tree: PassiveTreeGraph for connectivity validation
        budget: Current budget state
        prioritize_adds: If True, prefer free allocations over swaps

    Returns:
        List of valid TreeMutation objects (limit: Top 100 by value)
    """
```

**Metrics API** (Story 2.6)
```python
def calculate_metric(build: BuildData, metric_type: str) -> float:
    """
    Calculate optimization metric for a build.

    Metrics:
    - "dps": Total DPS output (raw value from PoB)
    - "ehp": Effective Hit Points (Life + ES + mitigation formula)
    - "balanced": Weighted average (60% DPS normalized, 40% EHP normalized)

    Args:
        build: BuildData to evaluate
        metric_type: "dps" | "ehp" | "balanced"

    Returns:
        Metric value (higher is better)

    Raises:
        ValueError: If metric_type unknown
        CalculationError: If PoB calculation fails (logged, returns -infinity)
    """
```

**Budget Tracking API** (Story 2.4)
```python
class BudgetTracker:
    """Manages dual budget constraints during optimization."""

    def __init__(self, unallocated: int, respec: Optional[int]):
        self.state = BudgetState(unallocated, 0, respec, 0)

    def can_apply_mutation(self, mutation: TreeMutation) -> bool:
        """Check if mutation fits within budget."""

    def apply_mutation(self, mutation: TreeMutation) -> None:
        """Update budget counters after applying mutation."""

    def get_budget_summary(self) -> dict:
        """Return budget usage for reporting."""
```

**Convergence Detection API** (Story 2.7)
```python
class ConvergenceDetector:
    """Detects when optimization should stop."""

    def __init__(self, patience: int = 3, min_improvement: float = 0.001):
        self.patience = patience                    # Iterations without improvement
        self.min_improvement = min_improvement      # 0.1% threshold
        self.iterations_without_improvement = 0
        self.best_metric = None

    def update(self, current_metric: float) -> None:
        """Update with latest metric value."""

    def has_converged(self) -> bool:
        """Check if optimization has converged."""

    def get_convergence_reason(self) -> str:
        """Return reason: "no_improvement" | "diminishing_returns" | "no_neighbors"."""
```

**Progress Tracking API** (Story 2.8)
```python
class ProgressTracker:
    """Tracks and reports optimization progress."""

    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.start_time = time.time()

    def update(
        self,
        iteration: int,
        best_metric: float,
        improvement_pct: float,
        budget: BudgetState
    ) -> None:
        """Update progress and invoke callback every 100 iterations."""

    def should_report(self) -> bool:
        """Check if we should report progress (every 100 iterations)."""

# Callback signature
def progress_callback(
    iteration: int,
    best_metric: float,
    improvement_pct: float,
    budget_used: dict,
    time_elapsed: float
) -> None:
    """Called every 100 iterations for UI updates (Epic 3)."""
```

### Workflows and Sequencing

**High-Level Optimization Flow:**

```
1. Initialize
   ├── Load passive tree (cached from Epic 1)
   ├── Calculate baseline stats (invoke PoB engine)
   ├── Initialize budget tracker (unallocated + respec points)
   ├── Initialize convergence detector (patience=3)
   └── Initialize progress tracker (with UI callback)

2. Main Loop (while not converged)
   ├── Generate neighbors from current build
   │   ├── Check budget availability
   │   ├── Generate "add node" mutations (free budget)
   │   ├── Generate "swap node" mutations (costly budget)
   │   ├── Validate tree connectivity for all
   │   └── Prioritize and limit to Top 100 by value
   │
   ├── Evaluate neighbors (steepest-ascent)
   │   ├── For each mutation:
   │   │   ├── Apply mutation → new BuildData
   │   │   ├── Calculate stats (PoB engine, 2ms)
   │   │   ├── Calculate metric value
   │   │   └── Track best neighbor
   │   └── Select best if improvement found
   │
   ├── Update state
   │   ├── If improvement: adopt new build
   │   ├── Update budget tracker
   │   ├── Update convergence detector
   │   └── Report progress (every 100 iterations)
   │
   └── Check convergence
       ├── No improvement for 3 iterations?
       ├── Max iterations (600) reached?
       ├── Timeout (5 min) exceeded?
       ├── No valid neighbors?
       └── Improvement <0.1% (diminishing returns)?

3. Finalize
   ├── Calculate final stats
   ├── Compute improvement percentage
   ├── Generate change summary (adds/removes/swaps)
   └── Return OptimizationResult
```

**Performance Budget per Iteration:**

| Operation | Time | Calls | Total |
|-----------|------|-------|-------|
| Generate neighbors | ~20ms | 1 | 20ms |
| Evaluate neighbors (PoB) | 2ms | 50-200 | 100-400ms |
| Calculate metrics | ~0.01ms | 50-200 | 0.5-2ms |
| Update state | ~5ms | 1 | 5ms |
| **Total** | - | - | **125-425ms** |

**Expected Optimization Times:**
- Typical build (300 iterations): 37-127 seconds (0.6-2.1 minutes)
- Complex build (600 iterations): 75-255 seconds (1.3-4.25 minutes)
- Always within 5-minute timeout with safety margin

## Non-Functional Requirements

### Performance

**NFR-Epic2-P1: Optimization Completion Time**
- **Target:** Typical build completes in <2 minutes (300 iterations × 400ms avg = 120s)
- **Maximum:** Complex build completes in <5 minutes (600 iterations × 425ms = 255s)
- **Measurement:** Wall-clock time from optimize_build() call to return
- **Validation:** Performance test suite with 22-build corpus (prep sprint deliverable)
- **Reference:** PRD NFR-3 (Calculation Performance)

**NFR-Epic2-P2: Iteration Performance**
- **Target:** Average iteration time ≤400ms (50-200 neighbors × 2ms calc)
- **Components:** 20ms neighbor gen + 100-400ms evaluation + 5ms state update
- **Bottleneck:** PoB calculations (2ms each, dominant cost)
- **Optimization:** Pre-compiled Lua functions (validated in Epic 1 Story 1.8)

**NFR-Epic2-P3: Memory Usage**
- **Target:** <100MB during optimization (Epic 1 baseline: 45MB, +55MB headroom)
- **Validation:** Run 50 consecutive optimizations, verify no memory growth
- **Cleanup:** Explicit resource cleanup after each optimization (Story 3.10 requirement)

**NFR-Epic2-P4: Convergence Efficiency**
- **Target:** Converge within 300-600 iterations for 80%+ of builds
- **Patience:** 3 iterations without improvement (balance speed vs thoroughness)
- **Early termination:** Diminishing returns check (<0.1% improvement)

**Performance Regression Prevention:**
- Benchmark suite using 22-build test corpus
- CI pipeline fails if iteration time >500ms average
- Profiling required for all optimization-path changes

### Security

**NFR-Epic2-S1: Input Validation**
- Validate OptimizationConfiguration on entry (negative budgets rejected)
- Validate BuildData integrity (no orphan nodes, valid class starting position)
- Budget constraints enforced at multiple layers (defense in depth)

**NFR-Epic2-S2: Resource Limits**
- Max iterations hard limit (600) prevents infinite loops
- Timeout enforcement (5 minutes) prevents resource exhaustion
- No user-controlled recursion depth

**NFR-Epic2-S3: Local-Only Security Posture**
- Epic 2 has zero network operations (purely computational)
- All inputs from trusted Epic 1 parsers (already validated)
- Epic 3 will add network layer security (out of scope for Epic 2)

### Reliability/Availability

**NFR-Epic2-R1: Graceful Degradation**
- Timeout returns best result found so far (partial success > failure)
- PoB calculation errors logged but don't crash optimizer (reject bad neighbor, continue)
- No valid neighbors treated as convergence (not error)

**NFR-Epic2-R2: Deterministic Behavior**
- Same build + config always produces same result (steepest-ascent deterministic)
- No randomness in neighbor generation order (reproducible for debugging)
- Test suite validates determinism (run same optimization 3x, compare results)

**NFR-Epic2-R3: Error Recovery**
- Budget overrun triggers AssertionError (fail-fast, indicates algorithm bug)
- Connectivity validation prevents invalid tree states (never return disconnected tree)
- Timeout doesn't lose work (best-so-far always tracked)

**NFR-Epic2-R4: Resource Cleanup**
- No memory leaks across 50+ consecutive optimizations
- LuaRuntime cleanup after each optimization (thread-local pattern from Epic 1)
- Budget/convergence/progress state reset between runs

### Observability

**NFR-Epic2-O1: Progress Reporting**
- Real-time progress updates every 100 iterations
- Callback provides: iteration, best metric, improvement %, budget used, time elapsed
- Epic 3 UI consumes these updates for live progress display

**NFR-Epic2-O2: Result Transparency**
- OptimizationResult includes full breakdown: baseline, optimized, improvement %
- Budget usage detailed: unallocated used/available, respec used/available
- Node changes tracked: additions, removals, swaps
- Convergence reason explicit: "no_improvement" | "max_iterations" | "timeout" | etc.

**NFR-Epic2-O3: Logging Strategy**
- INFO: Optimization start (config summary), completion (result summary)
- DEBUG: Iteration-level progress (every 10 iterations), neighbor counts, best metric updates
- WARN: Timeout approaching (4.5 min), no improvement for extended period
- ERROR: PoB calculation failures, invalid configurations, budget violations

**NFR-Epic2-O4: Performance Instrumentation**
- Iteration timing logged (detect performance regressions)
- Neighbor generation time tracked (identify bottlenecks)
- Convergence metrics recorded (analyze typical iteration counts)
- Memory usage sampled (detect leaks)

## Dependencies and Integrations

### External Dependencies

**Python Runtime:**
- Python 3.10+ (required for dataclasses, type hints, match statements)
- No new dependencies beyond Epic 1 requirements

**Epic 1 Dependencies (Inherited):**
- `lupa>=2.0` - Python-LuaJIT bindings for PoB calculation engine
- `xmltodict==0.13.0` - XML parsing for PoB codes
- Path of Building repository (Git submodule at `external/pob-engine/`)

**Testing Dependencies:**
- `pytest>=7.4.0` - Test framework
- `pytest-cov>=4.1.0` - Coverage reporting
- `pytest-benchmark>=4.0.0` - Performance benchmarking
- `pytest-xdist>=3.5.0` - Parallel test execution
- `psutil>=5.9.0` - Memory usage monitoring

**Epic 2 Adds:** Zero new external dependencies (Python stdlib only)

### Internal Module Dependencies

**Epic 1 APIs (Required):**
- `src/calculator/calculator.py::calculate_build_stats(BuildData) -> BuildStats`
  - Version: Stable as of Story 1.8
  - Performance: 2ms per call (validated)
  - Reliability: 0% error rate on test corpus

- `src/calculator/passive_tree.py::PassiveTreeGraph`
  - `get_neighbors(node_id: int) -> List[int]` - Adjacency list lookup
  - `is_connected(nodes: Set[int], start: int) -> bool` - Connectivity validation
  - Performance: 0.0185ms avg (validated in prep sprint)

- `src/models/build_data.py::BuildData`
  - Immutable dataclass representing build configuration
  - Contains: passive_nodes (Set[int]), character_level, class_name, etc.

- `src/models/build_data.py::BuildStats`
  - Calculation results: total_dps, life, energy_shield, evasion, etc.
  - Returned by calculate_build_stats()

**Epic 3 Integration Points (Provides To):**
- `src/optimizer/hill_climbing.py::optimize_build()` - Main entry point
- `OptimizationConfiguration` - Input model for UI
- `OptimizationResult` - Output model for results display
- `ProgressCallback` signature - Real-time UI updates

### Integration Constraints

**No Modifications to Epic 1:**
- Epic 1 code remains untouched (stable API contract)
- Optimizer consumes Epic 1 as read-only dependency
- No circular dependencies introduced

**Resource Sharing:**
- PassiveTreeGraph singleton (loaded once, cached)
- LuaRuntime thread-local pattern (maintained from Epic 1)
- No shared mutable state between optimizations

**Version Pinning:**
- Epic 1 APIs frozen as of Story 1.8 completion
- Any Epic 1 changes require Epic 2 regression testing
- Test corpus validates integration stability

## Acceptance Criteria (Authoritative)

### Story 2.1: Implement Hill Climbing Core Algorithm

**AC-2.1.1:** Algorithm starts with current passive tree (baseline)
**AC-2.1.2:** Algorithm generates neighbor configurations (add/swap 1 node)
**AC-2.1.3:** Algorithm evaluates each neighbor using PoB calculations
**AC-2.1.4:** Algorithm selects best neighbor if improvement found
**AC-2.1.5:** Algorithm repeats until convergence (no improvement)
**AC-2.1.6:** Algorithm returns best configuration found

### Story 2.2: Generate Neighbor Configurations (1-Hop Moves)

**AC-2.2.1:** Generate "add node" neighbors: add any unallocated connected node
**AC-2.2.2:** Generate "swap node" neighbors: remove 1 node, add 1 connected node
**AC-2.2.3:** Validate all neighbors are valid (connected tree, within budget)
**AC-2.2.4:** Limit neighbor count to reasonable size (50-200 per iteration)
**AC-2.2.5:** Prioritize high-value nodes (Notable/Keystone over travel nodes)

### Story 2.3: Auto-Detect Unallocated Passive Points

**AC-2.3.1:** Calculate: `max_points = get_max_passive_points(character_level)`
**AC-2.3.2:** Calculate: `allocated_points = count_allocated_nodes(passive_tree)`
**AC-2.3.3:** Calculate: `unallocated_points = max(0, max_points - allocated_points)`
**AC-2.3.4:** Display auto-detected value in UI (user can override if wrong)
**AC-2.3.5:** Handle edge cases: quest rewards, special nodes, ascendancy points

### Story 2.4: Implement Dual Budget Constraint Tracking

**AC-2.4.1:** Track `unallocated_available` and `unallocated_used` (free allocations)
**AC-2.4.2:** Track `respec_available` and `respec_used` (costly deallocations)
**AC-2.4.3:** Enforce: `unallocated_used <= unallocated_available`
**AC-2.4.4:** Enforce: `respec_used <= respec_available` (or unlimited if None)
**AC-2.4.5:** Prevent moves that exceed either budget
**AC-2.4.6:** Log budget usage in optimization progress

### Story 2.5: Implement Budget Prioritization (Free-First Strategy)

**AC-2.5.1:** When generating neighbors, prioritize "add node" moves (use unallocated)
**AC-2.5.2:** Only generate "swap node" moves if unallocated exhausted
**AC-2.5.3:** Result breakdown shows: "Used X of Y unallocated (FREE), Z of W respec"
**AC-2.5.4:** Users see immediate value from free allocations

### Story 2.6: Metric Selection and Evaluation

**AC-2.6.1:** Support metric: "Maximize DPS" (total DPS output)
**AC-2.6.2:** Support metric: "Maximize EHP" (effective hit points)
**AC-2.6.3:** Support metric: "Balanced" (weighted: 60% DPS, 40% EHP)
**AC-2.6.4:** Extract correct stats from PoB calculation results
**AC-2.6.5:** Normalize metrics for comparison (DPS and EHP different scales)

### Story 2.7: Convergence Detection

**AC-2.7.1:** Stop when no neighbor improves metric for N consecutive iterations (N=3)
**AC-2.7.2:** Stop when improvement delta <0.1% (diminishing returns)
**AC-2.7.3:** Stop when maximum iteration limit reached (600 iterations)
**AC-2.7.4:** Log convergence reason: "Converged: no improvement for 3 iterations"

### Story 2.8: Optimization Progress Tracking

**AC-2.8.1:** Track: current iteration number
**AC-2.8.2:** Track: best metric value found so far
**AC-2.8.3:** Track: current improvement percentage vs baseline
**AC-2.8.4:** Track: budget usage (unallocated used, respec used)
**AC-2.8.5:** Provide progress callback for UI updates
**AC-2.8.6:** Update every 100 iterations (per FR-5.2 consistency fix)

### Epic-Level Success Criteria

**Epic-AC-1:** Find improvements for 80%+ of non-optimal builds (from test corpus)
**Epic-AC-2:** Median improvement: 8%+ for builds with budget headroom
**Epic-AC-3:** Optimization completes within 5 minutes for complex builds
**Epic-AC-4:** Budget constraints never exceeded (hard stop enforcement)

## Traceability Mapping

| AC ID | Story | Spec Section | Component/API | Test Approach |
|-------|-------|--------------|---------------|---------------|
| AC-2.1.1 | 2.1 | Workflows & Sequencing (Initialize) | hill_climbing.py::optimize_build() | Unit test: verify baseline stats calculated |
| AC-2.1.2 | 2.1 | Workflows & Sequencing (Main Loop) | neighbor_generator.py::generate_neighbors() | Mock neighbor generator, verify called |
| AC-2.1.3 | 2.1 | Workflows & Sequencing (Evaluate) | metrics.py::calculate_metric() | Mock metrics, verify all neighbors evaluated |
| AC-2.1.4 | 2.1 | Workflows & Sequencing (Update State) | Steepest-ascent selection logic | Unit test: verify best neighbor selected |
| AC-2.1.5 | 2.1 | Workflows & Sequencing (Convergence) | convergence.py::has_converged() | Unit test: verify loop terminates |
| AC-2.1.6 | 2.1 | APIs: OptimizationResult | Return value structure | Integration test: verify result format |
| AC-2.2.1 | 2.2 | APIs: generate_neighbors() | generate_add_neighbors() | Unit test: verify add mutations created |
| AC-2.2.2 | 2.2 | APIs: generate_neighbors() | generate_swap_neighbors() | Unit test: verify swap mutations created |
| AC-2.2.3 | 2.2 | Data Models: TreeMutation | PassiveTreeGraph.is_connected() | Integration test: all neighbors valid trees |
| AC-2.2.4 | 2.2 | APIs: generate_neighbors() | Top-100 prioritization logic | Unit test: verify neighbor count ≤100 |
| AC-2.2.5 | 2.2 | Workflows: Neighbor Pruning | prioritize_candidates() | Unit test: Notables ranked > Travel nodes |
| AC-2.3.1 | 2.3 | Dependencies: BuildData | BuildData.unallocated_points property | Unit test: formula validation (validated in prep sprint) |
| AC-2.3.2 | 2.3 | Dependencies: BuildData | BuildData.passive_nodes.count() | Unit test: count allocated nodes |
| AC-2.3.3 | 2.3 | Data Models: BuildData | Calculation logic | Unit test: max - allocated = unallocated |
| AC-2.3.4 | 2.3 | Epic 3 Integration | UI display (out of Epic 2 scope) | Manual test in Epic 3 |
| AC-2.3.5 | 2.3 | Data Models: BuildData | Edge case handling | Unit test: various character levels |
| AC-2.4.1 | 2.4 | Data Models: BudgetState | BudgetState.unallocated_* fields | Unit test: state tracking |
| AC-2.4.2 | 2.4 | Data Models: BudgetState | BudgetState.respec_* fields | Unit test: state tracking |
| AC-2.4.3 | 2.4 | APIs: BudgetTracker | can_allocate() method | Unit test: boundary conditions |
| AC-2.4.4 | 2.4 | APIs: BudgetTracker | can_respec() method | Unit test: unlimited vs limited |
| AC-2.4.5 | 2.4 | Workflows: Budget Enforcement | Neighbor generation budget check | Integration test: no budget overrun |
| AC-2.4.6 | 2.4 | NFR: Observability (O2) | get_budget_summary() | Unit test: summary format |
| AC-2.5.1 | 2.5 | APIs: generate_neighbors() | Free-first generation order | Unit test: adds generated before swaps |
| AC-2.5.2 | 2.5 | APIs: generate_neighbors() | Conditional swap generation | Unit test: swaps only if U exhausted |
| AC-2.5.3 | 2.5 | Data Models: OptimizationResult | Budget breakdown fields | Integration test: result structure |
| AC-2.5.4 | 2.5 | Objectives & Scope | User value maximization | Acceptance test: free points used first |
| AC-2.6.1 | 2.6 | APIs: calculate_metric() | DPS metric calculation | Unit test: extract total_dps from BuildStats |
| AC-2.6.2 | 2.6 | APIs: calculate_metric() | EHP metric calculation | Unit test: Life + ES + mitigation formula |
| AC-2.6.3 | 2.6 | APIs: calculate_metric() | Balanced metric calculation | Unit test: 60/40 weighted average |
| AC-2.6.4 | 2.6 | Dependencies: Epic 1 | calculate_build_stats() integration | Integration test: real PoB calculations |
| AC-2.6.5 | 2.6 | APIs: calculate_metric() | Normalization logic | Unit test: comparable scales |
| AC-2.7.1 | 2.7 | APIs: ConvergenceDetector | Patience counter logic | Unit test: 3 iterations without improvement |
| AC-2.7.2 | 2.7 | APIs: ConvergenceDetector | Diminishing returns threshold | Unit test: <0.1% improvement triggers |
| AC-2.7.3 | 2.7 | Data Models: OptimizationConfiguration | max_iterations limit | Unit test: 600 iteration hard stop |
| AC-2.7.4 | 2.7 | NFR: Observability (O2) | get_convergence_reason() | Unit test: reason strings correct |
| AC-2.8.1 | 2.8 | APIs: ProgressTracker | Iteration counter | Unit test: iteration tracking |
| AC-2.8.2 | 2.8 | APIs: ProgressTracker | Best metric tracking | Unit test: best value recorded |
| AC-2.8.3 | 2.8 | APIs: ProgressTracker | Improvement percentage calc | Unit test: (best-baseline)/baseline * 100 |
| AC-2.8.4 | 2.8 | APIs: ProgressTracker | Budget usage tracking | Unit test: budget state captured |
| AC-2.8.5 | 2.8 | APIs: ProgressTracker | Callback invocation | Unit test: callback called with correct args |
| AC-2.8.6 | 2.8 | APIs: ProgressTracker | Report frequency | Unit test: every 100 iterations |
| Epic-AC-1 | Epic 2 | Epic Success Criteria | End-to-end optimization | Acceptance test: 22-build corpus, 80%+ improved |
| Epic-AC-2 | Epic 2 | Epic Success Criteria | Median improvement calc | Acceptance test: median ≥8% on corpus |
| Epic-AC-3 | Epic 2 | NFR: Performance (P1) | Timeout enforcement | Performance test: max 5 min, all builds |
| Epic-AC-4 | Epic 2 | NFR: Reliability (R3) | Budget enforcement | Integration test: assert on budget violation |

## Risks, Assumptions, Open Questions

### Risks

**RISK-2.1: Local Maxima Problem** (Medium Probability, Medium Impact)
- **Issue:** Hill climbing can get stuck at local maxima, missing better global solutions
- **Mitigation:** Accept this limitation for MVP - local maximum still better than manual allocation
- **Future:** Implement random restart or simulated annealing if testing shows problem
- **Status:** Monitored - deferred to post-MVP

**RISK-2.2: Complex Build Timeout** (Medium Probability, Low Impact)
- **Issue:** Very complex builds may exceed 5-minute timeout with 600 iterations
- **Mitigation:** Graceful degradation - return best found so far (partial success)
- **Mitigation:** Reduced max_iterations to 600 (from 1000) per prep sprint analysis
- **Validation:** Performance test suite with 22-build corpus
- **Status:** Mitigated

**RISK-2.3: Test Corpus Mostly Optimal** (High Probability, Medium Impact)
- **Issue:** 22-build corpus has mostly fully-optimized builds (0 unallocated points)
- **Impact:** May not validate "8%+ median improvement" success criteria
- **Mitigation:** Add 3-5 synthetic inefficient builds for improvement testing
- **Mitigation:** Use corpus for convergence testing (algorithm should detect "already optimal")
- **Status:** Accepted - add synthetic builds during testing if needed

**RISK-2.4: PassiveTreeGraph Performance** (Low Probability, Medium Impact)
- **Issue:** Story 2.2 may call is_connected() 100,000+ times per optimization
- **Status:** RESOLVED - Prep sprint profiling validated 0.0185ms avg (27x faster than target)
- **No action needed**

**RISK-2.5: Algorithm Bug in Budget Enforcement** (Low Probability, High Impact)
- **Issue:** Bug could allow budget overspend, violating hard constraint
- **Mitigation:** Multi-layer validation (budget tracker + assert in main loop)
- **Mitigation:** Fail-fast with AssertionError if violation detected
- **Testing:** Integration tests specifically target budget edge cases
- **Status:** Mitigated through defensive programming

### Assumptions

**ASSUMPTION-2.1:** Epic 1 APIs remain stable (calculate_build_stats, PassiveTreeGraph)
- **Validation:** Epic 1 frozen as of Story 1.8
- **Impact if false:** May require Epic 2 refactoring
- **Confidence:** HIGH (Epic 1 complete and tested)

**ASSUMPTION-2.2:** PoE 2 passive points formula is `level + 23`
- **Validation:** Validated in prep sprint with 10 test cases
- **Impact if false:** Story 2.3 auto-detection incorrect
- **Mitigation:** User can override auto-detected value
- **Confidence:** HIGH (formula validated)

**ASSUMPTION-2.3:** Test corpus representative of real builds
- **Validation:** 22 builds from poe.ninja (real player builds)
- **Impact if false:** Epic success criteria may not generalize
- **Mitigation:** Diverse class/level distribution in corpus
- **Confidence:** MEDIUM (corpus is real but sample size modest)

**ASSUMPTION-2.4:** 60% DPS / 40% EHP weighting appropriate for "balanced" metric
- **Validation:** Reasonable default per gaming community norms
- **Impact if false:** Users may prefer different weights
- **Mitigation:** Fixed for MVP, make configurable in future
- **Confidence:** MEDIUM (untested with users)

**ASSUMPTION-2.5:** Steepest-ascent sufficient for MVP (no need for advanced algorithms)
- **Validation:** Literature supports steepest-ascent as reliable baseline
- **Impact if false:** May need random restart or simulated annealing
- **Mitigation:** Defer advanced algorithms to post-MVP
- **Confidence:** MEDIUM (validated in research, not in practice)

### Open Questions

**Q1: Should we implement early termination optimization?** (Story 2.1)
- **Context:** If find 5%+ improvement early, stop evaluating remaining neighbors
- **Decision:** Implement as hidden flag (default OFF), test in performance validation
- **Resolution:** Deferred to Story 2.1 implementation

**Q2: What happens if optimization finds 0% improvement?** (Epic Success Criteria)
- **Context:** Build already optimal or budget insufficient
- **Decision:** Return original build, log "no improvement found", not considered failure
- **Resolution:** Documented in convergence detector

**Q3: Should convergence patience be user-configurable?** (Story 2.7)
- **Context:** Currently hardcoded to 3 iterations
- **Decision:** Fixed value for MVP, expose in config file (not UI) if needed
- **Resolution:** Patience=3 is sufficient for MVP

**Q4: How to validate "8%+ median improvement" with mostly-optimal corpus?** (Epic Success Criteria)
- **Context:** Test corpus has 20/22 builds fully optimized (0 unallocated)
- **Decision:** Add 3-5 synthetic inefficient builds during Story 2.6 testing
- **Resolution:** Deferred to testing phase

**Q5: Should Story 2.8 progress output include console logging?** (Story 2.8)
- **Context:** Callback API for UI, but helpful for debugging
- **Decision:** RESOLVED in prep sprint Task #7 - API + basic console output
- **Resolution:** Console logging included for development visibility

## Test Strategy Summary

### Test Levels

**Unit Tests (60% coverage target):**
- **Budget Tracker:** Budget validation, can_allocate/can_respec edge cases
- **Convergence Detector:** Patience counter, diminishing returns, reason strings
- **Progress Tracker:** Iteration tracking, callback invocation frequency
- **Metrics:** Metric calculation with mocked BuildStats (DPS, EHP, balanced)
- **Neighbor Generator:** Add/swap generation logic, prioritization (mocked tree)

**Integration Tests (30% coverage target):**
- **Hill Climbing:** End-to-end optimization with mocked calculator
- **Neighbor Generator:** Real PassiveTreeGraph, validate all neighbors are valid trees
- **Metrics:** Real PoB calculations (2-3 test builds)
- **Budget Enforcement:** No budget overrun across scenarios

**Performance Tests (10% coverage target):**
- **Optimization Speed:** 22-build corpus, measure completion time
- **Iteration Performance:** Average iteration time ≤400ms
- **Memory Usage:** 50 consecutive optimizations, verify no growth

**Acceptance Tests:**
- **Epic Success Criteria:** 80%+ improvement rate, 8%+ median improvement
- **Determinism:** Same build+config produces same result across 3 runs
- **Timeout Handling:** Verify 5-minute hard stop returns partial results

### Test Build Corpus

**Source:** 22 real builds from poeninja (prep sprint Task #4)
- Location: `tests/fixtures/optimization_builds/corpus.json`
- Classes: All 7 classes represented
- Levels: Focus on endgame (68-100)
- Composition: 20/22 fully optimized (good for convergence), 2 with unallocated points

**Synthetic Builds (if needed):**
- 3-5 intentionally inefficient builds
- Allocate travel nodes, skip notables, suboptimal pathing
- For validating "8%+ median improvement" criteria

### Coverage Targets

- **Line Coverage:** 80%+ for optimizer module
- **Branch Coverage:** 70%+ for decision logic (convergence, budget validation)
- **Integration Coverage:** All Epic 1 APIs exercised
- **Performance Regression:** CI fails if iteration time >500ms avg

### Mocking Strategy

- **Mock calculator for fast unit tests:** Return predefined BuildStats
- **Real calculator for integration tests:** Limit to 5-10 builds (slow but accurate)
- **Mock PassiveTreeGraph for unit tests:** Control neighbor count and connectivity
- **Real PassiveTreeGraph for integration tests:** Validate algorithm with real tree

### Test Execution

- **Development:** pytest with coverage (`pytest --cov=src/optimizer`)
- **CI Pipeline:** pytest + performance benchmarks
- **Performance Suite:** pytest-benchmark with 22-build corpus
- **Acceptance:** Manual validation of epic success criteria

### Risk-Based Testing Priorities

1. **HIGH Priority:** Budget enforcement (budget violation = critical bug)
2. **HIGH Priority:** Convergence detection (infinite loop = timeout/hang)
3. **HIGH Priority:** Connectivity validation (disconnected tree = invalid result)
4. **MEDIUM Priority:** Metric calculation accuracy (wrong optimization target)
5. **MEDIUM Priority:** Performance regression (timeout violations)
6. **LOW Priority:** Progress tracking (informational, not critical path)
