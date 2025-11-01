# Hill Climbing Strategy for Passive Tree Optimization

**Purpose:** Research and strategy document for Stories 2.1-2.2
**Author:** Bob (Scrum Master) - Prep Sprint Task #6
**Date:** 2025-10-27
**Status:** APPROVED for implementation

---

## 1. Executive Summary

This document outlines the hill climbing algorithm strategy for PoE 2 passive tree optimization, based on research of optimization techniques, local search strategies, and neighbor pruning methods.

**Selected Approach:** **Steepest-Ascent Hill Climbing** with **First-Improvement Pruning** and **Priority-Based Neighbor Generation**

**Rationale:**
- Steepest-ascent ensures we always move to the best available neighbor (quality)
- First-improvement pruning reduces computation time when early neighbors are good
- Priority-based generation focuses search on high-value moves (efficiency)

---

## 2. Algorithm Variants Considered

### 2.1 Simple Hill Climbing

**Definition:** Move to the FIRST neighbor that improves the evaluation function.

**Pros:**
- Fast - minimal neighbor evaluation
- Low memory usage

**Cons:**
- May miss better neighbors in the same iteration
- Greedy - can converge to weaker local maxima

**Decision:** ❌ Not suitable - sacrifices too much quality for speed

---

### 2.2 Steepest-Ascent Hill Climbing

**Definition:** Evaluate ALL neighbors, select the one with GREATEST improvement.

**Pros:**
- Finds best possible single-step move
- Robust - converges to strongest accessible local maximum
- Predictable behavior

**Cons:**
- Slower - must evaluate all neighbors before moving
- May evaluate 100-200 neighbors per iteration

**Decision:** ✅ **SELECTED** - Best balance of quality and predictability

**Justification:**
- Performance validated: 2ms per calculation × 200 neighbors = ~400ms/iteration (acceptable)
- Quality critical for MVP validation ("8%+ median improvement" success criteria)
- Steepest-ascent most commonly used in production optimization systems

---

### 2.3 Stochastic Hill Climbing

**Definition:** Select neighbors RANDOMLY, move if improvement found.

**Pros:**
- Fast - can stop after finding ANY improvement
- Can sometimes escape local optima via randomness

**Cons:**
- Non-deterministic - same build may get different results
- May miss best neighbors
- Harder to debug

**Decision:** ❌ Not suitable for MVP - prefer deterministic behavior

---

### 2.4 First-Choice Hill Climbing

**Definition:** Generate neighbors randomly until a better one is found, then move.

**Pros:**
- Excellent for large neighbor spaces (1000+ neighbors)
- Fast when good neighbors are common

**Cons:**
- Worst-case: must generate many neighbors before finding improvement
- Non-deterministic

**Decision:** ❌ Not needed - our neighbor space is manageable (50-200 neighbors)

---

## 3. Selected Algorithm: Steepest-Ascent with Optimizations

### 3.1 Core Algorithm

```python
def optimize(build, metric, budget):
    current_build = build
    current_metric = evaluate(build, metric)

    while not converged:
        # Generate all valid neighbors
        neighbors = generate_neighbors(current_build, budget)

        # Evaluate all neighbors
        best_neighbor = None
        best_metric = current_metric

        for neighbor in neighbors:
            neighbor_metric = evaluate(neighbor, metric)
            if neighbor_metric > best_metric:
                best_neighbor = neighbor
                best_metric = neighbor_metric

        # Move to best neighbor if improvement found
        if best_neighbor:
            current_build = best_neighbor
            current_metric = best_metric
        else:
            break  # Converged - no improvement found

    return current_build
```

### 3.2 Optimization: Early Termination

**Strategy:** **Adaptive First-Improvement**

If we find a neighbor with **significant improvement** early, we can optionally stop evaluation and move immediately.

**Definition of Significant:**
- Improvement > 5% for current metric
- OR: Improvement > 2× average recent improvement

**Implementation:**

```python
# In neighbor evaluation loop
if neighbor_metric > current_metric * 1.05:  # 5% improvement
    # Significant improvement found - can terminate early
    # Optional: Only use if iteration count high and time pressure
    best_neighbor = neighbor
    break
```

**Decision:** ⚠️ Implement as **optional flag** `enable_early_termination=False`
- Default OFF for MVP (prioritize quality)
- Can enable for performance testing
- Future: Enable if timeout approaching (adaptive optimization)

---

## 4. Neighbor Generation Strategy (Story 2.2)

### 4.1 Neighbor Types

**Type 1: Add Node** (costs unallocated points)
- Allocate any unallocated, connected node
- Budget: 1 unallocated point
- Example: Current has {A, B, C}, add D (connected to C) → {A, B, C, D}

**Type 2: Swap Node** (costs respec points)
- Remove 1 node, add 1 connected node
- Budget: 1 respec point
- Example: Current has {A, B, C}, remove C, add D (connected to B) → {A, B, D}

### 4.2 Generation Order: **Free-First Strategy**

**Priority 1:** Generate ALL "add node" neighbors first
- Uses free budget (unallocated points)
- Maximum value for user (no currency cost)

**Priority 2:** Generate "swap node" neighbors only if:
- Unallocated points exhausted (all spent)
- OR: No valid "add node" neighbors found
- Respec budget still available

**Rationale:**
- Story 2.5 AC: "Only generate swap moves if unallocated exhausted"
- Delivers maximum free value before using costly respecs

**Implementation:**

```python
def generate_neighbors(build, tree, budget):
    neighbors = []

    # Priority 1: Add nodes (free)
    if budget.can_allocate():
        add_neighbors = generate_add_neighbors(build, tree)
        neighbors.extend(add_neighbors)

    # Priority 2: Swap nodes (costly)
    # Only if no unallocated budget OR no valid adds found
    if budget.can_respec() and (not budget.can_allocate() or len(neighbors) == 0):
        swap_neighbors = generate_swap_neighbors(build, tree, budget)
        neighbors.extend(swap_neighbors)

    return neighbors
```

---

## 5. Neighbor Pruning Techniques

### 5.1 Pruning Goal

**Problem:** Passive tree has 4,118 nodes. Even with connectivity constraints, we might generate 500+ neighbors per iteration.

**Target:** Limit to 50-200 neighbors per iteration for reasonable performance.

**Strategy:** Multi-level pruning based on node value and reachability.

---

### 5.2 Level 1: Connectivity Pruning (Mandatory)

**Rule:** Only generate neighbors that maintain tree connectivity.

**Implementation:**
- For "add node": Node must be connected to existing allocated set
- For "swap node": Removing node must not orphan other nodes

**Expected Reduction:** ~95% of nodes (only ~200-300 nodes adjacent to allocated set)

**Code:**

```python
def get_valid_add_candidates(build, tree):
    """Get all unallocated nodes adjacent to allocated set."""
    candidates = set()
    for allocated_node in build.passive_nodes:
        for neighbor in tree.get_neighbors(allocated_node):
            if neighbor not in build.passive_nodes:
                candidates.add(neighbor)
    return candidates
```

---

### 5.3 Level 2: Value-Based Prioritization (Recommended)

**Rule:** Prioritize high-value nodes over low-value travel nodes.

**Node Value Hierarchy:**
1. **Keystone** (highest value) - Major unique mechanics
2. **Notable** (high value) - Significant stat boosts
3. **Small Passive** (medium value) - Minor stat boosts
4. **Travel Node** (low value) - +10 to single stat

**Strategy:** **Top-K Selection**

Generate ALL valid candidates, rank by value, select **Top 100**.

**Implementation:**

```python
def prioritize_candidates(candidates, tree):
    """Rank candidates by node value."""
    def node_value(node_id):
        node = tree.nodes[node_id]
        if node.is_keystone:
            return 100
        elif node.is_notable:
            return 50
        elif len(node.stats) > 1:  # Multi-stat small passive
            return 20
        else:  # Travel node
            return 5

    # Sort by value descending
    ranked = sorted(candidates, key=node_value, reverse=True)

    # Take Top 100
    return ranked[:100]
```

**Expected Reduction:** 200-300 candidates → 100 candidates (50% reduction)

---

### 5.4 Level 3: Path Efficiency Filtering (Future Enhancement)

**Rule:** Prefer nodes that provide value per pathing cost.

**Metric:** Value / Distance from current allocated set

**Example:**
- Keystone 10 nodes away: Value=100, Distance=10 → Score=10
- Notable 2 nodes away: Value=50, Distance=2 → Score=25 (better!)

**Decision:** ⚠️ **Defer to post-MVP**
- Adds complexity (pathfinding for each candidate)
- Performance cost: ~0.02ms × 200 candidates = 4ms per iteration
- Benefit unclear without testing

**Future Work:** Implement if testing shows algorithm allocates too many travel nodes

---

## 6. Convergence Criteria (Story 2.7)

### 6.1 Primary Criterion: **No Improvement**

**Rule:** Stop when no neighbor improves metric for **N consecutive iterations**.

**N = 3** (patience parameter)

**Rationale:**
- N=1: Too aggressive - may stop at weak local maximum
- N=3: Balanced - gives algorithm chance to escape plateaus
- N=5: Too patient - wastes time when truly converged

**Code:**

```python
iterations_without_improvement = 0
while iterations_without_improvement < 3:
    best_neighbor = find_best_neighbor(...)
    if best_neighbor improves metric:
        iterations_without_improvement = 0
    else:
        iterations_without_improvement += 1
```

---

### 6.2 Secondary Criteria

**Criterion 2:** **Diminishing Returns**
- Stop if improvement < 0.1% (negligible for user)
- Example: 100,000 DPS → 100,100 DPS (+0.1%)

**Criterion 3:** **Max Iterations**
- Hard limit: 1000 iterations
- Prevents infinite loops
- Typical convergence: 200-500 iterations

**Criterion 4:** **Timeout**
- Hard limit: 5 minutes (300 seconds)
- Graceful degradation: Return best found so far
- Story 3.9 requirement

**Criterion 5:** **No Valid Neighbors**
- Stop if neighbor generator returns empty list
- Indicates budget exhausted or all moves invalid

---

## 7. Expected Performance

### 7.1 Iteration Budget

Based on Epic 1 performance and prep sprint profiling:

| Operation | Time | Calls/Iter | Total/Iter |
|-----------|------|------------|------------|
| Generate neighbors | ~20ms | 1 | 20ms |
| Evaluate neighbors (PoB) | 2ms | 50-200 | 100-400ms |
| Update state | ~5ms | 1 | 5ms |
| **Total per iteration** | - | - | **125-425ms** |

**Estimated Optimization Times:**
- Typical (300 iterations): 37-127 seconds (0.6-2.1 minutes)
- Complex (1000 iterations): 125-425 seconds (2.1-7.1 minutes)

### 7.2 Risk: Timeout

**Problem:** Complex builds may exceed 5-minute timeout at 1000 iterations.

**Mitigation Options:**

**Option A:** Reduce max_iterations to 600
- Ensures timeout compliance: 600 × 0.425s = 255s (~4.25 min)
- May sacrifice some quality

**Option B:** Adaptive iteration limit
- Start with 1000
- If average iteration time > 250ms, reduce limit to 600
- Dynamically adjust based on performance

**Option C:** Early termination when improvement rate drops
- Track: improvement per iteration over last 50 iterations
- If rate < 0.1% per iteration, stop early
- Assumes diminishing returns = near convergence

**Decision:** ✅ **Option A** for MVP (simple, safe)
- Future: Implement Option C if timeout issues observed

---

## 8. Pseudo-Local Optima Problem

### 8.1 Problem Statement

**Issue:** Hill climbing can get stuck at local maxima.

**Example:**
- Current build: 100k DPS (local maximum)
- Better build exists: 120k DPS (global maximum)
- But reaching it requires passing through worse builds temporarily

**Impact:** May not find best possible optimization.

### 8.2 Mitigation: Out of Scope for MVP

**Strategies Considered:**

**Random Restart:**
- Periodically jump to random tree location
- Explore multiple local maxima, return best
- **Cost:** 2-5× runtime (run optimization 2-5 times)

**Simulated Annealing:**
- Accept worse neighbors with decreasing probability
- Allows escape from local maxima
- **Complexity:** Adds hyperparameter tuning (temperature schedule)

**Genetic Algorithm:**
- Population-based search
- Combines multiple builds (crossover)
- **Complexity:** Major architecture change

**Decision:** ❌ **Defer all to post-MVP**

**Rationale:**
- MVP goal: Prove concept works (any improvement > 0%)
- Local maximum still better than user's manual allocation
- Success criteria: 8%+ median improvement (likely achievable with simple hill climbing)
- If MVP testing shows local maxima problem, implement Random Restart in v2

---

## 9. Implementation Checklist

### Story 2.1: Hill Climbing Core

- [ ] Implement steepest-ascent main loop
- [ ] Integrate convergence detector (Story 2.7)
- [ ] Integrate progress tracker (Story 2.8)
- [ ] Add optional early termination flag (default OFF)
- [ ] Unit tests: Mock neighbor generator and metrics

### Story 2.2: Neighbor Generation

- [ ] Implement `get_valid_add_candidates()` (connectivity pruning)
- [ ] Implement `generate_add_neighbors()` (add node mutations)
- [ ] Implement `generate_swap_neighbors()` (swap node mutations)
- [ ] Implement `prioritize_candidates()` (value-based ranking)
- [ ] Implement free-first strategy (adds before swaps)
- [ ] Limit neighbors to Top 100 after prioritization
- [ ] Validate tree connectivity for all generated neighbors
- [ ] Integration tests: Use real passive tree, verify validity

### Performance Validation

- [ ] Profile neighbor generation time (target: <50ms)
- [ ] Profile full iteration time (target: <500ms average)
- [ ] Test optimization on test corpus (once Task #4 complete)
- [ ] Verify convergence within 5 minutes for all builds

---

## 10. Open Questions

**Q1:** Should we implement "path efficiency filtering" (Level 3 pruning) in MVP?
- **Answer:** No - defer to post-MVP unless testing shows excessive travel node allocation

**Q2:** What max_iterations value should we use?
- **Answer:** 600 (ensures <5 min timeout with safety margin)

**Q3:** Should early termination be user-configurable?
- **Answer:** No - hidden flag for development testing only

**Q4:** How do we handle "no valid neighbors" edge case?
- **Answer:** Treat as convergence, return current build (already in architecture doc)

---

## 11. Success Criteria Alignment

### Epic 2 Success Criteria

✅ **Find improvements for 80%+ of non-optimal builds**
- Steepest-ascent explores all neighbors → maximizes improvement chance

✅ **Median improvement: 8%+ for builds with budget headroom**
- Prioritization focuses on high-value nodes → maximizes metric gains

✅ **Complete within 5 minutes**
- Max 600 iterations × 425ms = 255s = 4.25 min (within budget)

✅ **Never exceed budget constraints**
- Budget validation before generating neighbors → hard enforcement

---

## 12. References

### Research Sources

1. **Hill Climbing in AI: 2025 Guide & Examples** - https://futurense.com/blog/hill-climbing-in-ai
2. **Hill Climbing in Artificial Intelligence** - GeeksforGeeks
3. **Local Search Optimization** - Wikipedia, Carnegie Mellon University
4. **Neighbor Pruning Techniques** - ScienceDirect Topics, Stanford Graphics

### Internal Documents

- `docs/architecture/epic-2-optimizer-design.md` - Architecture specification
- `docs/retrospectives/epic-001-retro-2025-10-27.md` - Epic 1 learnings
- `docs/performance/passive-tree-performance-report.md` - Performance validation

---

**Reviewed by:** Bob (Scrum Master)
**Date:** 2025-10-27
**Status:** APPROVED for Story 2.1-2.2 implementation
**Next Steps:** Begin Story 2.1 after Prep Sprint complete
