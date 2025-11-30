# Story 2.9.1: Hybrid Calculation Approach

Status: ready-for-dev

## Story

As a **developer**,
I want **the calculator to support all skill types (attacks, spells, DOT, totems) using a hybrid approach**,
so that **Epic 2 validation achieves 100% success rate (15/15 builds) and the optimizer can find meaningful improvements across all build archetypes**.

## Context

**Background:**
Story 2.9 successfully implemented items/skills loading and passive tree integration, achieving **311.7 DPS** for attack-based skills (vs ~1.2 Default Attack baseline). However, Epic 2 validation (Task 6) revealed a critical gap: **only 20% success rate** (3 out of 15 builds).

**Gap Analysis (Story 2.9.x):**
Comprehensive analysis on 2025-11-29 identified root causes for 12 failing builds:
- **3 builds:** Missing weapon type stubs (One-Handed Mace, Spear)
- **2 builds:** Spell base damage formulas missing
- **1 build:** DOT calculation engine not implemented
- **2 builds:** Totem/minion mechanics missing
- **4 builds:** Calculator crashes (Lua errors, parser bugs)

**Approved Solution: Hybrid Approach (Revised)**
After discovering existing PoB data files (`Data/Bases/*.lua`, `Data/Gems.lua`), Alec approved a **10-16 hour hybrid implementation**:
- **Phase 1 (2-4 hrs):** Load PoB weapon data, fix missing weapon types → Fixes 3 builds
- **Phase 2 (8-12 hrs):** Subprocess fallback for spells/DOT/totem → Fixes 9 builds
- **Result:** 100% success rate, performance acceptable

**Strategic Rationale:**
- **Uses existing PoB data** (no reinventing wheel)
- **Preserves MinimalCalc performance** for attack builds (~10ms)
- **Guarantees complete coverage** via subprocess for complex skills
- **Avoids validation thrashing** (single informed implementation vs incremental discovery)

**References:**
- Gap Analysis: `docs/stories/2-9-x-calculation-gap-analysis.md`
- Revised Analysis: `docs/validation/calculation-gap-REVISED-ANALYSIS-2025-11-29.md`
- Sprint Change Proposal: `docs/sprint-change-proposal-2025-11-29.md`

## Acceptance Criteria

### Phase 1: Load PoB Data & Fix Weapons (2-4 hours)

**AC-2.9.1.1:** Load PoB weapon base data files
- MinimalCalc.lua loads all weapon types from `Data/Bases/*.lua` (mace, spear, sword, axe, bow, staff, wand, sceptre, dagger, claw, crossbow)
- `data.itemBases` table populated with weapon definitions
- Weapon stats available: PhysicalMin/Max, AttackRate, CritChance, Range

**AC-2.9.1.2:** Add missing weapon type support
- "Spear" added to `weaponTypeInfo` table
- Spear pattern matching implemented in weapon type detection
- One-Handed Mace properly distinguished from Two-Handed Mace

**AC-2.9.1.3:** Use real weapon data instead of hard-coded stubs
- Weapon creation uses `data.itemBases` lookup instead of manual stubs
- Graceful fallback for unrecognized weapon types
- Existing weapon stub format maintained for compatibility

**AC-2.9.1.4:** Weapon build validation
- `warrior_earthquake_89` (Mace Strike) produces DPS > 0
- `warrior_spear_45` (Explosive Spear L45) produces DPS > 0
- `warrior_spear_71` (Explosive Spear L71) produces DPS > 0
- No regressions: `deadeye_lightning_arrow_76` still produces ~311 DPS

### Phase 2: Subprocess Fallback (8-12 hours)

**AC-2.9.1.5:** Skill type detection implemented
- Skill classification function detects: attack, spell, DOT, totem, warcry, minion
- Detection uses `skillFlags.attack` and skill metadata
- Edge cases handled: warcries with weapon scaling, minion skills

**AC-2.9.1.6:** External PoB subprocess integration
- SubprocessCalculator class implemented in `src/calculator/subprocess_calculator.py`
- Writes build XML to temp file
- Executes external PoB process (platform-specific: Windows GUI, Linux CLI if available)
- Parses PoB output (JSON or text format)
- Extracts DPS, Life, EHP, defenses

**AC-2.9.1.7:** Hybrid routing logic
- `calculate_build_stats()` routes based on skill type:
  - Attack skills → MinimalCalc.lua (fast path, ~10ms)
  - Spell/DOT/totem skills → SubprocessCalculator (~50-100ms)
- Fallback: If MinimalCalc errors → retry with subprocess
- Graceful error handling for subprocess failures

**AC-2.9.1.8:** Spell/DOT/totem build validation
- All 9 non-attack builds produce DPS > 0:
  - `bloodmage_remnants_95` (Life Remnants - DOT)
  - `gemling_frost_mage_100` (Frost spell)
  - `witch_frost_mage_91` (Frost spell)
  - `titan_totem_90` (Totem)
  - `warrior_ballista_93` (Siege Ballista)
  - `lich_frost_mage_90` (Frost spell)
  - `lich_storm_mage_90` (Storm spell)
  - `ritualist_lightning_spear_96` (Spell)
  - `titan_infernal_cry_72` (Warcry)

**AC-2.9.1.9:** Epic 2 validation criteria achieved
- **Success rate:** 100% (15/15 builds produce DPS > 0)
- **Median improvement:** ≥5% when optimizer runs with unallocated points
- **Budget constraints:** Zero violations across all optimizations
- **Performance:** All build optimizations complete within 300 seconds

**AC-2.9.1.10:** Performance validation
- Attack build optimization time remains fast (<60s for simple builds)
- Spell/DOT build optimization time acceptable (<300s per build)
- Batch validation (15 builds) completes in reasonable time (<90 minutes)
- Process isolation via pytest-xdist prevents Fatal Exception 0xe24c4a02 (per ADR-003)

## Tasks / Subtasks

### Phase 1: Load PoB Data & Fix Weapons (2-4 hours)

- [ ] **Task 1:** Load PoB weapon base data (AC: #1, #2)
  - [ ] 1.1: Add `Data/Bases/*.lua` loading to MinimalCalc.lua (after line 252)
  - [ ] 1.2: Create `data.itemBases` table and populate with all weapon types
  - [ ] 1.3: Add "Spear" to `weaponTypeInfo` table with correct flags
  - [ ] 1.4: Add Spear pattern matching to weapon type detection (after line 1019)
  - [ ] 1.5: Test data loading with debug logging

- [ ] **Task 2:** Use real weapon data (AC: #3)
  - [ ] 2.1: Modify weapon stub creation to use `data.itemBases` lookup
  - [ ] 2.2: Implement fallback for missing weapon types (use generic defaults)
  - [ ] 2.3: Preserve existing weapon stub structure for backward compatibility
  - [ ] 2.4: Verify weapon stats correctly populated (PhysMin/Max, APS, Crit)

- [ ] **Task 3:** Validate weapon fixes (AC: #4)
  - [ ] 3.1: Test `warrior_earthquake_89` (Mace Strike) → Verify DPS > 0
  - [ ] 3.2: Test `warrior_spear_45` (Explosive Spear L45) → Verify DPS > 0
  - [ ] 3.3: Test `warrior_spear_71` (Explosive Spear L71) → Verify DPS > 0
  - [ ] 3.4: Regression test: Ensure `deadeye_lightning_arrow_76` still works (~311 DPS)
  - [ ] 3.5: Update validation results JSON

### Phase 2: Subprocess Fallback (8-12 hours)

- [ ] **Task 4:** Implement skill type detection (AC: #5)
  - [ ] 4.1: Create `is_attack_skill()` helper in `pob_engine.py`
  - [ ] 4.2: Detect attack skills using `skillFlags.attack` from gem data
  - [ ] 4.3: Handle edge cases: warcries with weapon scaling, minion skills
  - [ ] 4.4: Add unit tests for skill classification

- [ ] **Task 5:** Implement external PoB subprocess (AC: #6)
  - [ ] 5.1: Create `SubprocessCalculator` class in `src/calculator/subprocess_calculator.py`
  - [ ] 5.2: Write build XML to temp file (use `tempfile` module)
  - [ ] 5.3: Platform detection: Windows (PoB GUI) vs Linux (PoB CLI if available)
  - [ ] 5.4: Execute subprocess with timeout (30s max per calculation)
  - [ ] 5.5: Parse PoB output (JSON format if available, else text scraping)
  - [ ] 5.6: Extract stats: TotalDPS, Life, EnergyShield, Evasion, Armour
  - [ ] 5.7: Error handling: graceful degradation for subprocess failures

- [ ] **Task 6:** Integrate hybrid routing (AC: #7)
  - [ ] 6.1: Modify `calculate_build_stats()` in `build_calculator.py`
  - [ ] 6.2: Add routing logic: if attack → MinimalCalc, else → Subprocess
  - [ ] 6.3: Implement fallback: MinimalCalc error → retry with subprocess
  - [ ] 6.4: Preserve BuildStats dataclass structure (no API changes)
  - [ ] 6.5: Add logging: track which calculation path used per build

- [ ] **Task 7:** Comprehensive validation (AC: #8, #9, #10)
  - [ ] 7.1: Run validation script on all 15 realistic builds
  - [ ] 7.2: Verify 100% success rate (15/15 builds produce DPS > 0)
  - [ ] 7.3: Log calculation path: MinimalCalc (3 builds) vs Subprocess (12 builds)
  - [ ] 7.4: Epic 2 criteria check: ≥70% success, ≥5% median improvement
  - [ ] 7.5: Performance test: All optimizations complete <300s
  - [ ] 7.6: Update `docs/validation/realistic-validation-results.json`
  - [ ] 7.7: Document results in validation report

## Dev Notes

### Technical Context

**Story 2.9 Achievement:**
- ✅ Attack skill DPS calculation working (311.7 DPS verified)
- ✅ Items and skills loading infrastructure complete
- ✅ Passive tree stat parsing integrated
- ❌ Spell/DOT/totem skills return 0 DPS (MinimalCalc scope limitation)

**Gap Analysis Discovery (2025-11-29):**
- Alec's insight: PoB 2 has complete, curated data files (`Data/Bases/*.lua`, `Data/Gems.lua`)
- Original assumption: "Data.lua has GUI dependencies" → **INCORRECT**
- Reality: Data files are headless-compatible, already partially loaded by MinimalCalc
- Breakthrough: Can use existing PoB data instead of reinventing

**Why Hybrid (Not Full Incremental or Full Subprocess):**
- **Incremental (75-97 hrs):** Exceeds 16-hour threshold, high validation risk
- **Subprocess (19-26 hrs):** Simpler but loses MinimalCalc performance for attacks
- **Hybrid (10-16 hrs):** ✓ Best of both worlds, fits ≤16 hour target

### Implementation Approach

**Phase 1: Load PoB Data & Fix Weapons (Lines to Modify)**

File: `src/calculator/MinimalCalc.lua`

**After line 252 (weapon type info table):**
```lua
-- STORY 2.10 Phase 1: Load PoB weapon base data files
data.itemBases = { }
local itemTypes = {"mace", "spear", "sword", "axe", "bow", "staff", "wand", "sceptre", "dagger", "claw", "crossbow"}
for _, type in ipairs(itemTypes) do
    LoadModule("Data/Bases/"..type, data.itemBases)
end

-- Add Spear to weaponTypeInfo
data.weaponTypeInfo["Spear"] = { name = "Spear", oneHand = true, melee = true, flag = "Spear" }
```

**After line 1019 (weapon type pattern matching):**
```lua
elseif rawType:match("Spear") then
    weaponType = "Spear"
```

**In weapon stub creation (~line 1276):**
Replace hard-coded weapon stubs with:
```lua
-- Use real PoB weapon data from Data/Bases/*.lua
local itemBase = data.itemBases[weaponType]
if itemBase then
    -- Use curated PoB data (PhysicalMin, PhysicalMax, AttackRate, CritChance)
    weaponData.PhysicalMin = itemBase.weaponData[1].PhysicalMin or 10
    weaponData.PhysicalMax = itemBase.weaponData[1].PhysicalMax or 20
    -- etc.
else
    -- Fallback to generic defaults if weapon type unknown
end
```

**Phase 2: Subprocess Fallback (New Files)**

File: `src/calculator/subprocess_calculator.py` (NEW)
```python
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Optional
from ..models.build_data import BuildData, BuildStats

class SubprocessCalculator:
    """Calculator wrapper using external PoB process for guaranteed accuracy."""

    def calculate(self, build: BuildData, timeout: int = 30) -> BuildStats:
        """Run calculation via external PoB subprocess."""
        # 1. Write build XML to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(build.xml_data)
            xml_path = f.name

        try:
            # 2. Execute PoB subprocess (platform-specific)
            if sys.platform == 'win32':
                result = self._call_pob_windows(xml_path, timeout)
            else:
                result = self._call_pob_linux(xml_path, timeout)

            # 3. Parse output and extract stats
            stats = self._parse_pob_output(result)
            return stats

        finally:
            # 4. Cleanup temp file
            Path(xml_path).unlink(missing_ok=True)
```

File: `src/calculator/build_calculator.py` (MODIFIED)
```python
def calculate_build_stats(self, build: BuildData) -> BuildStats:
    """Calculate stats using hybrid approach: MinimalCalc for attacks, subprocess for spells."""

    # Detect skill type
    if self._is_attack_skill(build.skills):
        # Fast path: Use MinimalCalc for attack-based skills
        try:
            return self.pob_engine.calculate(build)
        except Exception as e:
            # Fallback to subprocess if MinimalCalc fails
            logging.warning(f"MinimalCalc failed, falling back to subprocess: {e}")
            return self.subprocess_calc.calculate(build)
    else:
        # Spell/DOT/totem path: Use subprocess for guaranteed accuracy
        return self.subprocess_calc.calculate(build)
```

### Project Structure Notes

**Files to Create:**
- `src/calculator/subprocess_calculator.py` - Subprocess wrapper class

**Files to Modify:**
- `src/calculator/MinimalCalc.lua` - Load PoB data, add Spear support
- `src/calculator/build_calculator.py` - Add hybrid routing logic
- `src/calculator/pob_engine.py` - Add `_is_attack_skill()` helper

**Files to Update:**
- `docs/validation/realistic-validation-results.json` - New validation results
- `tests/integration/test_epic2_validation.py` - Test hybrid routing

**No Changes Needed:**
- `src/models/build_data.py` - BuildStats structure unchanged
- Epic 1 code - Zero modifications (stable API)

### Performance Expectations

**MinimalCalc Path (Attack Builds - 3/15 builds):**
- Single calculation: ~10ms
- Optimization (200 iterations × 10 neighbors): ~20 seconds
- **Status:** Fast path preserved

**Subprocess Path (Spell/DOT/Totem - 12/15 builds):**
- Single calculation: ~50-100ms (subprocess overhead)
- Optimization (200 iterations × 10 neighbors): ~100-200 seconds
- **Status:** Acceptable (< 300s Epic 2 target)

**Hybrid Overall:**
- Attack builds: Fast (~20s per optimization)
- Spell builds: Moderate (~150s per optimization)
- **All within Epic 2 performance budget**

### Risk Mitigation

**Risk 1: PoB subprocess crashes**
- Mitigation: Process timeout (30s), graceful error handling
- Fallback: Return last known good stats or fail gracefully
- Probability: Low (PoB GUI stable on Windows)

**Risk 2: Windows Fatal Exception (ADR-003)**
- Mitigation: Use pytest-xdist for process isolation in tests
- Pattern: `pytest -n auto --dist=loadfile`
- Status: Already documented and working

**Risk 3: Phase 1 doesn't fix all 3 weapon builds**
- Mitigation: Phase 2 subprocess provides fallback
- Impact: Low - worst case all 3 route to subprocess

**Risk 4: Subprocess performance unacceptable**
- Mitigation: Already measured ~75ms per call (acceptable)
- Fallback: Process pooling can reduce overhead by 2-3x if needed

### References

**Gap Analysis Documentation:**
- [Source: docs/stories/2-9-x-calculation-gap-analysis.md] - Complete gap analysis story
- [Source: docs/stories/2-9-x-calculation-gap-analysis-REPORT.md] - Executive summary
- [Source: docs/validation/calculation-gap-REVISED-ANALYSIS-2025-11-29.md] - **CRITICAL** - Approved Hybrid approach details
- [Source: docs/validation/calculation-gap-decision-matrix-2025-11-29.md] - Decision rationale
- [Source: docs/validation/calculation-gap-effort-estimation-2025-11-29.md] - Detailed effort breakdown
- [Source: docs/validation/calculation-gap-categorization-2025-11-29.md] - Failure categories

**Strategic Context:**
- [Source: docs/sprint-change-proposal-2025-11-29.md#Section 6] - Implementation plan approved by Alec
- [Source: docs/tech-spec-epic-2.md#Epic Success Criteria] - Epic-AC-1: 80%+ success rate, Epic-AC-2: 8%+ median improvement
- [Source: docs/stories/2-9-integrate-full-pob-calculation-engine.md] - Story 2.9 baseline (what already works)

**Technical References:**
- [Source: docs/decisions/ADR-003-windows-luajit-cleanup-mitigation.md] - Process isolation pattern
- [Source: external/pob-engine/src/Data/Bases/*.lua] - PoB weapon base data files
- [Source: external/pob-engine/src/Data/Gems.lua] - Spell gem progression data
- [Source: external/pob-engine/src/Modules/CalcOffence.lua] - PoB calculation engine

### Testing Strategy

**Phase 1 Testing (Weapons):**
1. Unit test: `test_load_weapon_bases()` - Verify Data/Bases loading
2. Unit test: `test_spear_pattern_matching()` - Verify Spear detection
3. Integration test: Run validation on 3 weapon builds
4. Expected: 3/3 weapon builds produce DPS > 0

**Phase 2 Testing (Subprocess):**
1. Unit test: `test_skill_type_detection()` - Attack vs spell classification
2. Unit test: `test_subprocess_calculator()` - Subprocess execution and parsing
3. Integration test: Run validation on 12 spell/DOT/totem builds
4. Expected: 12/12 builds produce DPS > 0

**Full Integration:**
1. Run `scripts/validate_realistic_builds.py` on all 15 builds
2. Verify 100% success rate (15/15 builds DPS > 0)
3. Run Epic 2 optimizer validation (Task 6)
4. Verify ≥70% success, ≥5% median improvement, <300s completion

**Performance Benchmarking:**
1. Measure MinimalCalc path: Average calculation time for attack builds
2. Measure Subprocess path: Average calculation time for spell builds
3. Measure full optimization: Time for 3 attack builds, 12 spell builds
4. Document in validation report

## Dev Agent Record

### Context Reference

- [Story Context XML](2-9-1-hybrid-calculation-approach.context.xml) - Generated 2025-11-29

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

<!-- Will be added during implementation -->

### Completion Notes List

<!-- Will be updated as implementation progresses -->

### File List

**Created/Modified:**
<!-- Will be added during implementation -->

---

## Change Log

- **2025-11-29**: Story 2.9.1 drafted by Bob (Scrum Master) based on Story 2.9.x gap analysis
- Status: drafted (ready for story-context and story-ready workflows)
