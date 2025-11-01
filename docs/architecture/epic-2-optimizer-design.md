# Epic 2: Core Optimization Engine - Architecture Design

**Author:** Winston (Architect) via Bob (Scrum Master)
**Date:** 2025-10-27
**Status:** DRAFT - For Prep Sprint Review
**Version:** 1.0

---

## 1. Overview

This document defines the architecture for Epic 2: Core Optimization Engine, which implements a hill climbing algorithm to discover superior passive tree configurations within budget constraints.

**Primary Goals:**
- Find improvements for 80%+ of non-optimal builds
- Median improvement: 8%+ for builds with budget headroom
- Complete optimization within 5 minutes
- Never exceed budget constraints (hard stop enforcement)

---

## 2. Module Structure

```
src/optimizer/
├── __init__.py                 # Package exports
├── hill_climbing.py            # Story 2.1 - Core algorithm
├── neighbor_generator.py       # Story 2.2 - Tree mutation strategies
├── budget_tracker.py           # Story 2.4 - Dual budget management
├── metrics.py                  # Story 2.6 - Optimization objectives
├── convergence.py              # Story 2.7 - Stopping conditions
└── progress.py                 # Story 2.8 - Progress tracking/reporting
```

### Module Dependencies

```
optimizer/
├── hill_climbing.py
│   ├── → neighbor_generator.py (generate neighbors)
│   ├── → budget_tracker.py (validate budget)
│   ├── → metrics.py (evaluate configurations)
│   ├── → convergence.py (check termination)
│   └── → progress.py (report status)
│
├── neighbor_generator.py
│   ├── → calculator.passive_tree (connectivity validation)
│   ├── → budget_tracker.py (check budget availability)
│   └── → models.build_data (BuildData manipulation)
│
├── budget_tracker.py
│   └── (no dependencies - pure state management)
│
├── metrics.py
│   ├── → calculator.calculator (calculate_build_stats)
│   └── → models.build_data (BuildStats access)
│
├── convergence.py
│   └── (no dependencies - pure logic)
│
└── progress.py
    └── (no dependencies - pure state tracking)
```

**Dependency Rules:**
- No circular dependencies
- Core logic (hill_climbing) orchestrates all other modules
- Utility modules (budget_tracker, convergence, progress) have zero dependencies
- Only neighbor_generator and metrics call external systems (tree, calculator)

---

## 3. Data Models

### 3.1 Configuration State

```python
@dataclass
class OptimizationConfiguration:
    """Input configuration for optimization run."""
    build: BuildData                    # Initial build to optimize
    metric: str                         # "dps", "ehp", "balanced"
    unallocated_points: int             # Budget: free allocations
    respec_points: Optional[int]        # Budget: costly deallocations (None = unlimited)
    max_iterations: int = 1000          # Convergence: max iterations
    max_time_seconds: int = 300         # Timeout: 5 minutes
    convergence_patience: int = 3       # Convergence: iterations without improvement
    progress_callback: Optional[Callable] = None  # UI updates
```

### 3.2 Optimization Result

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

### 3.3 Budget State

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

### 3.4 Tree Mutation

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

---

## 4. Core Components

### 4.1 Hill Climbing Algorithm (Story 2.1)

**Module:** `optimizer/hill_climbing.py`

**Primary Function:**

```python
def optimize_build(config: OptimizationConfiguration) -> OptimizationResult:
    """
    Execute hill climbing optimization on a build.

    Algorithm:
    1. Start with baseline build
    2. Generate neighbor configurations (mutations)
    3. Evaluate each neighbor (calculate stats)
    4. Select best neighbor if improvement found
    5. Update budget state
    6. Check convergence conditions
    7. Repeat until converged or timeout

    Args:
        config: Optimization configuration

    Returns:
        OptimizationResult with best configuration found
    """
```

**Key Responsibilities:**
- Orchestrate optimization loop
- Coordinate all other modules
- Track best configuration found
- Handle timeout/convergence
- Report progress via callback

**Performance Considerations:**
- Main loop overhead: ~0.01ms per iteration (negligible)
- Bottleneck: PoB calculations in metrics.py (~2ms each)
- Target: 300-500 iterations typical, 1000 max

---

### 4.2 Neighbor Generator (Story 2.2)

**Module:** `optimizer/neighbor_generator.py`

**Primary Function:**

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

    Prioritization:
    - If prioritize_adds=True: Generate adds first, swaps only if budget exhausted
    - Prefer high-value nodes: Notable > Keystone > Small passives
    - Limit neighbors to 50-200 per iteration (performance)

    Args:
        build: Current build configuration
        tree: PassiveTreeGraph for connectivity validation
        budget: Current budget state
        prioritize_adds: If True, prefer free allocations over swaps

    Returns:
        List of valid TreeMutation objects
    """
```

**Key Responsibilities:**
- Generate "add node" mutations
- Generate "swap node" mutations
- Validate tree connectivity (no orphan nodes)
- Respect budget constraints
- Prioritize high-value moves

**Performance Considerations:**
- is_connected() calls: ~0.02ms per check (validated in Prep Sprint)
- Target: 50-200 neighbors per iteration
- Worst case: 200 neighbors × 5 checks × 0.02ms = ~20ms per iteration (acceptable)

**Edge Cases:**
- No unallocated budget → Only generate swaps
- No respec budget → Only generate adds
- No valid moves → Return empty list (triggers convergence)

---

### 4.3 Budget Tracker (Story 2.4)

**Module:** `optimizer/budget_tracker.py`

**Primary Class:** `BudgetState` (see Section 3.3)

**Key Methods:**

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

**Key Responsibilities:**
- Track unallocated vs respec points separately
- Enforce hard budget limits (prevent overspending)
- Provide budget availability queries
- Generate budget usage reports

**Invariants:**
- `unallocated_used <= unallocated_available` (always)
- `respec_used <= respec_available` (if respec not unlimited)
- Never allow mutations that violate budget

---

### 4.4 Metrics (Story 2.6)

**Module:** `optimizer/metrics.py`

**Primary Functions:**

```python
def calculate_metric(build: BuildData, metric_type: str) -> float:
    """
    Calculate optimization metric for a build.

    Metrics:
    - "dps": Total DPS output
    - "ehp": Effective Hit Points (Life + ES + mitigation)
    - "balanced": Weighted average (60% DPS, 40% EHP)

    Args:
        build: BuildData to evaluate
        metric_type: "dps" | "ehp" | "balanced"

    Returns:
        Metric value (higher is better)
    """
```

**Normalization Strategy:**

```python
def normalize_for_comparison(dps: float, ehp: float) -> Tuple[float, float]:
    """
    Normalize DPS and EHP to comparable scales for balanced metric.

    Approach:
    - DPS typical range: 10,000 - 1,000,000
    - EHP typical range: 5,000 - 50,000
    - Normalize both to 0-100 scale relative to baseline
    - Apply weights: 60% DPS, 40% EHP
    """
```

**Key Responsibilities:**
- Invoke PoB calculator for each build
- Extract relevant stats from BuildStats
- Normalize metrics for comparison
- Handle calculation errors gracefully

**Performance Considerations:**
- PoB calculation: ~2ms per build (validated in Epic 1)
- Bottleneck of entire optimization (dominates runtime)
- No caching (mutations are unique, cache hit rate ~0%)

---

### 4.5 Convergence Detector (Story 2.7)

**Module:** `optimizer/convergence.py`

**Primary Class:**

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
        """Return reason for convergence."""
```

**Convergence Conditions:**
1. **No Improvement:** No neighbor improves metric for `patience` consecutive iterations
2. **Diminishing Returns:** Improvement delta < `min_improvement` (0.1%)
3. **No Valid Neighbors:** Neighbor generator returns empty list
4. **Max Iterations:** Iteration limit reached (1000 default)
5. **Timeout:** Time limit exceeded (5 minutes default)

**Key Responsibilities:**
- Track improvement history
- Detect stagnation
- Prevent infinite loops
- Report convergence reason for debugging

---

### 4.6 Progress Tracker (Story 2.8)

**Module:** `optimizer/progress.py`

**Primary Class:**

```python
class ProgressTracker:
    """Tracks and reports optimization progress."""

    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.start_time = time.time()
        self.iteration = 0
        self.best_metric = None
        self.improvement_pct = 0.0
        self.budget_used = {"unallocated": 0, "respec": 0}

    def update(
        self,
        iteration: int,
        best_metric: float,
        improvement_pct: float,
        budget: BudgetState
    ) -> None:
        """Update progress and invoke callback."""

    def should_report(self) -> bool:
        """Check if we should report progress (every 100 iterations)."""
```

**Progress Callback Signature:**

```python
def progress_callback(
    iteration: int,
    best_metric: float,
    improvement_pct: float,
    budget_used: dict,
    time_elapsed: float
) -> None:
    """
    Called every 100 iterations to report progress.

    Epic 3 UI will consume these updates to show:
    - Progress bar (estimated % complete)
    - Current iteration / max iterations
    - Best improvement found so far
    - Budget usage
    - Time elapsed
    """
```

**Key Responsibilities:**
- Track iteration count
- Measure elapsed time
- Calculate improvement percentage
- Invoke UI callback (Story 3.5 integration)
- Rate limit updates (every 100 iterations)

---

## 5. Algorithm Flow

### 5.1 High-Level Flow

```
1. Initialize
   ├── Load passive tree (cached from Epic 1)
   ├── Calculate baseline stats
   ├── Initialize budget tracker
   ├── Initialize convergence detector
   └── Initialize progress tracker

2. Main Loop (until convergence)
   ├── Generate neighbors from current build
   │   ├── Check budget availability
   │   ├── Generate "add node" mutations
   │   ├── Generate "swap node" mutations
   │   └── Validate tree connectivity
   │
   ├── Evaluate neighbors
   │   ├── For each mutation:
   │   │   ├── Apply mutation → new BuildData
   │   │   ├── Calculate stats (PoB engine)
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
       ├── No improvement for N iterations?
       ├── Max iterations reached?
       ├── Timeout exceeded?
       └── No valid neighbors?

3. Finalize
   ├── Calculate final stats
   ├── Compute improvement percentage
   ├── Generate change summary (adds/removes/swaps)
   └── Return OptimizationResult
```

### 5.2 Detailed Pseudocode

```python
def optimize_build(config: OptimizationConfiguration) -> OptimizationResult:
    # 1. Initialize
    tree = get_passive_tree()
    baseline_stats = calculate_build_stats(config.build)
    baseline_metric = calculate_metric(config.build, config.metric)

    budget = BudgetTracker(config.unallocated_points, config.respec_points)
    convergence = ConvergenceDetector(patience=config.convergence_patience)
    progress = ProgressTracker(callback=config.progress_callback)

    current_build = config.build
    current_metric = baseline_metric
    best_build = current_build
    best_metric = current_metric

    start_time = time.time()
    iteration = 0

    # 2. Main Loop
    while iteration < config.max_iterations:
        iteration += 1

        # Check timeout
        if time.time() - start_time > config.max_time_seconds:
            convergence_reason = "timeout"
            break

        # Generate neighbors
        neighbors = generate_neighbors(current_build, tree, budget.state)

        if not neighbors:
            convergence_reason = "no_valid_neighbors"
            break

        # Evaluate neighbors
        best_neighbor = None
        best_neighbor_metric = current_metric

        for mutation in neighbors:
            candidate_build = mutation.apply(current_build)
            candidate_stats = calculate_build_stats(candidate_build)
            candidate_metric = calculate_metric(candidate_build, config.metric)

            if candidate_metric > best_neighbor_metric:
                best_neighbor = mutation
                best_neighbor_metric = candidate_metric

        # Update state
        if best_neighbor and best_neighbor_metric > current_metric:
            # Improvement found - adopt neighbor
            current_build = best_neighbor.apply(current_build)
            current_metric = best_neighbor_metric
            budget.apply_mutation(best_neighbor)

            if current_metric > best_metric:
                best_build = current_build
                best_metric = current_metric

        # Check convergence
        convergence.update(current_metric)
        if convergence.has_converged():
            convergence_reason = convergence.get_convergence_reason()
            break

        # Report progress
        if progress.should_report():
            improvement_pct = ((best_metric - baseline_metric) / baseline_metric) * 100
            progress.update(iteration, best_metric, improvement_pct, budget.state)

    # 3. Finalize
    optimized_stats = calculate_build_stats(best_build)
    improvement_pct = ((best_metric - baseline_metric) / baseline_metric) * 100

    return OptimizationResult(
        optimized_build=best_build,
        baseline_stats=baseline_stats,
        optimized_stats=optimized_stats,
        improvement_pct=improvement_pct,
        unallocated_used=budget.state.unallocated_used,
        respec_used=budget.state.respec_used,
        iterations_run=iteration,
        convergence_reason=convergence_reason,
        time_elapsed_seconds=time.time() - start_time,
        nodes_added=compute_nodes_added(config.build, best_build),
        nodes_removed=compute_nodes_removed(config.build, best_build),
        nodes_swapped=compute_nodes_swapped(config.build, best_build)
    )
```

---

## 6. Performance Budget

Based on Epic 1 performance validation and Prep Sprint profiling:

| Operation | Time per Call | Calls per Iteration | Total per Iteration |
|-----------|---------------|---------------------|---------------------|
| Generate neighbors | ~20ms | 1 | 20ms |
| Calculate stats (PoB) | ~2ms | 50-200 | 100-400ms |
| Calculate metric | ~0.01ms | 50-200 | 0.5-2ms |
| is_connected() | ~0.02ms | 100-1000 | 2-20ms |
| Other overhead | - | - | ~5ms |
| **Total per iteration** | - | - | **~130-450ms** |

**Estimated optimization times:**
- Typical build (300 iterations): 39-135 seconds (0.6-2.3 minutes)
- Complex build (1000 iterations): 130-450 seconds (2.2-7.5 minutes)

**Risk:** Complex builds may exceed 5-minute timeout with 1000 iterations.

**Mitigation:**
- Reduce max_iterations to 600 (target: <5 minutes)
- Implement adaptive convergence (stop early if improvement rate drops)
- Consider parallel evaluation of neighbors (future optimization)

---

## 7. Error Handling

### 7.1 Calculation Failures

**Issue:** PoB calculation may fail for invalid builds (rare but possible)

**Strategy:**
- Catch exceptions in metrics.calculate_metric()
- Log warning with build details
- Return -infinity metric (neighbor rejected)
- Continue with other neighbors

### 7.2 Connectivity Validation

**Issue:** Generated neighbor may have orphan nodes (algorithm bug)

**Strategy:**
- Validate connectivity before adding to neighbor list
- Use PassiveTreeGraph.validate_tree_connectivity()
- Log error if validation fails (indicates bug)
- Skip invalid neighbor

### 7.3 Budget Overrun

**Issue:** Mutation may exceed budget (algorithm bug)

**Strategy:**
- Double-check budget before applying mutation
- Raise AssertionError if budget violated (fail-fast)
- Log detailed debug info (budget state, mutation)

### 7.4 Timeout Handling

**Issue:** Optimization exceeds 5-minute limit

**Strategy:**
- Check timeout at start of each iteration
- Return partial results (best found so far)
- Set convergence_reason = "timeout"
- Display message: "Optimization timed out, showing best result found"

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Module:** `tests/unit/optimizer/`

- `test_budget_tracker.py`: Budget validation logic
- `test_convergence.py`: Convergence detection
- `test_progress.py`: Progress tracking
- `test_metrics.py`: Metric calculation (mocked calculator)

**Coverage Target:** 80%+ line coverage

### 8.2 Integration Tests

**Module:** `tests/integration/optimizer/`

- `test_neighbor_generator.py`: Generate valid neighbors, validate connectivity
- `test_hill_climbing.py`: End-to-end optimization with mocked calculator

**Test Builds:**
- Small build (50 nodes, 20 unallocated)
- Medium build (100 nodes, 10 unallocated, 10 respec)
- Large build (150 nodes, 5 respec only)

### 8.3 Performance Tests

**Module:** `tests/performance/`

- `test_optimization_speed.py`: Measure optimization time for various build sizes
- Target: Typical build completes in <2 minutes

### 8.4 Acceptance Tests

**Module:** `tests/acceptance/`

- Use test corpus from Prep Sprint Task #4
- Validate 8%+ median improvement
- Verify budget never exceeded
- Confirm convergence within 5 minutes

---

## 9. Future Enhancements (Post-MVP)

### 9.1 Algorithm Improvements

**Random Restart:** Escape local maxima by randomly jumping to different tree regions
**Simulated Annealing:** Accept worse neighbors with decreasing probability
**Genetic Algorithm:** Population-based search with crossover and mutation
**Parallel Evaluation:** Evaluate neighbors in parallel (multi-threading)

### 9.2 Performance Optimizations

**Calculation Caching:** Cache PoB results for identical builds (hash passive_nodes + items)
**Incremental Calculation:** Update stats incrementally instead of full recalculation
**Adaptive Neighbor Generation:** Reduce neighbor count when convergence likely
**GPU Acceleration:** Offload calculations to GPU (requires Lua->Python port)

### 9.3 Advanced Features

**Multi-Objective Optimization:** Optimize DPS and EHP simultaneously (Pareto frontier)
**Cluster Jewel Support:** Optimize jewel socket allocations
**Ascendancy Selection:** Recommend optimal ascendancy for build
**Path Optimization:** Find shortest path to allocated nodes (minimize travel nodes)

---

## 10. Open Questions

### 10.1 For Prep Sprint Resolution

**Q1:** Should Story 2.8 include console output or just API?
- **Answer:** TBD (Task #7 in Prep Sprint)

**Q2:** What is the exact format for test corpus builds?
- **Answer:** TBD (Task #4 - Alec to provide Maxroll builds)

**Q3:** How do we measure "8%+ median improvement" with limited test corpus?
- **Answer:** TBD (Task #5 - establish baseline stats)

### 10.2 For Story Implementation

**Q4:** Should we implement random restart in MVP or defer to post-MVP?
- **Recommendation:** Defer - hill climbing sufficient for MVP validation

**Q5:** What metrics should be exposed in progress callback?
- **Recommendation:** iteration, best_metric, improvement_pct, budget_used, time_elapsed

**Q6:** Should convergence patience be user-configurable via UI?
- **Recommendation:** No - use fixed value (3) for MVP, expose in config file

---

## 11. Acceptance Criteria Traceability

### Story 2.1: Hill Climbing Core

- ✅ Algorithm starts with current passive tree (baseline)
- ✅ Algorithm generates neighbor configurations
- ✅ Algorithm evaluates each neighbor using PoB calculations
- ✅ Algorithm selects best neighbor if improvement found
- ✅ Algorithm repeats until convergence
- ✅ Algorithm returns best configuration found

### Story 2.2: Neighbor Generation

- ✅ Generate "add node" neighbors
- ✅ Generate "swap node" neighbors
- ✅ Validate all neighbors are valid (connected tree, within budget)
- ✅ Limit neighbor count to reasonable size (50-200)
- ✅ Prioritize high-value nodes

### Story 2.3: Auto-Detect Unallocated Points

- ✅ Calculate max_points from character level
- ✅ Calculate allocated_points from passive tree
- ✅ Calculate unallocated = max - allocated
- ✅ Display auto-detected value (handled in UI)

### Story 2.4: Dual Budget Constraint

- ✅ Track unallocated_available and unallocated_used
- ✅ Track respec_available and respec_used
- ✅ Enforce unallocated_used <= unallocated_available
- ✅ Enforce respec_used <= respec_available
- ✅ Prevent moves that exceed either budget

### Story 2.5: Budget Prioritization

- ✅ Prioritize "add node" moves (use unallocated)
- ✅ Only generate "swap node" moves if unallocated exhausted
- ✅ Result breakdown shows free vs costly changes

### Story 2.6: Metric Selection

- ✅ Support "Maximize DPS"
- ✅ Support "Maximize EHP"
- ✅ Support "Balanced" (60% DPS, 40% EHP)
- ✅ Extract correct stats from PoB calculations
- ✅ Normalize metrics for comparison

### Story 2.7: Convergence Detection

- ✅ Stop when no improvement for N iterations (N=3)
- ✅ Stop when improvement delta <0.1%
- ✅ Stop when max iterations reached (1000)
- ✅ Log convergence reason

### Story 2.8: Progress Tracking

- ✅ Track current iteration number
- ✅ Track best metric value found
- ✅ Track improvement percentage vs baseline
- ✅ Track budget usage
- ✅ Provide progress callback
- ✅ Update every 100 iterations

---

## 12. Sign-Off

**Architect:** Winston (via Bob - Prep Sprint)
**Date:** 2025-10-27
**Status:** DRAFT - Ready for team review

**Next Steps:**
1. Team review of architecture (Prep Sprint standup)
2. Resolve open questions (Q1-Q3)
3. Approve architecture for Story 2.1 implementation
4. Create Story Context for Epic 2 (Task #10)

---

**Document Version History:**
- v1.0 (2025-10-27): Initial draft - Prep Sprint Task #2
