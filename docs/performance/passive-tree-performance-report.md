# PassiveTreeGraph Performance Report

**Date:** 2025-10-27
**Status:** ✅ EXCELLENT - No optimization required
**Owner:** Bob (Scrum Master) - Prep Sprint Task #1

---

## Executive Summary

PassiveTreeGraph.is_connected() performance **far exceeds** requirements for Story 2.2 (Neighbor Generation). Current BFS implementation is **27x faster** than the 0.5ms target for typical builds.

**Recommendation:** Proceed with Story 2.2 using current implementation. No optimization needed.

---

## Test Results

### Performance by Build Size

| Build Size | Allocated Nodes | Avg Time | vs Target | Status |
|------------|----------------|----------|-----------|--------|
| Small | 50 nodes | 0.0084 ms | 60x faster | ✅ PASS |
| Medium | 100 nodes | 0.0185 ms | 27x faster | ✅ PASS |
| Large | 150 nodes | 0.0328 ms | 15x faster | ✅ PASS |
| Endgame | 200 nodes | 0.0458 ms | 11x faster | ✅ PASS |
| Worst Case | 300 nodes | 0.0721 ms | 7x faster | ✅ PASS |

**Target:** <0.5ms average
**Best Case:** 0.0084 ms (Small Build)
**Worst Case:** 0.0721 ms (300-node build)

All scenarios **PASS** with significant margin.

### Performance Statistics (Medium Build, 100 nodes)

- **Average:** 0.0185 ms
- **Median:** 0.0129 ms
- **Min:** 0.0002 ms
- **Max:** 0.0824 ms
- **P95:** 0.0467 ms (95% of calls faster than this)
- **P99:** 0.0507 ms (99% of calls faster than this)
- **Throughput:** 53,995 checks/second

---

## Story 2.2 Optimization Impact

Story 2.2 (Neighbor Generation) will call `is_connected()` to validate tree connectivity. Estimated workload:

| Scenario | Total Checks | Estimated Time | Within Budget? |
|----------|--------------|----------------|----------------|
| Optimistic | 5,000 checks | 0.1s | ✅ Yes |
| Typical | 60,000 checks | 1.1s | ✅ Yes |
| Pessimistic | 1,000,000 checks | 18.5s | ✅ Yes |

**Notes:**
- Typical = 300 iterations × 100 neighbors × 2 checks/neighbor
- Pessimistic = 1000 iterations × 200 neighbors × 5 checks/neighbor
- Even pessimistic case well within 5-minute optimization timeout
- Actual optimization time dominated by PoB calculations (2ms each), not pathfinding

---

## Technical Analysis

### Current Implementation

**Algorithm:** Breadth-First Search (BFS)
**Complexity:** O(V + E) where V = allocated nodes, E = edges
**Location:** `src/calculator/passive_tree.py:94-140`

```python
def is_connected(self, from_node: int, to_node: int, allocated: Set[int]) -> bool:
    """Check if path exists from from_node to to_node using only allocated nodes."""
    # BFS implementation
    visited: Set[int] = {from_node}
    queue: deque = deque([from_node])

    while queue:
        current = queue.popleft()
        for neighbor in self.get_neighbors(current):
            if neighbor in allocated and neighbor not in visited:
                if neighbor == to_node:
                    return True
                visited.add(neighbor)
                queue.append(neighbor)
    return False
```

### Why BFS is Fast

1. **Small subgraphs:** Allocated sets (50-300 nodes) << full tree (4,118 nodes)
2. **Early termination:** BFS stops as soon as target found
3. **Efficient data structures:** Python sets (O(1) lookup), deque (O(1) append/popleft)
4. **Short paths:** Most checks involve nearby nodes (avg 5-10 hops)

### Optimization Considered (Not Needed)

**Option A: Memoization** - Cache reachable nodes from start
- **Pro:** O(1) lookups after initial computation
- **Con:** Memory overhead, cache invalidation complexity
- **Decision:** Not needed - current performance excellent

**Option B: Union-Find** - Pre-compute connected components
- **Pro:** O(α(n)) amortized per query (near-constant)
- **Con:** Requires rebuild on every tree mutation
- **Decision:** Not needed - current performance excellent

**Option C: Distance Matrix** - Pre-compute all-pairs connectivity
- **Pro:** O(1) lookups
- **Con:** O(n²) space and computation
- **Decision:** Not needed - current performance excellent

---

## Test Methodology

**Script:** `tests/performance/profile_passive_tree.py`

**Approach:**
1. Load PoE 2 passive tree (4,118 nodes, 4,950 edges)
2. Generate connected subgraphs of varying sizes (50-300 nodes)
3. Profile 1,000 `is_connected()` calls per scenario
4. Measure: avg, median, min, max, P95, P99 times

**Workload Simulation:**
- Random target nodes within allocated set
- Checks from Witch starting node (representative class)
- Realistic connectivity patterns (BFS expansion from start)

---

## Conclusion

PassiveTreeGraph performance is **EXCELLENT**. No optimization required for Epic 2.

**Story 2.2 Implementation:**
- Use current `is_connected()` implementation as-is
- No need for caching, memoization, or alternative algorithms
- Performance budget: ~1-2 seconds for pathfinding in typical optimization
- Remaining 5-10 seconds budget available for calculation and algorithm logic

**Prep Sprint Status:** ✅ COMPLETE - No blockers for Story 2.2

---

**Profiled by:** Bob (Scrum Master)
**Date:** 2025-10-27
**Prep Sprint Task:** #1 COMPLETED
**Next Steps:** Proceed with Story 2.2 implementation
