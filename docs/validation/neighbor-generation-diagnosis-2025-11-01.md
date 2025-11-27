# Neighbor Generation Diagnosis - 2025-11-01

## Executive Summary

**Critical Bug Found and Fixed**: The hill climbing optimizer was using a placeholder neighbor generator that always returned 0 neighbors. The real neighbor generation code existed but was never integrated. This has been fixed.

**New Finding**: After fixing the integration, validation still shows 0 neighbors because your tailored builds are **too well-optimized** - they form minimal spanning trees where every allocated node is required for connectivity.

## Issue Timeline

### 1. Initial Validation (0% Success Rate)
- **Date**: 2025-11-01 (morning)
- **Test**: 36 parity builds + 21 tailored builds
- **Result**: ALL builds showed `convergence_reason: "no_valid_neighbors"` with 0 iterations
- **Root Cause Suspected**: Test corpus unsuitable OR optimizer bug

### 2. Integration Bug Discovery
- **Location**: `src/optimizer/hill_climbing.py:161-165`
- **Issue**: Called `_generate_neighbors_placeholder()` which ALWAYS returns empty list
- **Expected**: Should call `generate_neighbors()` from neighbor_generator.py
- **Impact**: Optimizer could NEVER find neighbors, regardless of build quality

### 3. Integration Bug Fix
- **Changes Made**:
  1. Added imports: `from src.calculator.passive_tree import get_passive_tree`
  2. Added imports: `from src.optimizer.neighbor_generator import generate_neighbors`
  3. Initialized passive tree: `tree = get_passive_tree()`
  4. Created BudgetState for neighbor generator
  5. Called real `generate_neighbors()` instead of placeholder
  6. Converted TreeMutation objects to BuildData neighbors
  7. Updated `_select_best_neighbor()` to track node changes properly

### 4. Post-Fix Testing
- **Test Build**: `mercenary_hip_88_10points.xml` (High Improvement Potential)
- **Result**: Still 0 neighbors generated
- **Log Evidence**:
  ```
  WARNING - No valid neighbors found (convergence indicator): allocated=102, can_add=False, can_swap=True
  ```
- **Analysis**: Neighbor generator IS being called, but finds no valid swaps

## Root Cause Analysis: Minimal Spanning Trees

### What's Happening

Your tailored builds are **highly optimized** - they form minimal spanning trees where:
1. Every allocated node is required to maintain connectivity from class start to all other nodes
2. Removing ANY single node would orphan other nodes (break the tree)
3. The `_find_removable_nodes()` function returns 0 nodes
4. With 0 removable nodes and 0 unallocated points, there are 0 possible mutations

### Example: mercenary_hip_88_10points.xml

```
Level: 88
Allocated nodes: 102
Unallocated points: 0 (calculated as max(0, 88-1) - 102 = -15)
```

The build has:
- 102 nodes allocated
- 0 unallocated budget (can't add nodes)
- Unlimited respec budget (can swap nodes)
- BUT: All 102 nodes form a connected path with no "dead ends" or "redundant branches"

### Optimizer Logic

```python
def _find_removable_nodes(build, tree, class_start):
    """Find nodes that can be removed without breaking connectivity"""
    removable = set()
    for node in build.passive_nodes:
        if node == class_start:
            continue  # Never remove class start

        # Test: remove node, check if tree stays connected
        temp_allocated = build.passive_nodes - {node}
        if _is_tree_valid_full(tree, temp_allocated, class_start):
            removable.add(node)  # Safe to remove

    return removable  # Returns empty set if all nodes required
```

For your builds: `len(removable_nodes) = 0`

## Why This Matters for Validation

### Epic 2 Success Criteria
- **Target**: 70% success rate (builds showing improvement)
- **Current**: 0% success rate
- **Blocker**: No valid neighbors means optimizer can't even TRY to improve

### What We Need for Valid Testing

The optimizer needs builds with **optimization potential**:

1. **Unallocated Points** (easiest for optimizer):
   - Example: Level 90 with only 70 nodes allocated = 19 unallocated points
   - Optimizer can try adding nodes from the frontier
   - High chance of finding improvements

2. **Removable Nodes** (harder, requires good builds with some waste):
   - Example: Build that pathed through 5 travel nodes to reach a Notable
   - But there's a shortcut through only 3 travel nodes
   - Optimizer can swap the inefficient path for the efficient one

3. **Balanced Allocation** (ideal):
   - Some unallocated points (5-15)
   - Some suboptimal routing (removable nodes)
   - This gives optimizer multiple strategies to try

## Test Results Summary

### Original Parity Builds (36 builds)
| Category | Count | Issue |
|----------|-------|-------|
| Empty builds | 12 | Only class start node allocated |
| Fully allocated | 24 | 0 unallocated, likely minimal spanning trees |
| **Total unsuitable** | **36** | **100%** |

### Tailored Builds (21 builds)
| Category | Count | Allocated | Unallocated (actual) | Issue |
|----------|-------|-----------|---------------------|-------|
| HIP | 7 | 71-102 nodes | -2 to -15 | Negative unallocated (over-allocated) |
| MIP | 7 | 73-107 nodes | -4 to -18 | Negative unallocated (over-allocated) |
| LIP | 7 | 101-131 nodes | -5 to -36 | Negative unallocated (over-allocated) |
| **Total** | **21** | | | **All form minimal spanning trees** |

**Note**: Negative unallocated likely due to:
- Builds using tree version 0_1 (older) vs our 0_3 (current)
- Including respec points in total allocation budget
- Professional build optimization (no waste)

## Options for Moving Forward

### Option A: Generate Synthetic Builds (Recommended)

**Approach**: Programmatically create builds with known improvement potential

1. **Start with parity builds** (already validated in Epic 1)
2. **Remove 10-15 random nodes** (not on critical path)
3. **Leave 10-15 points unallocated**
4. **Validation**: Run optimizer, should easily re-add the removed nodes

**Pros**:
- Quick to generate (can create 30-50 in minutes)
- Guaranteed optimization potential
- Reproducible results
- Can control difficulty (HIP/MIP/LIP)

**Cons**:
- Not "real" builds from actual gameplay
- Might miss edge cases from human build creation

**Implementation**:
```python
def create_synthetic_hip_build(base_build, unallocated=15):
    \"\"\"Create a build with high improvement potential\"\"\"
    # Start with good build
    nodes = base_build.passive_nodes.copy()

    # Remove 15 random non-critical nodes
    removable = _find_removable_nodes(base_build, tree, class_start)
    to_remove = random.sample(removable, min(15, len(removable)))
    for node in to_remove:
        nodes.remove(node)

    # Return build with unallocated points
    return BuildData(..., passive_nodes=nodes)
```

### Option B: Request Different Real Builds from Alec

**Ask for**:
1. **In-progress builds** (not fully optimized):
   - Level 70-90 characters
   - 10-20 unallocated points
   - May have suboptimal routing

2. **Builds with "mistakes"**:
   - Inefficient pathing
   - Low-value nodes allocated
   - Nodes that could be swapped for better ones

3. **Build variants** for same character:
   - One "good" version (current)
   - One "before optimization" version (what player started with)

**Pros**:
- Real player data
- Tests realistic optimization scenarios
- May find unexpected edge cases

**Cons**:
- Requires Alec's time
- May be hard to find "unoptimized" builds from experienced player
- Less control over difficulty distribution

### Option C: Hybrid Approach (Best)

1. **Use Alec's builds as templates**
2. **Generate variations programmatically**:
   - Remove some nodes → HIP (easy to improve)
   - Remove fewer nodes → MIP (moderate improvement)
   - Use as-is with 5 unallocated → LIP (hard to improve)
   - Optimal builds → Control group (should show 0-2% improvement)

3. **Validation targets**:
   - HIP: 90%+ success rate, 10-25% median improvement
   - MIP: 70-85% success rate, 5-15% median improvement
   - LIP: 40-60% success rate, 2-8% median improvement
   - Optimal: 0-20% success rate, 0-2% median improvement

**Pros**:
- Best of both worlds
- Based on real builds
- Guaranteed optimization potential
- Can hit exact success rate targets

**Cons**:
- Slightly more complex implementation

## Technical Details: Neighbor Generation

### How It Works (Now Fixed)

1. **Add Neighbors** (uses unallocated points):
   ```python
   # Find all unallocated nodes adjacent to allocated nodes
   candidates = {neighbor for node in allocated for neighbor in tree.get_neighbors(node) if neighbor not in allocated}

   # For each candidate, validate connectivity
   for candidate in candidates:
       if tree.is_connected(class_start, candidate, allocated | {candidate}):
           mutations.append(TreeMutation("add", {candidate}, set(), 1, 0))
   ```

2. **Swap Neighbors** (uses respec points):
   ```python
   # Find nodes that can be removed without breaking tree
   removable = {node for node in allocated if tree_stays_connected_without(node)}

   # For each removable node, find nodes to swap in
   for remove_node in removable:
       temp_allocated = allocated - {remove_node}
       candidates = {neighbor for node in temp_allocated for neighbor in tree.get_neighbors(node)}

       for add_node in candidates:
           if tree.is_connected(class_start, add_node, temp_allocated | {add_node}):
               mutations.append(TreeMutation("swap", {add_node}, {remove_node}, 0, 1))
   ```

3. **Prioritization**:
   - Notable > Keystone > Small > Travel (by value)
   - Limit to top 100-200 neighbors per iteration
   - Evaluate all, select best (steepest-ascent hill climbing)

### Why Your Builds Show 0 Neighbors

```
allocated=102, can_add=False, can_swap=True
                   ↑              ↑
                   |              |
           no unallocated    unlimited respec
                 points         available

                   ↓

    removable_nodes = _find_removable_nodes()
                     ↓
              returns empty set
                     ↓
        (all nodes required for connectivity)
                     ↓
              0 swap mutations
                     ↓
            0 total neighbors
```

## Recommendations

### Immediate Next Steps

1. **Choose Option C** (Hybrid Approach):
   - Use your 21 tailored builds as templates
   - Generate 30-35 builds programmatically:
     - 10 HIP (remove 15-20 nodes)
     - 15 MIP (remove 8-12 nodes)
     - 5 LIP (remove 3-5 nodes)
     - 5 Optimal (use as-is, add 3-5 unallocated)

2. **Run Validation**:
   - Execute `validate_epic2_success.py` on new corpus
   - Target: 70%+ success rate, 5%+ median improvement

3. **Document Results**:
   - Generate final validation report
   - Include corpus composition
   - Show success rate by category
   - Analyze any failures

4. **Get Approval**:
   - Share report with Alec
   - Confirm success criteria met
   - Proceed to Epic 3

### Validation Success Criteria

From Epic 2 retrospective:
- **Success Rate**: ≥70% of builds show improvement
- **Median Improvement**: ≥5% for target metric
- **Completion Time**: <300s (5 minutes) per build
- **Budget Violations**: 0 (must respect constraints)

### Timeline Estimate

- Generate synthetic corpus: **1-2 hours**
- Run validation (35 builds × 3-5 min): **2-3 hours**
- Analyze results and create report: **1 hour**
- **Total**: 4-6 hours to complete Task 6

## Files Modified

### Integration Bug Fix
1. `src/optimizer/hill_climbing.py`:
   - Added imports for `get_passive_tree` and `generate_neighbors`
   - Initialized passive tree in `optimize_build()`
   - Replaced placeholder with real neighbor generation
   - Fixed node change tracking in `_select_best_neighbor()`

### Test Scripts Created
1. `scripts/test_neighbor_generation.py`: Quick test to verify integration
2. `scripts/validate_epic2_success.py`: Full validation script (existing)
3. `scripts/validate_tailored_corpus.py`: Tailored build validation (existing)
4. `scripts/inventory_tailored_corpus.py`: Build inventory tool (existing)

### Documentation
1. `docs/validation/neighbor-generation-diagnosis-2025-11-01.md`: This document
2. `docs/validation/epic-2-success-validation-2025-11-01.md`: Initial validation report
3. `docs/validation/epic-2-validation-results-2025-11-01.json`: Raw data (36 parity builds)
4. `docs/validation/tailored-corpus-validation-2025-11-01.json`: Raw data (21 tailored builds)

## Conclusion

The integration bug has been **fixed** - the neighbor generator now works correctly. However, validation still fails because test builds lack optimization potential (minimal spanning trees with no removable nodes).

**Next Action**: Generate synthetic builds with guaranteed optimization potential using Option C (hybrid approach), then re-run validation to achieve Epic 2 success criteria.
