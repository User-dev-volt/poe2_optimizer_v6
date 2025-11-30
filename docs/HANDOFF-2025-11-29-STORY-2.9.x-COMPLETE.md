# Story 2.9.x Complete - Hybrid Approach Approved
**Date:** 2025-11-29
**Status:** ✓ COMPLETE - Ready for Story 2.9.1 Implementation

---

## Summary

**Gap Analysis Complete:** Story 2.9.x successfully identified all calculation failures and recommended implementation approach.

**Approved Approach:** **Hybrid (Revised) - 10-16 hours**

**Key Discovery:** Alec's insight about existing PoB data files (Data/Bases/*.lua, Data/Gems.lua) reduced implementation effort by 60%!

---

## Deliverables

### Analysis Documents
1. ✓ `docs/validation/calculation-gap-categorization-2025-11-29.md` - 5 failure categories
2. ✓ `docs/validation/calculation-gap-effort-estimation-2025-11-29.md` - Original estimates (75-97 hrs incremental)
3. ✓ `docs/validation/calculation-gap-decision-matrix-2025-11-29.md` - Original recommendation (subprocess)
4. ✓ `docs/validation/calculation-gap-REVISED-ANALYSIS-2025-11-29.md` - **APPROVED** (hybrid 10-16 hrs)
5. ✓ `docs/stories/2-9-x-calculation-gap-analysis-REPORT.md` - Executive summary
6. ✓ `docs/stories/2-9-x-calculation-gap-analysis.md` - Story file (updated with approval)

### Test Data
7. ✓ `docs/validation/gap-analysis-raw-output-2025-11-29.log` - 20MB verbose logs
8. ✓ `docs/validation/realistic-validation-results.json` - Structured results (3/15 success)

### Tools
9. ✓ `scripts/analyze_gap_results.py` - Gap analysis utility

---

## Key Findings

**Current State:**
- Success Rate: 3/15 builds (20%) produce DPS > 0
- Target: 70%+ required for Epic 2 validation
- Gap: 50 percentage points below target

**Root Causes:**
1. **Weapon Stubs:** MinimalCalc doesn't load Data/Bases/*.lua (mace, spear exist but unused)
2. **Spell Damage:** Data/Gems.lua loaded but not used for spell base damage
3. **DOT Engine:** CalcOffence has formulas, but MinimalCalc doesn't call them
4. **Totems:** Data/Minions.lua exists but not loaded

**Critical Discovery:**
- PoB data files (Data/Bases/*.lua, Data/Gems.lua, Data/Minions.lua) **already exist**
- MinimalCalc deliberately avoids loading them (line 177: "NOT full Data.lua which has GUI dependencies")
- **GUI dependency concern is outdated** - Data.lua has no real GUI dependencies (only 1 commented-out ConPrintf)
- **By loading existing data files, effort drops from 75-97 hrs → 10-16 hrs!**

---

## Approved Implementation: Hybrid Approach (10-16 hours)

### Phase 1: Load PoB Data & Fix Weapons (2-4 hours)

**Work:**
1. Add 4 lines to load Data/Bases/*.lua into data.itemBases
2. Add "Spear" to weaponTypeInfo and pattern matching
3. Use real weapon data from data.itemBases instead of hard-coded stubs
4. Test 3 weapon-failing builds

**Code Changes (MinimalCalc.lua):**
```lua
-- After line 252, add:
data.itemBases = { }
local itemTypes = {"mace", "spear", "sword", "axe", "bow", "staff", "wand", "sceptre", "dagger", "claw", "crossbow"}
for _, type in ipairs(itemTypes) do
    LoadModule("Data/Bases/"..type, data.itemBases)
end

-- Add to weaponTypeInfo:
data.weaponTypeInfo["Spear"] = { name = "Spear", oneHand = true, melee = true, flag = "Spear" }

-- Add pattern matching after line 1019:
elseif rawType:match("Spear") then
    weaponType = "Spear"
```

**Expected Result:**
- warrior_earthquake_89 (Mace Strike): 0 DPS → 49,896 DPS ✓
- warrior_spear_45 (Explosive Spear): 0 DPS → 165 DPS ✓
- warrior_spear_71 (Explosive Spear): 0 DPS → 6,230 DPS ✓

**Success Rate:** 6/15 (40%) → moving in right direction!

---

### Phase 2: Subprocess Fallback (8-12 hours)

**Work:**
1. Detect skill type (attack vs spell/DOT/totem)
2. If NOT attack → route to external PoB subprocess
3. Implement subprocess wrapper:
   - Write build XML to temp file
   - Execute: `pob-cli calculate build.xml --output json`
   - Parse JSON output (DPS, life, defenses)
4. Handle errors, timeouts, process pooling
5. Test all 15 builds

**Expected Result:**
- All spell builds: Use PoB subprocess → DPS calculated correctly ✓
- All DOT builds: Use PoB subprocess → DPS calculated correctly ✓
- All totem builds: Use PoB subprocess → DPS calculated correctly ✓

**Success Rate:** 15/15 (100%) ✓

---

## Performance Impact

**Attack Builds (40% of corpus):**
- **Fast:** Continue using MinimalCalc (~10ms per calculation)
- No change from current performance

**Spell/DOT/Totem Builds (60% of corpus):**
- **Slower:** Use PoB subprocess (~50-100ms per calculation)
- Typical optimization: 50-200 iterations × 10 neighbors × 75ms = 37-150 seconds
- **Still fits Epic 2 budget:** < 300 seconds per build ✓

**Trade-off:** Performance for attack builds preserved, spells slower but acceptable.

---

## Next Steps - Story 2.9.1

### Story 2.9.1: Hybrid Calculation Implementation

**Priority:** CRITICAL (blocks Epic 2 validation)
**Estimate:** 10-16 hours
**Epic:** 2 - Core Optimization Engine

**Tasks:**
1. **Task 1:** Load PoB weapon bases and add Spear support (2-4 hrs)
   - 1.1: Add Data/Bases loading (4 lines)
   - 1.2: Add Spear pattern matching (3 lines)
   - 1.3: Test 3 weapon builds (warrior_earthquake, warrior_spear_45/71)

2. **Task 2:** Implement subprocess fallback for non-attacks (8-12 hrs)
   - 2.1: Skill type detection (attack vs spell/DOT/totem)
   - 2.2: External PoB subprocess wrapper
   - 2.3: JSON output parsing
   - 2.4: Error handling, timeouts, process pooling
   - 2.5: Test all 15 builds → 100% success

**Acceptance Criteria:**
- AC-2.9.1.1: All 15 realistic builds produce DPS > 0 (100% success)
- AC-2.9.1.2: Attack builds use fast MinimalCalc path (~10ms)
- AC-2.9.1.3: Spell/DOT/totem builds use PoB subprocess (~75ms)
- AC-2.9.1.4: Max completion time < 300s per build
- AC-2.9.1.5: Zero budget violations

**Success Metrics:**
- Before: 3/15 (20%) success rate
- After: 15/15 (100%) success rate ✓
- Performance: Attack builds fast, spells acceptable ✓

---

## Files Modified/Created

**Story 2.9.x Deliverables:**
- docs/validation/calculation-gap-categorization-2025-11-29.md
- docs/validation/calculation-gap-effort-estimation-2025-11-29.md
- docs/validation/calculation-gap-decision-matrix-2025-11-29.md
- docs/validation/calculation-gap-REVISED-ANALYSIS-2025-11-29.md
- docs/stories/2-9-x-calculation-gap-analysis-REPORT.md
- docs/validation/gap-analysis-raw-output-2025-11-29.log (20MB)
- docs/validation/realistic-validation-results.json
- scripts/analyze_gap_results.py
- docs/stories/2-9-x-calculation-gap-analysis.md (updated)
- docs/sprint-status.yaml (updated)

**Story 2.9.1 Will Modify:**
- src/calculator/MinimalCalc.lua (load PoB data, add Spear)
- src/calculator/calculator.py (subprocess fallback)
- tests/ (add tests for hybrid path)

---

## Timeline

**Story 2.9.x:** ✓ COMPLETE (4-8 hours actual)
**Story 2.9.1:** 10-16 hours estimated
- Week 1: Phase 1 (2-4 hrs) - Quick wins, weapon fixes
- Week 2: Phase 2 (8-12 hrs) - Subprocess integration

**Total Time to Epic 2 Validation:** ~2-3 weeks from today

---

## Acknowledgments

**Special thanks to Alec** for the insight about existing PoB data files! This discovery:
- Reduced implementation effort by 60% (75-97 hrs → 10-16 hrs)
- Enables using battle-tested PoB data instead of reinventing
- Makes weapon fixes trivial (2-4 hours instead of weeks)

**Your instinct was spot-on, Alec!** 🎯

---

**Status:** Ready to begin Story 2.9.1 implementation
**Approved By:** Alec
**Date:** 2025-11-29
