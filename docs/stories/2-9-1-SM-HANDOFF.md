# Story 2.9.1 → 2.9.2 SM Handoff Document

**Date:** 2025-11-30
**From:** Amelia (Dev Agent)
**To:** Bob (Scrum Master)
**Subject:** Story 2.9.1 Partial Completion - Handoff for Story 2.9.2

---

## Executive Summary

Story 2.9.1 achieved **partial completion**:
- ✅ **Phase 1 Complete**: Weapon builds working (4/15 builds, 26.7% success rate)
- ✅ **Infrastructure Complete**: Hybrid routing, skill detection, SubprocessCalculator implemented
- ❌ **Phase 2 Blocked**: Spell/DOT/totem support requires MinimalCalc.lua enhancements (11/15 builds blocked)

**Recommendation:** Create **Story 2.9.2** to complete spell/DOT support, achieving original 100% success goal.

---

## What Was Accomplished (Story 2.9.1)

### ✅ Phase 1: Load PoB Data & Fix Weapons (COMPLETE)

**Delivered:**
- MinimalCalc.lua loads all 11 weapon types from PoB `Data/Bases/*.lua` (284 bases)
- Added "Spear" and "Maul" weapon type support
- Real weapon data replaces hard-coded stubs
- Physical damage % modifiers parsed and applied

**Validation Results:**
- `warrior_earthquake_89` (Mace): **1205.26 DPS** ✓
- `warrior_spear_45` (Spear L45): **87.50 DPS** ✓
- `warrior_spear_71` (Spear L71): **249.48 DPS** ✓
- `deadeye_lightning_arrow_76` (Bow): **347.15 DPS** ✓ (regression test)

**Tests:** 4/4 passing (`test_story_2_9_1_phase1_weapons.py`)

### ✅ Infrastructure: Hybrid Routing (COMPLETE)

**Delivered:**

1. **Skill Type Detection** (`pob_engine.py`):
   - `is_attack_skill()` method queries Lua `data.skills` table
   - Checks `statSets[1].baseFlags.attack` for classification
   - Edge cases handled: warcries, missing skill_id, invalid IDs
   - Tests: 8/8 passing (`test_skill_type_detection.py`)

2. **SubprocessCalculator** (`subprocess_calculator.py`):
   - Pragmatic implementation using dedicated Lua engine instance
   - **Architectural Note**: Uses enhanced Lua instead of true subprocess (PoB GUI has no headless mode)
   - API designed for future swap if PoB CLI emerges
   - Placeholder methods documented for true subprocess support

3. **Hybrid Routing Logic** (`build_calculator.py`):
   - Routes attack skills → MinimalCalc (fast path ~10ms)
   - Routes spell/DOT/totem → SubprocessCalculator (~50-100ms)
   - Automatic fallback: MinimalCalc error → retry with Subprocess
   - Thread-local calculator instances for isolation
   - Zero API breaking changes

---

## What's Blocked (Story 2.9.2 Scope)

### ❌ Phase 2: Spell/DOT/Totem Support (BLOCKED)

**Root Cause:**
MinimalCalc.lua does not implement spell base damage calculation. PoB's CalcOffence module requires:
1. Access to gem level progression data (`grantedEffect.levels[level]`)
2. Spell base damage values from those levels (stored in gem `statSets`)
3. Spell effectiveness multipliers
4. Proper spell damage scaling formulas

**Test Evidence:**
```
Spell Build: witch_frost_mage_91
  Skill: Pain Offering (spell)
  skillFlags.attack = false ✓ (correctly detected as spell)
  calcs.perform() = SUCCESS ✓ (PoB engine runs)
  mainSkill.output = NIL ❌ (no spell damage calculated)
  TotalDPS = 0 ❌
  Life = 1073 ✓ (defenses work)
```

**Impact:**
- 11/15 realistic builds blocked (73% of validation corpus)
- All spell/DOT/totem builds return DPS = 0
- Epic 2 validation cannot achieve 100% success rate

**Affected Builds:**
1. bloodmage_remnants_95 (Life Remnants - DOT)
2. gemling_frost_mage_100 (Frost spell)
3. witch_frost_mage_91 (Frost spell)
4. titan_totem_90 (Totem)
5. warrior_ballista_93 (Siege Ballista)
6. lich_frost_mage_90 (Frost spell)
7. lich_storm_mage_90 (Storm spell)
8. ritualist_lightning_spear_96 (Spell)
9. titan_infernal_cry_72 (Warcry)
10. witch_essence_drain_86 (DOT)
11. titan_falling_thunder_99 (Spell)

---

## Proposed Story 2.9.2: Spell/DOT MinimalCalc Enhancement

### Story Title
"Enhance MinimalCalc.lua for Spell/DOT/Totem Damage Calculation"

### Story Description
**As a** developer,
**I want** MinimalCalc.lua to calculate spell/DOT/totem damage from gem level progression data,
**so that** all 15 realistic builds produce DPS > 0 and Epic 2 validation achieves 100% success rate.

### Epic Context
Continues Story 2.9.1 hybrid calculation work. Phase 1 (weapon builds) complete. Phase 2 (spell support) requires MinimalCalc enhancement to access PoB's gem base damage data.

### Acceptance Criteria

**AC-2.9.2.1:** Spell base damage calculation implemented
- MinimalCalc.lua accesses `grantedEffect.levels[skillLevel]` for spell gems
- Extracts base damage values from gem stat progression
- Applies spell damage effectiveness multipliers
- Handles spell crit, cast speed, and mana cost

**AC-2.9.2.2:** DOT calculation support
- DOT skills calculate base damage over time
- Ailment damage formulas applied (ignite, poison, bleed if applicable to PoE 2)
- DOT duration and damage multipliers handled

**AC-2.9.2.3:** Totem/minion calculation support
- Totem skills route through totem damage pipeline
- Minion skills handled (or explicitly marked as unsupported with graceful degradation)

**AC-2.9.2.4:** Spell build validation
- All 11 spell/DOT/totem builds produce DPS > 0
- Validation results documented in `docs/validation/realistic-validation-results.json`
- Tests added: `test_story_2_9_2_spell_builds.py`

**AC-2.9.2.5:** Epic 2 validation criteria achieved
- **Success rate:** 100% (15/15 builds produce DPS > 0)
- **Median improvement:** ≥5% when optimizer runs with unallocated points
- **Budget constraints:** Zero violations
- **Performance:** All optimizations complete <300s

### Estimated Effort
**10-16 hours** (based on PoB engine complexity and validation requirements)

**Breakdown:**
- Research PoB spell damage calculation: 2-3 hours
- Implement spell base damage in MinimalCalc.lua: 4-6 hours
- Implement DOT/totem support: 2-4 hours
- Testing and validation: 2-3 hours

### Tasks (High-Level)

1. **Research PoB Spell Damage Calculation**
   - Study `CalcOffence.lua` spell damage formulas
   - Understand `grantedEffect.levels` structure
   - Map gem stat IDs to base damage values

2. **Enhance MinimalCalc.lua**
   - Add spell base damage extraction from `grantedEffect.levels[level]`
   - Implement spell effectiveness calculation
   - Add spell crit and cast speed modifiers
   - Handle spell flags in CalcOffence pipeline

3. **Add DOT/Totem Support**
   - Implement DOT base damage calculation
   - Add totem damage multipliers
   - Handle minion skills (or graceful degradation)

4. **Comprehensive Validation**
   - Test all 15 realistic builds
   - Verify 100% success rate (15/15 DPS > 0)
   - Run Epic 2 validation (≥70% success, ≥5% improvement)
   - Document results

### Dependencies
- Story 2.9.1 (partial completion - infrastructure ready)
- PoB gem data already loaded (`Data/Gems.lua`, `Data/Skills/*.lua`)
- Hybrid routing infrastructure in place

### Risks
1. **PoB spell formula complexity**: Mitigation: Focus on base damage first, iterate
2. **Gem stat mapping unclear**: Mitigation: Use debug logging to inspect stat IDs
3. **Time overrun**: Mitigation: Start with subset of spells, expand iteratively

---

## Key Reference Materials for SM

**The SM should read these before drafting Story 2.9.2:**

### 1. Story 2.9.1 Complete File
- **Path:** `docs/stories/2-9-1-hybrid-calculation-approach.md`
- **Why:** Full context of what was achieved, what's blocked, and technical approach

### 2. This Handoff Document
- **Path:** `docs/stories/2-9-1-SM-HANDOFF.md`
- **Why:** Executive summary, proposed story structure, effort estimates

### 3. Gap Analysis (Original Planning)
- **Path:** `docs/validation/calculation-gap-REVISED-ANALYSIS-2025-11-29.md`
- **Why:** Original discovery of PoB data files and hybrid approach rationale

### 4. Test Results Evidence
- **Path:** Run `python scripts/final_spell_test.py` to see spell DPS = 0 issue
- **Why:** Concrete evidence of the problem to inform AC validation criteria

### 5. PoB Engine Reference (Optional Deep Dive)
- **Paths:**
  - `external/pob-engine/src/Modules/CalcOffence.lua` - Spell damage formulas
  - `external/pob-engine/src/Modules/CalcActiveSkill.lua` - Skill setup
  - `external/pob-engine/src/Data/Gems.lua` - Gem progression data
- **Why:** Technical reference for understanding PoB spell calculation architecture

### 6. Story Context XML
- **Path:** `docs/stories/2-9-1-hybrid-calculation-approach.context.xml`
- **Why:** Complete artifact and constraint context

---

## Implementation Notes for Future Dev Agent

**When Story 2.9.2 is assigned, the Dev Agent should:**

1. **Start with Debug/Research:**
   - Run `scripts/debug_spell_data.py` to inspect `grantedEffect.levels` structure
   - Examine Ball Lightning or Frost Wall gem data to understand stat progression
   - Identify which stat IDs correspond to base spell damage

2. **Key Lua Code Locations:**
   - **MinimalCalc.lua line 1210-1250:** `activeEffect` creation for gems
   - **MinimalCalc.lua line 1654-1682:** Result extraction (currently uses `player.output`)
   - **PoB CalcOffence.lua:** Reference for spell damage formulas (external/pob-engine)

3. **Testing Strategy:**
   - Start with ONE spell build (e.g., `witch_frost_mage_91`)
   - Get DPS > 0 for that build first
   - Then expand to other spell types (DOT, totem)
   - Final validation: All 15 builds

4. **Success Criteria:**
   - `mainSkill.output.TotalDPS > 0` for spell builds
   - Validation test passes: 15/15 builds DPS > 0
   - Epic 2 success rate ≥70%, median improvement ≥5%

---

## Files Modified in Story 2.9.1

**Created:**
- `src/calculator/subprocess_calculator.py` (171 lines)
- `tests/integration/test_skill_type_detection.py` (119 lines)
- `scripts/debug_skill_flags.py` (60 lines)
- `scripts/test_hybrid_routing.py` (85 lines)
- `scripts/debug_spell_data.py` (67 lines)
- `scripts/final_spell_test.py` (48 lines)

**Modified:**
- `src/calculator/pob_engine.py` (+88 lines) - Added `is_attack_skill()` method
- `src/calculator/build_calculator.py` (+104 lines) - Hybrid routing logic
- `src/calculator/MinimalCalc.lua` - Phase 1 weapon support (already modified in previous stories)
- `docs/stories/2-9-1-hybrid-calculation-approach.md` - Task status, completion notes

---

## Current Project State

**Epic 2 Validation Status:**
- **Phase 1 (Weapons):** 4/15 builds working (26.7%)
- **Phase 2 (Spells):** 0/11 spell builds working (blocked)
- **Overall Success Rate:** 26.7% (target: 100%)

**Next Milestone:**
- Story 2.9.2 completion → 100% success rate (15/15 builds)
- Then: Epic 2 optimization validation (Task 6)
- Then: Epic 2 complete!

**Infrastructure Ready:**
- ✅ Hybrid routing works
- ✅ Skill type detection accurate
- ✅ Thread-safe calculator instances
- ✅ Fallback mechanism in place
- ✅ API stable (no breaking changes)

---

## Questions for SM Before Story Creation

1. **Priority:** Should Story 2.9.2 be next in sprint, or are there other priorities?
2. **Scope:** Accept proposed 10-16 hour estimate, or reduce scope (e.g., spells only, defer DOT/totem)?
3. **Validation:** Accept proposed AC validation criteria (100% success, Epic 2 thresholds)?

---

**End of Handoff Document**

*Prepared by Amelia (Dev Agent) - 2025-11-30*
