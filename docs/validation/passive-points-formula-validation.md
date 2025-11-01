# PoE 2 Passive Points Formula Validation

**Date:** 2025-10-27
**Status:** ✅ VALIDATED
**Owner:** Bob (Scrum Master) during Prep Sprint

---

## Summary

The passive points formula in `src/models/build_data.py:76` has been validated against live PoE 2 mechanics.

**Formula:** `level + 23`

**Breakdown:** `(level - 1) from leveling + 24 from quests`

**Result:** 123 passive skill points at level 100

---

## Validation Results

### PoE 2 Mechanics (Verified 2025-10-27)

- **Leveling Points:** 99 points (gain 1 per level from 2 to 100)
- **Quest Points:** 24 points from campaign quests
  - Act 1: +4 points
  - Interlude 1: +2 points
  - Act 2: +4 points
  - Interlude 2: +2 points
  - Act 3: +4 points
  - Interlude 3: +4 points
  - Act 4: +4 points
- **Total at Level 100:** 123 points

### Sources

- Maxroll: https://maxroll.gg/poe2/getting-started/permanent-stats-from-campaign
- PoE2 Wiki: https://www.poewiki.net/wiki/poe2wiki:Passive_Skill_Tree
- Multiple community sources cross-validated

### Test Coverage

Created comprehensive test suite in `tests/validation/test_passive_points_formula.py`:

- ✅ Level 1 character (24 points)
- ✅ Level 100 character (123 points)
- ✅ Typical endgame level 85 (108 points)
- ✅ With allocated nodes (correct subtraction)
- ✅ Fully allocated build (0 unallocated)
- ✅ Over-allocated build (defensive clamping)
- ✅ Formula consistency across all character classes

**All 10 tests PASSED**

---

## Known Edge Cases

### 1. Formula Assumes All Quests Completed

**Issue:** At low levels (e.g., level 30), the character may not have completed all quest rewards yet.

**Example:**
- Level 30 character in mid-Act 2
- Formula gives: 30 + 23 = 53 points
- Reality: ~37-39 points (29 from leveling + 8-10 from quests completed so far)

**Decision:**
- Use upper bound (24 quest points) as default
- Reasonable assumption: most PoB exports are from players who've completed the campaign
- **Story 2.3 AC includes manual override** for cases where auto-detection is wrong

### 2. Pathfinder Ascendancy Bonus

**Issue:** Pathfinders can gain +6 additional passive points from Traveller's Wisdom ascendancy.

**Example:**
- Level 100 Pathfinder: 129 points (123 base + 6 bonus)
- Current formula: 123 points (doesn't include ascendancy bonuses)

**Decision:**
- Base formula excludes ascendancy bonuses
- Edge case can be handled via manual override in UI
- May add ascendancy-specific logic in future if needed

### 3. Cruel Difficulty (Future Consideration)

**Note:** PoE 2 has Cruel difficulty where players can repeat quests for additional points.

**Current Scope:** MVP focuses on Normal difficulty (123 points max)

**Future:** If Cruel support needed, formula would need difficulty parameter

---

## Implementation Notes

### Current Code (Validated ✅)

```python
@property
def unallocated_points(self) -> int:
    """Calculate unallocated points based on level.

    Formula: (level - 1) + 24 = level + 23
    - Characters gain 1 passive point per level from 2 to 100 (99 points total)
    - Campaign quest rewards provide 24 additional passive points
    - Total at level 100: 123 passive skill points
    Source: Path of Exile 2 campaign progression (2025)
    """
    max_points = self.level + 23  # PoE 2: (level - 1) from leveling + 24 from quests
    return max(0, max_points - self.allocated_point_count)
```

### Story 2.3 AC Compliance

✅ "Display auto-detected value in UI (user can override if wrong)"
✅ "Handle edge cases: quest rewards, special nodes, ascendancy points"

The formula provides accurate defaults with documented edge cases that can be handled via manual override.

---

## Conclusion

**Status:** ✅ Formula validated and correct for PoE 2 Normal difficulty.

**Blocks Removed:** Story 2.3 can proceed without formula changes.

**Action Items:** None - formula is production-ready.

---

**Validated by:** Bob (Scrum Master)
**Date:** 2025-10-27
**Prep Sprint Task:** #3 COMPLETED
