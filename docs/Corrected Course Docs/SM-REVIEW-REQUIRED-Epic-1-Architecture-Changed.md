# 🚨 SM REVIEW REQUIRED: Epic 1 Architecture Fundamentally Changed

**Date:** 2025-10-17
**Priority:** CRITICAL - BLOCKING Epic 1 Progress
**Assigned To:** SM Agent (Bob)
**Requested By:** Dev Agent (Amelia) - Story 1.4 Implementation

---

## Executive Summary

Story 1.4 achieved a major technical breakthrough but discovered that the **original Epic 1 architecture is impossible**. The assumptions in the PRD and tech spec about using HeadlessWrapper.lua and loading full PoB data are **architecturally invalid**.

**Status Change:** Blocked → InProgress (calculation engine loaded successfully)

**Critical Finding:** We CAN load the PoB calculation engine, but NOT the way we planned. We need SM to replan Stories 1.5-1.8 based on the new MinimalCalc.lua architecture.

---

## What Happened

### Session 2: Architectural Blocker Discovered
- HeadlessWrapper.lua requires native GUI runtime (Windows windowing, C++ bindings)
- Triggers Windows Fatal Exception 0xe24c4a02 (cannot be caught)
- Data.lua loads 100+ sub-modules with GUI dependencies (skills/gems/items/uniques/bosses/minions)
- 4 of 6 acceptance criteria were **architecturally impossible**
- Status: **Blocked - Architectural Decision Required**

### Session 3: BREAKTHROUGH - Option A Successfully Implemented
- Created MinimalCalc.lua custom bootstrap
- Discovered calculation engine needs ONLY minimal constants (Data/Global.lua + Data/Misc.lua)
- Successfully loaded Modules/Calcs.lua + ALL sub-modules (CalcSetup, CalcPerform, CalcDefence, CalcOffence, etc.)
- All 10 integration tests passing
- No crashes, stable baseline achieved
- Status: **InProgress - Calculation Engine Loaded**

---

## Architectural Impact

### Original Plan (PRD/Tech Spec)
```
HeadlessWrapper.lua → Launch.lua → Full Data.lua → PoB Build Object
                                    ↓
                           100+ sub-modules loaded
                           (skills, gems, items, uniques, etc.)
```

### New Reality (MinimalCalc.lua)
```
MinimalCalc.lua → Data/Global.lua (enums only)
                → Data/Misc.lua (constants only)
                → Modules/Calcs.lua (calculation engine)
                ✅ NO GUI dependencies
                ❌ NO skills/gems/items data
                ❌ NO passive tree data
```

### Key Differences
| Aspect | Original Plan | New Architecture |
|--------|--------------|------------------|
| Bootstrap | HeadlessWrapper.lua | MinimalCalc.lua (custom) |
| Data Loading | Full Data.lua (100+ modules) | Minimal constants only |
| Skills/Gems | ✅ Loaded from Data.lua | ❌ Need stubs or selective loading |
| Passive Tree | ✅ Loaded from Data.lua | ❌ Need alternative source |
| Items | ✅ Loaded from Data.lua | ❌ Need stubs or selective loading |
| Build Object | ✅ PoB provides | ❌ Must construct manually |
| XML Support | ✅ HeadlessWrapper handles | ⚠️ May not be needed |

---

## Stories Affected

### Story 1.5: Execute BuildData → BuildStats Calculation ⚠️
**Original Scope:** Pass BuildData to PoB's existing build object
**New Scope:** Must construct minimal build object from scratch

**Questions for SM:**
- Can we calculate with NO skills/gems data? (likely need minimal stubs)
- Can we calculate with NO passive tree data? (likely need minimal hardcoded nodes)
- Can we calculate with NO item data? (likely need minimal base types)

**Recommendation:** Add task for "Construct Minimal Build Object in Lua"

---

### Story 1.6: BuildData → PoB XML Conversion ⚠️
**Original Scope:** Convert BuildData to PoB XML format
**New Scope:** May not be needed at all

**Questions for SM:**
- Is XML still needed? (for PoB import/export compatibility?)
- Or can we construct build object directly in Lua, bypassing XML entirely?

**Recommendation:** Evaluate if this story can be eliminated or drastically simplified

---

### Story 1.7: Extract Passive Tree Graph 🚨
**Original Scope:** Access passive tree from loaded Data.lua
**New Scope:** Data.lua not loaded - need alternative source

**Questions for SM:**
- Can we load ONLY Data/3_0.lua (passive tree version)? → Need to test for GUI dependencies
- Or export passive tree to JSON and load that? → Maintenance overhead
- Or hardcode minimal subset of nodes? → Limited functionality

**Recommendation:** Add spike story to investigate Data/3_0.lua safety, or create "Export PoB Passive Tree to JSON" story

---

### Story 1.8: Optimize Calculation Performance ⚠️
**Original Scope:** Profile and optimize PoB calculation calls
**New Scope:** Performance characteristics completely different with minimal data

**Questions for SM:**
- What's the performance baseline with MinimalCalc.lua? → Need measurements
- Where are the bottlenecks with minimal data? → May be different than full data

**Recommendation:** Add task for "Measure MinimalCalc.lua Performance Baseline"

---

## Architectural Decisions Needed

The SM must make strategic decisions on these four critical areas:

### 1. Data Loading Strategy
**Options:**
- **A:** Continue with minimal constants only, stub out missing data as needed (FASTEST)
- **B:** Selectively load some Data.lua sub-modules (test each for GUI dependencies) (RISKY)
- **C:** Export PoB data to JSON format, load from JSON (MOST MAINTENANCE)

**Recommendation:** Start with Option A (minimal stubs), expand to Option B if needed

---

### 2. Build Object Construction
**Options:**
- **A:** Construct minimal Lua build object directly in MinimalCalc.lua (CLEANEST)
- **B:** Create Python → Lua build object bridge in pob_engine.py (MORE FLEXIBLE)
- **C:** Use PoB XML as intermediate format (original plan, may be unnecessary)

**Recommendation:** Option A for MVP, Option B if we need Python-side build manipulation

---

### 3. Passive Tree Data Source
**Options:**
- **A:** Load Data/3_0.lua directly (if no GUI dependencies) → NEED TO TEST
- **B:** Export passive tree to JSON, load from JSON (one-time export, ongoing maintenance)
- **C:** Hardcode minimal subset of nodes for MVP (limited functionality)

**Recommendation:** Test Option A first (spike story), fall back to Option B if needed

---

### 4. Skills/Gems/Items Data
**Options:**
- **A:** Create minimal hardcoded stubs for common builds (FASTEST for MVP)
- **B:** Selectively load specific Data/Skills/* files (test each for safety) (RISKY)
- **C:** Extract data to JSON, load from JSON (maintenance overhead)

**Recommendation:** Option A for MVP (hardcode ~5 common skills), expand later

---

## Recommended SM Actions

### Phase 1: Review and Understand (1-2 hours)
1. ✅ Read `docs/stories/story-1.4-breakthrough-summary.md` (comprehensive technical details)
2. ✅ Read `docs/stories/story-1.4-minimal-calc-progress.md` (discovery process)
3. ✅ Read Story 1.4 "SM Review Required" section (lines 725-836)
4. ✅ Review MinimalCalc.lua source code (`src/calculator/MinimalCalc.lua`)

### Phase 2: Make Architectural Decisions (30 minutes)
1. ✅ Decide on data loading strategy (A, B, or C)
2. ✅ Decide on build object construction approach (A, B, or C)
3. ✅ Decide on passive tree data source (A, B, or C)
4. ✅ Decide on skills/gems/items data approach (A, B, or C)
5. ✅ Document decisions in PRD Section 5.2

### Phase 3: Update Stories (2-3 hours)
1. ✅ Update Story 1.5 with minimal build object construction tasks
2. ✅ Update Story 1.6 (simplify or eliminate XML conversion)
3. ✅ Update Story 1.7 with passive tree data source investigation
4. ✅ Update Story 1.8 with MinimalCalc.lua performance baseline measurement
5. ✅ Consider creating NEW Story: "Create Minimal Data Stubs for Calculations"

### Phase 4: Update Documentation (1 hour)
1. ✅ Update PRD Section 5.2 (Epic 1 scope) with MinimalCalc.lua approach
2. ✅ Update tech-spec-epic-1.md with revised architecture diagrams
3. ✅ Update backlog for any downstream impacts (Stories 1.9+)

### Phase 5: Communicate Decisions (15 minutes)
1. ✅ Update Story 1.4 with SM decisions
2. ✅ Mark SM Review section as complete
3. ✅ Notify Dev Agent to proceed with Story 1.5 (or continue Story 1.4 Calculate() implementation)

---

## Success Criteria

**SM Review Complete When:**
1. ✅ All four architectural decisions documented
2. ✅ Stories 1.5-1.8 updated with revised tasks
3. ✅ PRD Section 5.2 updated
4. ✅ Tech spec updated with MinimalCalc.lua architecture
5. ✅ New stories created if needed
6. ✅ Backlog reviewed for downstream impacts
7. ✅ Dev Agent notified to proceed

---

## Key Files for SM Review

**Primary Documentation:**
- `docs/stories/story-1.4.md` - Lines 725-836 (SM Review Required section)
- `docs/stories/story-1.4-breakthrough-summary.md` - Technical deep dive (87 KB)
- `docs/stories/story-1.4-minimal-calc-progress.md` - Discovery process log

**Source Code:**
- `src/calculator/MinimalCalc.lua` - Custom bootstrap (198 lines)
- `src/calculator/pob_engine.py` - Python integration layer

**Tests:**
- `tests/integration/test_headlesswrapper_loading.py` - All 10 tests passing

---

## Questions for SM

1. **MVP Scope:** Should we target minimal viable calculation (base stats only) or full build calculation (with skills/tree/items)?

2. **Data Strategy:** Are you comfortable with hardcoded stubs for MVP, or do you prefer extracting PoB data to JSON?

3. **XML Requirement:** Do we need PoB XML support for import/export, or can we skip it entirely?

4. **Passive Tree:** Should we investigate loading Data/3_0.lua (risky but complete) or export to JSON (safe but maintenance)?

5. **Timeline Impact:** How does this architecture change affect Epic 1 timeline? (Original: 40-60 hours, New: TBD based on decisions)

---

## Contact

**SM Agent (Bob)** - Epic 1 Story Master
**Dev Agent (Amelia)** - Story 1.4 Implementer (available for questions)

**Status:** Awaiting SM architectural decisions before Story 1.5 can begin.

---

## Appendix: Test Results

```bash
$ python -m pytest tests/integration/test_headlesswrapper_loading.py -v
============================= 10 passed in 0.17s ==============================

[MinimalCalc] PoB src directory: D:/poe2_optimizer_v6/external/pob-engine/src
[MinimalCalc] Creating stubs for external libraries and GUI functions...
[MinimalCalc] ===== STEP 1: Loading GameVersions.lua (pure data, no GUI) =====
[MinimalCalc] SUCCESS: latestTreeVersion = 0_3
[MinimalCalc] ===== STEP 2: Loading Common.lua (utility functions) =====
[MinimalCalc] SUCCESS: Common.lua loaded, common.classes available
[MinimalCalc] ===== STEP 3: Loading Data/Global.lua (ModFlag, KeywordFlag, SkillType) =====
[MinimalCalc] SUCCESS: Global.lua loaded, ModFlag/KeywordFlag/SkillType available
[MinimalCalc] ===== STEP 4: Loading Data/Misc.lua (game constants) =====
[MinimalCalc] SUCCESS: Misc.lua loaded, data.characterConstants/gameConstants/monsterConstants available
[MinimalCalc] ===== STEP 5: Loading Modules/Calcs.lua (calculation engine) =====
[MinimalCalc] SUCCESS: Calcs.lua loaded
[MinimalCalc] ===== Bootstrap complete - minimal PoB environment ready =====
```

**Proof of Success:** Calculation engine is loaded and stable. Now we need SM guidance on how to use it.
