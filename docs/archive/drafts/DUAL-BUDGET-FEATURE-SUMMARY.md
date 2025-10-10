# Dual-Budget Feature Summary

**Feature:** Unallocated Points + Respec Points Budget System
**Added:** 2025-10-08 (PRD enhancement based on user feedback)
**Impact:** Critical UX improvement - distinguishes FREE vs COSTLY optimizations

---

## Problem Statement

**Original Design (Single Budget):**
- Only tracked "respec points" (currency to deallocate nodes)
- Didn't account for unallocated passive points (free to allocate)
- Users with 15 unallocated + 12 respec points were treated same as users with 0 unallocated + 12 respec
- Missed opportunity for immediate value delivery (free allocations)

**User Insight:**
> "What about just unallocated points available? If the player has 15 points to put in still and can respec on top of that, this might be important."

---

## Solution: Dual-Budget System

### Two Separate Constraints

**1. Unallocated Points (U) - FREE**
- Points earned through leveling but not yet spent
- Cost: $0 in-game currency
- Detection: Auto-calculated from `character_level - currently_allocated_points`
- Priority: Use FIRST (maximize free value)

**2. Respec Points (R) - COSTLY**
- Currency to deallocate already-allocated nodes
- Cost: 2-4 hours farming per 15-25 respec points
- Detection: User input (cannot auto-detect from PoB code)
- Priority: Use SECOND (minimize expensive changes)

### Optimization Strategy

```
Priority 1: Allocate unallocated points (U) for maximum gain
  → Adds up to U new nodes at ZERO cost
  → Immediate value delivery

Priority 2: Use respec points (R) if additional improvement possible
  → Deallocates up to R suboptimal nodes
  → Reallocates better nodes in their place
  → Costs valuable in-game currency

Goal: Maximize performance improvement while minimizing respec cost
```

---

## User Experience Impact

### Scenario Comparison

**Before (Single Budget):**
```
User: Level 85, has 15 unallocated + 12 respec points
System: "Enter respec budget: [12]"
Result: Uses 12 respec points, ignores 15 free points sitting unused
Outcome: Suboptimal - missed free value
```

**After (Dual Budget):**
```
User: Level 85, has 15 unallocated + 12 respec points
System:
  "Unallocated points: [15] (auto-detected)"
  "Respec points: [12]"
Result:
  • Used 15 of 15 unallocated points (FREE)
  • Used 4 of 12 respec points (costly)
Outcome: +18% DPS using 15 free + 4 respec instead of 0 free + 12 respec
```

### Value Delivered

**Immediate Value (Free Allocations):**
- User can implement unallocated node allocations RIGHT NOW
- No in-game currency cost
- No "respec anxiety"
- Typical gain: 5-12% improvement from free allocations alone

**Deferred Value (Respec Suggestions):**
- User can save respec suggestions for later
- Implements when they earn more respec points
- Full optimization available when budget permits

---

## Implementation Details

### FR-2.2: Budget Constraint (Dual Input)

**UI Components:**
```html
<div class="budget-inputs">
  <label>Unallocated Points Available
    <input type="number" id="unallocated" value="15" />
    <span class="helper">Auto-detected from your build. Edit if wrong.</span>
  </label>

  <label>Respec Points Available
    <input type="number" id="respec" placeholder="Leave blank for unlimited" />
    <span class="helper">Currency to remove already-spent points</span>
    <div class="quick-select">
      <button>[Free (0)]</button>
      <button>[Budget (15)]</button>
      <button>[Unlimited]</button>
    </div>
  </label>
</div>
```

**Auto-Detection Logic:**
```python
def detect_unallocated_points(pob_data):
    character_level = pob_data['level']
    max_points = get_max_passive_points(character_level)  # e.g., level 85 = 113 points
    allocated_points = count_allocated_nodes(pob_data['tree'])
    unallocated = max(0, max_points - allocated_points)
    return unallocated
```

### FR-4.3: Budget Enforcement (Dual Constraint)

**Tracking During Optimization:**
```python
class OptimizationBudget:
    def __init__(self, unallocated: int, respec: Optional[int]):
        self.unallocated_available = unallocated
        self.respec_available = respec  # None = unlimited

        self.unallocated_used = 0
        self.respec_used = 0

    def can_allocate_new_node(self) -> bool:
        return self.unallocated_used < self.unallocated_available

    def can_deallocate_node(self) -> bool:
        if self.respec_available is None:
            return True  # Unlimited
        return self.respec_used < self.respec_available

    def allocate_new_node(self):
        if self.can_allocate_new_node():
            self.unallocated_used += 1
        else:
            raise BudgetExceededError("No unallocated points remaining")

    def deallocate_node(self):
        if self.can_deallocate_node():
            self.respec_used += 1
        else:
            raise BudgetExceededError("No respec points remaining")
```

### Results Display

**Budget Usage Breakdown:**
```
Budget Usage:
• Unallocated points: Used 15 of 15 available (all used) ✓
• Respec points: Used 4 of 12 available (8 remaining) ✓

Changes:
• 15 new nodes allocated (FREE - used your unspent points!)
• 4 nodes deallocated and replaced (costs 4 respec points)
• Total nodes changed: 19

Cost Summary:
→ You got 15 free allocations worth ~10% DPS boost
→ Plus 4 respec changes worth ~5% additional boost
→ Total improvement: +15.2% DPS for only 4 respec points!
```

---

## User Journey Impact

### Journey 1: Marcus (Level 92, Maxed Out)
```
Before: Unallocated=0, Respec=12
Result: 6 respec changes → +8.2% DPS
Impact: NO CHANGE (already maxed, dual budget doesn't apply)
```

### Journey 2: Sarah (Level 58, Leveling)
```
Before: Only entered respec budget, missed 11 unallocated points
Result: Suggested 11 respecs she couldn't afford

After: Auto-detected 11 unallocated points
Result:
  • Immediate: 11 FREE allocations → +11% DPS (implemented right away!)
  • Deferred: 8 respec suggestions (saved for later)
Impact: IMMEDIATE VALUE instead of "unusable suggestions"

Return Visit (Level 68):
  • Auto-detected 10 more unallocated points (leveled 58→68)
  • Used 10 FREE + 5 respec → +17% DPS
Impact: BECAME PROMOTER (NPS 7→8) due to better UX
```

### Journey 3: Typical Leveling Player
```
Scenario: Level 75, has 8 unallocated + 6 respec
Old system: Might only use 6 respec, ignore 8 free points
New system:
  • Use 8 FREE allocations first → +6% DPS (no cost!)
  • Then use 3 respec for additional +4% DPS
  • Total: +10% DPS for only 3 respec instead of 6
Impact: 50% cost reduction (3 vs 6 respec) for better results
```

---

## Technical Considerations

### Auto-Detection Accuracy

**Expected Accuracy: 90%+**

**Why it might be wrong:**
- PoB code from old PoE 1 (different level/point formula)
- Custom passive tree mods (not standard tree)
- Quest reward points not accounted for

**Solution:**
- Make field editable (user can correct if wrong)
- Show calculation: "Detected: 15 (level 85, 98/113 allocated)"
- Allow manual override

### Performance Impact

**Additional Calculations:**
- Auto-detection: +10ms (negligible)
- Dual constraint tracking: +5ms per iteration (negligible)
- Total impact: <1% optimization time increase

**Complexity Impact:**
- Algorithm complexity: Same (still hill climbing)
- Constraint checks: 2x instead of 1x (trivial CPU cost)
- Code maintainability: Slightly more complex but well-documented

---

## Success Metrics

**Auto-Detection Accuracy:**
- Target: 90%+ of PoB codes correctly detect unallocated points
- Measure: Log actual vs detected, user manual overrides

**User Value:**
- Metric: % of optimizations that deliver immediate value (free allocations >0)
- Target: 60%+ of users have unallocated points to use
- Hypothesis: Leveling players (L40-95) most common users

**Cost Efficiency:**
- Metric: Average respec points used with dual budget vs single budget
- Target: 30% reduction in respec cost for same performance gain
- Measure: A/B test or before/after comparison

**User Satisfaction:**
- Metric: NPS improvement
- Hypothesis: Users with unallocated points become Promoters (NPS 9-10) due to immediate value
- Measure: Segment NPS by "had unallocated points" vs "didn't"

---

## Future Enhancements

**V2 Improvements:**

1. **Cost Calculator:**
   ```
   Respec Cost Analysis:
   • 4 respec points needed
   • Estimated farming time: ~30 minutes
   • Worth it? +5% DPS for 30min investment = YES!
   ```

2. **Progressive Implementation Plan:**
   ```
   Optimization Phases:

   Phase 1 (Implement Now - FREE):
   • Allocate 15 unallocated points
   • Gain: +10.2% DPS
   • Cost: $0

   Phase 2 (When you get 4 respec points):
   • Deallocate 4 suboptimal nodes
   • Allocate 4 better replacements
   • Additional gain: +5% DPS
   • Cost: 4 respec points (~30min farming)

   Total Potential: +15.2% DPS
   ```

3. **Budget Recommendations:**
   ```
   Smart Suggestion:
   "You have 15 unallocated points but only 3 respec points.
   Recommendation: Use your free points first, then decide
   if the +5% from respecs is worth farming 4 more respec points."
   ```

---

## Documentation References

**Updated Requirements:**
- FR-2.2: Budget Constraint (Unallocated Points + Respec Points)
- FR-4.3: Budget Enforcement (Dual Constraint)

**Updated User Journeys:**
- Journey 1 (Marcus): Shows respec-only scenario (level 92 maxed)
- Journey 2 (Sarah): Shows unallocated + unlimited respec scenario (leveling)

**Architecture Impact:**
- Dual budget tracking in optimization algorithm
- Auto-detection in PoB parser
- Results display showing breakdown

---

**Status:** ✅ Specified in PRD, ready for architecture phase
**Priority:** HIGH - Critical UX differentiator
**Complexity:** MEDIUM - Requires auto-detection + dual constraint tracking
