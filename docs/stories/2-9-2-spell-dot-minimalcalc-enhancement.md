# Story 2.9.2: Spell/DOT MinimalCalc Enhancement

Status: ready-for-dev

## Story

As a **developer**,
I want **MinimalCalc.lua to calculate spell/DOT/totem damage from gem level progression data**,
so that **all 15 realistic builds produce DPS > 0 and Epic 2 validation achieves 100% success rate**.

## Context

**Background:**
Story 2.9.1 achieved **partial completion** with critical infrastructure delivered:
- ✅ **Phase 1 Complete**: Weapon builds working (4/15 builds, 26.7% success rate)
- ✅ **Infrastructure Complete**: Hybrid routing, skill detection, SubprocessCalculator operational
- ❌ **Phase 2 Blocked**: Spell/DOT/totem support requires MinimalCalc.lua enhancements

**Gap Analysis:**
During Story 2.9.1 implementation, testing revealed MinimalCalc.lua does not implement spell base damage calculation. PoB's CalcOffence module requires:
1. Access to gem level progression data (`grantedEffect.levels[level]`)
2. Spell base damage values from gem stat progression
3. Spell effectiveness multipliers
4. Proper spell damage scaling formulas

**Current Status:**
- **Working**: 4/15 builds (all weapon-based attacks)
- **Blocked**: 11/15 builds (all spell/DOT/totem builds return DPS = 0)
- **Infrastructure**: Hybrid routing and skill type detection ready and tested

**Strategic Context:**
Completing spell/DOT support unblocks Epic 2 validation (Task 6) and achieves the original Story 2.9 goal of 100% build success rate. This story represents Phase 2 of the hybrid calculation approach approved by Alec on 2025-11-29.

**References:**
- Story 2.9.1: `docs/stories/2-9-1-hybrid-calculation-approach.md`
- SM Handoff: `docs/stories/2-9-1-SM-HANDOFF.md`
- Gap Analysis: `docs/validation/calculation-gap-REVISED-ANALYSIS-2025-11-29.md`

## Acceptance Criteria

### AC-2.9.2.1: Spell base damage calculation implemented
- MinimalCalc.lua accesses `grantedEffect.levels[skillLevel]` for spell gems
- Extracts base damage values from gem stat progression
- Applies spell damage effectiveness multipliers
- Handles spell crit, cast speed, and mana cost calculations

### AC-2.9.2.2: DOT calculation support
- DOT skills calculate base damage over time
- Ailment damage formulas applied (ignite, poison, bleed if applicable to PoE 2)
- DOT duration and damage multipliers handled correctly
- DOT skills return non-zero DPS values

### AC-2.9.2.3: Totem/minion calculation support
- Totem skills route through totem damage pipeline
- Minion skills handled appropriately (or explicitly marked as unsupported with graceful degradation)
- Totem/minion builds produce DPS > 0 or graceful error message

### AC-2.9.2.4: Spell build validation
- All 11 spell/DOT/totem builds produce DPS > 0
- Validation results documented in test results
- Builds tested:
  - bloodmage_remnants_95 (Life Remnants - DOT)
  - gemling_frost_mage_100 (Frost spell)
  - witch_frost_mage_91 (Frost spell)
  - titan_totem_90 (Totem)
  - warrior_ballista_93 (Siege Ballista)
  - lich_frost_mage_90 (Frost spell)
  - lich_storm_mage_90 (Storm spell)
  - ritualist_lightning_spear_96 (Spell)
  - titan_infernal_cry_72 (Warcry)
  - witch_essence_drain_86 (DOT)
  - titan_falling_thunder_99 (Spell)

### AC-2.9.2.5: Epic 2 validation criteria achieved
- **Success rate:** 100% (15/15 builds produce DPS > 0)
- **Median improvement:** ≥5% when optimizer runs with unallocated points
- **Budget constraints:** Zero violations across all optimizations
- **Performance:** All build calculations complete <500ms per calculation

### AC-2.9.2.6: No regressions in weapon builds
- All 4 weapon builds from Story 2.9.1 Phase 1 continue to work correctly
- DPS values remain stable (within 5% variance acceptable)
- Test suite: `test_story_2_9_1_phase1_weapons.py` continues to pass

## Tasks / Subtasks

### Task 1: Research PoB Spell Damage Calculation (AC: #1)
- [x] 1.1: Study `CalcOffence.lua` spell damage formulas in external/pob-engine
- [x] 1.2: Understand `grantedEffect.levels` structure and data format
- [x] 1.3: Map gem stat IDs to base damage values (identify which stats = spell damage)
- [x] 1.4: Create debug script to inspect spell gem data structure
- [x] 1.5: Document findings: which Lua tables to access, data format, calculation order

### Task 2: Enhance MinimalCalc.lua for Spell Base Damage (AC: #1, #2)
- [ ] 2.1: Add spell base damage extraction from `grantedEffect.levels[level]`
- [ ] 2.2: Implement spell effectiveness calculation
- [ ] 2.3: Add spell crit and cast speed modifiers
- [ ] 2.4: Handle spell flags in CalcOffence pipeline
- [ ] 2.5: Implement DOT base damage calculation
- [ ] 2.6: Add DOT duration and ailment damage formulas
- [ ] 2.7: Test with ONE spell build first (e.g., `witch_frost_mage_91`)

### Task 3: Add Totem/Minion Support (AC: #3)
- [ ] 3.1: Implement totem damage multipliers
- [ ] 3.2: Route totem skills through appropriate calculation path
- [ ] 3.3: Handle minion skills (or implement graceful degradation)
- [ ] 3.4: Test totem builds: `titan_totem_90`, `warrior_ballista_93`
- [ ] 3.5: Document any unsupported skill types

### Task 4: Comprehensive Validation (AC: #4, #5, #6)
- [ ] 4.1: Create test suite: `test_story_2_9_2_spell_builds.py`
- [ ] 4.2: Test all 11 spell/DOT/totem builds individually
- [ ] 4.3: Verify 100% success rate (15/15 builds DPS > 0)
- [ ] 4.4: Run regression tests on weapon builds (no breakage)
- [ ] 4.5: Run Epic 2 validation suite (≥70% success, ≥5% improvement)
- [ ] 4.6: Measure performance: <500ms per calculation target
- [ ] 4.7: Document results in validation report

## Dev Notes

### Technical Context

**Story 2.9.1 Achievements:**
- ✅ Hybrid routing infrastructure operational
- ✅ Skill type detection accurate (8/8 tests passing)
- ✅ SubprocessCalculator implemented (uses enhanced Lua engine)
- ✅ Thread-local calculator instances for isolation
- ✅ 4/15 weapon builds working (315-1205 DPS range)

**Key Discovery from 2.9.1:**
Testing revealed that spell builds route correctly through the hybrid system, but MinimalCalc.lua returns DPS = 0 because spell base damage formulas are not yet implemented. The infrastructure is ready—only spell calculation logic is missing.

**Test Evidence (from `scripts/final_spell_test.py`):**
```
Spell Build: witch_frost_mage_91
  Skill: Pain Offering (spell)
  skillFlags.attack = false ✓ (correctly detected as spell)
  calcs.perform() = SUCCESS ✓ (PoB engine runs)
  mainSkill.output = NIL ❌ (no spell damage calculated)
  TotalDPS = 0 ❌
  Life = 1073 ✓ (defenses work)
```

**Root Cause:**
MinimalCalc.lua does not access `grantedEffect.levels[skillLevel]` to extract spell gem base damage. PoB's spell damage calculation requires:
- Gem base damage from stat progression tables
- Spell effectiveness multipliers
- Proper spell damage scaling formulas

**Implementation Approach:**
1. Start with ONE spell build (`witch_frost_mage_91`)
2. Get DPS > 0 for that build first
3. Expand to other spell types (DOT, totem)
4. Final validation: All 15 builds

**Success Criteria:**
- `mainSkill.output.TotalDPS > 0` for spell builds
- Validation test passes: 15/15 builds DPS > 0
- Epic 2 success rate ≥70%, median improvement ≥5%

### Project Structure Notes

**Key Lua Code Locations (MinimalCalc.lua):**
- **Line 1210-1250:** `activeEffect` creation for gems
- **Line 1654-1682:** Result extraction (currently uses `player.output`)
- **Reference:** PoB CalcOffence.lua in external/pob-engine

**Files to Modify:**
- `src/calculator/MinimalCalc.lua` - Add spell base damage calculation
- `src/calculator/pob_engine.py` - May need additional Lua data access methods

**Files to Create:**
- `tests/integration/test_story_2_9_2_spell_builds.py` - Spell build validation tests
- `scripts/debug_spell_data.py` - Already exists, use for gem data inspection

**No Changes Expected:**
- `src/calculator/subprocess_calculator.py` - Already implemented
- `src/calculator/build_calculator.py` - Hybrid routing already working
- Epic 1 code - Zero modifications (stable API)

### Architecture Notes

**Hybrid Routing (Already Operational):**
- Attack skills → MinimalCalc (fast path ~10ms)
- Spell/DOT/totem → SubprocessCalculator (~50-100ms)
- Automatic fallback: MinimalCalc error → retry with Subprocess

**Current Limitation:**
Both calculation paths currently use the same Lua engine. MinimalCalc needs spell formulas implemented to support non-attack skills.

**Post-Story 2.9.2:**
- MinimalCalc will support both attack AND spell calculations
- SubprocessCalculator provides fallback for edge cases
- 100% build coverage achieved

### Testing Strategy

**Phase 1: Single Spell Build (Task 2.7)**
- Focus on `witch_frost_mage_91` (Pain Offering spell)
- Get `mainSkill.output.TotalDPS > 0`
- Verify calculation accuracy against PoB GUI
- Document approach before expanding

**Phase 2: All Spell Types (Task 3)**
- Test frost spells, storm spells, DOT, totems
- Verify each category produces DPS > 0
- Document any category-specific logic

**Phase 3: Full Validation (Task 4)**
- All 15 builds in test suite
- 100% success rate verification
- Epic 2 validation run
- Performance benchmarking

**Regression Prevention:**
- Weapon build tests continue to pass
- No performance degradation
- API stability maintained

### Performance Expectations

**MinimalCalc Path (All Builds After This Story):**
- Single calculation: ~10ms (spell) to ~50ms (complex spell)
- Optimization (200 iterations × 10 neighbors): ~20-100 seconds
- **Target:** <500ms per calculation for any build type

**Epic 2 Performance Budget:**
- Attack builds: ~20s per optimization (fast path)
- Spell builds: ~50-100s per optimization (acceptable)
- **All within Epic 2 performance budget (<300s)**

### Risk Mitigation

**Risk 1: PoB spell formula complexity**
- Mitigation: Start with simple spell (Ball Lightning, Frost Wall)
- Mitigation: Focus on base damage first, iterate on modifiers
- Probability: Medium, Impact: Medium

**Risk 2: Gem stat mapping unclear**
- Mitigation: Use debug logging to inspect stat IDs
- Mitigation: Reference PoB CalcOffence.lua implementation
- Probability: Low, Impact: Low

**Risk 3: Time overrun (10-16h estimate)**
- Mitigation: Start with subset of spells, expand iteratively
- Mitigation: Mark remaining spell types as unsupported if needed
- Probability: Low, Impact: Medium

**Risk 4: Regression in weapon builds**
- Mitigation: Comprehensive regression test suite
- Mitigation: Separate spell logic from attack logic in code
- Probability: Very Low, Impact: High

### References

**Source Documents:**
- [Source: docs/stories/2-9-1-hybrid-calculation-approach.md] - Story 2.9.1 complete context
- [Source: docs/stories/2-9-1-SM-HANDOFF.md] - Handoff document with proposed story structure
- [Source: docs/validation/calculation-gap-REVISED-ANALYSIS-2025-11-29.md] - Gap analysis and approach
- [Source: docs/tech-spec-epic-2.md] - Epic 2 technical specification

**PoB Engine Reference:**
- [Source: external/pob-engine/src/Modules/CalcOffence.lua] - Spell damage formulas
- [Source: external/pob-engine/src/Modules/CalcActiveSkill.lua] - Skill setup
- [Source: external/pob-engine/src/Data/Gems.lua] - Gem progression data

**Test Scripts:**
- [Source: scripts/debug_spell_data.py] - Spell gem data structure inspection
- [Source: scripts/final_spell_test.py] - Spell calculation validation (confirms DPS=0 issue)
- [Source: tests/integration/test_skill_type_detection.py] - Skill classification tests (8/8 passing)

**Epic Context:**
- [Source: docs/epics.md#Story 2.9] - Original Story 2.9 goals and acceptance criteria
- [Source: docs/tech-spec-epic-2.md#Epic Success Criteria] - Epic-AC-1: 80%+ success rate, Epic-AC-2: 8%+ median improvement

## Dev Agent Record

### Context Reference

- `docs/stories/2-9-2-spell-dot-minimalcalc-enhancement.context.xml` - Generated 2025-12-01 by BMAD Story Context Workflow

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

- `scripts/debug_spell_data.py` - Spell gem data exploration
- `scripts/final_spell_test.py` - Evidence of spell DPS = 0 issue

### Completion Notes List

**Task 1 Research (Completed 2025-12-01):**
- Discovered spell base damage storage structure in PoB:
  - Values stored in `grantedEffect.statSets[n].levels[gemLevel][index]`
  - Index position corresponds to `statSets[n].stats` array order
  - Example: Ball Lightning level 20: `levels[20] = {4, 70, ...}` → min=4, max=70 lightning damage
- Extraction pipeline identified:
  1. Get level data from `statSet.levels[gemLevel]`
  2. Map stat position to value: `levelData[index]` where index is position in `stats` array
  3. Map stat name to modifier via SkillStatMap (e.g., "spell_minimum_base_lightning_damage" → "LightningMin")
  4. CalcOffence sums modifiers to get final base damage
- Key PoB files referenced:
  - `external/pob-engine/src/Modules/CalcTools.lua:136-196` - buildSkillInstanceStats()
  - `external/pob-engine/src/Modules/CalcActiveSkill.lua:53-87` - mergeSkillInstanceMods()
  - `external/pob-engine/src/Data/Skills/*.lua` - Skill definitions with level data
- Created debug scripts: `scripts/debug_spell_gem_levels.py`, `scripts/check_frost_bolt_data.py`, `scripts/get_stat_progression.py`
- Verified data loading: Ball Lightning properly loaded with 40 levels, statSets with stats and level data intact

**Task 2.1 Implementation (In Progress 2025-12-01):**
- Added spell base damage extraction code to MinimalCalc.lua:1628-1688
- Implementation approach:
  - Detects spell skills via `skillFlags.spell == true` check
  - Extracts base damage from `grantedEffect.statSets[1].levels[gemLevel]`
  - Maps stat names to damage modifiers (Physical/Lightning/Cold/Fire/Chaos Min/Max)
  - Injects modifiers into `skillModList` before `calcs.perform()`
- Status: Code implemented but requires debugging
  - Spell detection logic executes (confirmed via debug logs)
  - Need to verify `skillFlags.spell` is properly set for spell skills
  - Need to confirm modifiers are being added to skillModList correctly
- Next steps:
  - Debug spell detection condition (skillFlags.spell may be nil or false)
  - Verify modifier injection is working
  - Test with witch_frost_mage_91 to confirm DPS > 0

### File List

**Modified:**
- `src/calculator/MinimalCalc.lua` - Added spell base damage extraction (lines 1628-1688)
- `docs/stories/2-9-2-spell-dot-minimalcalc-enhancement.md` - Updated with Task 1 completion and Task 2.1 progress

**Created:**
- `scripts/debug_spell_gem_levels.py` - Enhanced debug script for spell gem level data inspection
- `scripts/check_frost_bolt_data.py` - Script to verify spell base damage in gem data
- `scripts/get_stat_progression.py` - Script to examine stat progression values
- `scripts/deep_stat_check.py` - Deep dive into stat structure
- `scripts/check_stat_values.py` - Check stat values at different gem levels
- `scripts/verify_skill_data_loaded.py` - Verify skill data is properly loaded with statSets

---

## Change Log

- **2025-12-01 (Session 2)**: Implementation started by Amelia (Dev Agent)
  - **Task 1 COMPLETE**: Research phase completed - discovered spell base damage storage in PoB
  - **Task 2.1 IN PROGRESS**: Implemented spell base damage extraction in MinimalCalc.lua:1628-1688
  - Created 6 debug scripts to inspect and verify spell gem data structure
  - Verified Ball Lightning level 20 data: min=4, max=70 lightning damage properly loaded
  - Implementation approach: Manual extraction + modifier injection before calcs.perform()
  - **Blocker identified**: Need to debug skillFlags.spell detection (may not be set correctly)
  - **Next session**: Debug spell detection, verify modifier injection, test with witch_frost_mage_91

- **2025-12-01 (Session 1)**: Story 2.9.2 drafted by Bob (Scrum Master) based on Story 2.9.1 handoff
  - Story created from SM handoff document after Story 2.9.1 partial completion
  - Focuses on Phase 2: Spell/DOT/totem support for MinimalCalc.lua
  - Estimated effort: 10-16 hours (based on PoB engine complexity)
  - **Context:** Story 2.9.1 delivered infrastructure (hybrid routing, skill detection), blocked on spell formulas
  - **Goal:** Complete Epic 2 validation by achieving 100% build success rate (15/15 builds)
