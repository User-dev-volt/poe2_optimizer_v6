# Calculation Gap Analysis - Effort Estimation
**Date:** 2025-11-29
**Story:** 2.9.x - Comprehensive Calculation Gap Analysis

## Effort Estimation Framework

Estimates include:
- **Implementation time** (coding + debugging)
- **Testing time** (unit + integration tests)
- **Risk buffer** (20% for unknowns)

**Confidence Levels:**
- **HIGH** (±25%): Well-understood, similar work done before
- **MEDIUM** (±50%): Some unknowns, moderate complexity
- **LOW** (±100%): Significant unknowns, high complexity

---

## Category-by-Category Effort Estimates

### Category 5: Missing Weapon Type Stubs (3 builds affected)

**Description:** Add missing one-handed weapon types (Mace, Sword, Axe, Spear) to MinimalCalc.lua weapon stub logic.

**Location:** `src/calculator/MinimalCalc.lua` lines 988-1020

**Work Required:**
1. Add weapon type normalization for:
   - "One Handed Mace" (Mace Strike needs this)
   - "One Handed Sword"
   - "One Handed Axe"
   - "Spear" (Explosive Spear needs this)

2. Add weapon stats for each type:
   - Base physical damage range
   - Base attack rate
   - Base crit chance

3. Extend `data.weaponTypeInfo` table (lines 234-252) with new types

**Example Implementation:**
```lua
elseif rawType:match("Mace") then
    if rawType:match("Two Hand") then
        weaponType = "Two Handed Mace"  -- Already exists
    else
        weaponType = "One Handed Mace"  -- ADD THIS
    end
elseif rawType:match("Spear") then
    weaponType = "Spear"  -- ADD THIS
end
```

**Effort Breakdown:**
- Implementation: **1 hour** (pattern matching + stat assignment)
- Testing: **1 hour** (verify 3 failing builds now work)
- Buffer (20%): **0.5 hour**
- **TOTAL: 2-3 hours**

**Confidence:** HIGH (±25%)
**Dependencies:** None
**Risk:** Very low - simple pattern extension
**Impact:** Fixes 3/12 failures (25%)

---

### Category 3b: Python XML Parser Errors (2 builds affected)

**Description:** Fix `'list' object has no attribute 'get'` error in build XML parsing.

**Location:** `src/parsers/pob_parser.py` (skills extraction)

**Root Cause:** Some builds have skills as a list `[{...}, {...}]` instead of dict `{...}`, causing `.get()` to fail.

**Work Required:**
1. Add type checking in `_extract_skills()` function
2. Normalize list → dict handling
3. Handle edge cases (empty skills, multiple skill groups)

**Example Fix:**
```python
skills = skills_section.get("SkillSet", {}).get("SkillGroup", [])
if isinstance(skills, dict):
    skills = [skills]  # Normalize to list

for skill_group in skills:
    # Now safe to iterate
```

**Effort Breakdown:**
- Implementation: **1 hour** (add type checks, test locally)
- Testing: **1 hour** (verify 2 error builds now parse)
- Debugging: **1 hour** (may find additional edge cases)
- Buffer (20%): **0.5 hour**
- **TOTAL: 3-4 hours**

**Confidence:** HIGH (±25%)
**Dependencies:** None
**Risk:** Low - localized fix
**Impact:** Fixes 2/12 failures (17%)

---

### Category 3a: Lua Calculation Crashes (2 builds affected)

**Description:** Fix `Data/Global.lua:118: attempt to perform arithmetic on local 'result' (a nil value)` crash.

**Location:** `external/pob-engine/src/Data/Global.lua:118`

**Root Cause:** Skill stat mapping returns nil for unknown stats, causing arithmetic to fail.

**Work Required:**
1. Investigate what stat is failing (requires debugging with specific builds)
2. Options:
   - **Option A:** Add missing stat definition to SkillStatMap.lua
   - **Option B:** Add nil-check guards in Global.lua
   - **Option C:** Extend MinimalCalc's stat parser to handle unknown stats

3. Test against 2 affected builds (lich_frost_mage_90, ritualist_lightning_spear_96)

**Effort Breakdown:**
- Investigation: **2 hours** (trace error, identify missing stat)
- Implementation: **2 hours** (add stat mapping or guards)
- Testing: **2 hours** (verify fix doesn't break other builds)
- Buffer (20%): **1 hour**
- **TOTAL: 6-8 hours**

**Confidence:** MEDIUM (±50%)
**Dependencies:** Requires access to external/pob-engine source
**Risk:** Medium - touching PoB internals could have side effects
**Impact:** Fixes 2/12 failures (17%)

**Note:** These builds may still return DPS=0 after crash is fixed (underlying spell issue), but at least won't error.

---

### Category 4: Totem/Minion Mechanics Missing (2 builds affected)

**Description:** Implement totem damage calculation mode.

**Location:** `src/calculator/MinimalCalc.lua` (new calculation branch)

**Work Required:**
1. Detect totem skills (skill flags: totem, trap, mine, minion)
2. Implement totem-specific DPS calculation:
   - Totem DPS = base skill DPS × totem count
   - Apply totem placement speed
   - Handle totem life/duration

3. Add totem support to CalcSetup/CalcPerform
4. Populate `data.minions` table with totem stats

**Complexity:** Totems are a separate calculation mode in PoB. Need to:
- Understand how PoB's build.minions works
- May need to stub out minion data structures
- Totem damage scaling uses different modifier paths

**Effort Breakdown:**
- Research: **4 hours** (study PoB totem calculation logic)
- Implementation: **6 hours** (add totem calculation branch)
- Testing: **4 hours** (verify 2 builds + regression tests)
- Buffer (20%): **3 hours**
- **TOTAL: 14-18 hours**

**Confidence:** MEDIUM (±50%)
**Dependencies:** Understanding of PoB minion/totem system
**Risk:** Medium-high - complex interaction with existing calc engine
**Impact:** Fixes 2/12 failures (17%)

**Alternative:** Could skip totems and accept 0 DPS for these builds (lower priority than attack/spell fixes).

---

### Category 2: Spell Base Damage Missing (2 builds affected)

**Description:** Add spell base damage calculation from gem level progression.

**Location:** `src/calculator/MinimalCalc.lua` + `external/pob-engine/src/Data/Gems.lua`

**Work Required:**
1. Extract spell base damage from Data/Gems.lua:
   - Each spell gem has `levels` array with damage per level
   - Format: `{ [1] = {damageEffectiveness=1.2, ...}, [2] = {...}, ...}`

2. Add spell damage calculation logic:
   - Get gem level from build
   - Look up base damage for that level
   - Apply damage effectiveness
   - Convert cast speed → DPS

3. Integrate with CalcOffence spell damage path

**Complexity:** Spells have much more complex damage formulas than attacks:
- Added damage from gear
- Spell damage modifiers (% increased)
- Elemental damage types
- Crit calculations
- Cast speed vs attack speed

**Effort Breakdown:**
- Research: **4 hours** (understand PoB spell damage formulas)
- Implementation: **8 hours** (integrate gem data, add spell calc)
- Testing: **6 hours** (verify 2 builds + check for regressions)
- Buffer (20%): **4 hours**
- **TOTAL: 18-24 hours**

**Confidence:** LOW (±100%)
**Dependencies:**
- May require fixes to Data/Gems.lua loading (currently loads but doesn't use level data)
- May expose additional missing data (spell crit, conversion, etc.)

**Risk:** High - spell calculations are complex, likely to uncover more gaps
**Impact:** Fixes 2/12 failures (17%), but **may only partially** fix them

**Warning:** This might be a rabbit hole. Spells have many dependencies (base damage, added damage, conversions, ailments) that could cascade into more work.

---

### Category 1: DOT Calculation Engine Missing (1 build affected)

**Description:** Implement damage-over-time calculation engine.

**Location:** `src/calculator/MinimalCalc.lua` (new DOT calculation system)

**Work Required:**
1. Implement DOT base damage calculation:
   - Ignite: % of hit damage per second
   - Poison: % of hit damage per second
   - Bleed: flat physical per second
   - Chaos DOT: spell damage × DOT multi

2. Add DOT duration calculations:
   - Base duration from skill
   - % increased duration modifiers
   - Duration caps

3. Implement DOT stacking:
   - Number of DOTs that can stack
   - Total DPS = single DOT × stacks

4. Add DOT tick rate handling:
   - Standard: 1 tick per second
   - Fast dots: multiple ticks

5. Integrate with ailment system (data.ailmentData already stubbed)

**Complexity:** DOT is one of PoB's most complex subsystems:
- Multiple DOT types with different formulas
- Interaction with hit damage
- Stacking mechanics
- Duration scaling
- Tick rate variations
- Ailment thresholds

**Effort Breakdown:**
- Research: **8 hours** (study PoB DOT engine in CalcOffence.lua)
- Implementation: **16 hours** (implement DOT formulas, stacking, duration)
- Testing: **8 hours** (test Life Remnants + Essence Drain anomaly investigation)
- Buffer (20%): **6 hours**
- **TOTAL: 32-40 hours**

**Confidence:** LOW (±100%)
**Dependencies:**
- Spell base damage (Category 2) may need to be done first
- May need ailment calculation fixes
- Likely to expose more missing data

**Risk:** Very high - DOT system is deeply intertwined with PoB's calculation engine
**Impact:** Fixes 1/12 failures (8%), but **may** also fix Essence Drain anomaly

**Alternative:** Full subprocess for DOT skills (hybrid approach) avoids this entirely.

---

## Total Effort by Implementation Approach

### Approach A: Fix All Categories Incrementally

**Sequential Implementation Order (lowest to highest risk):**

1. **Cat 5:** Weapon stubs → **2-3 hours**
2. **Cat 3b:** Python parser → **3-4 hours**
   **→ Checkpoint: 5-7 hours, 5/12 failures fixed**

3. **Cat 3a:** Lua crashes → **6-8 hours**
   **→ Checkpoint: 11-15 hours, 7/12 failures fixed (but may still be 0 DPS)**

4. **Cat 4:** Totems → **14-18 hours**
   **→ Checkpoint: 25-33 hours, 9/12 failures fixed**

5. **Cat 2:** Spell damage → **18-24 hours**
   **→ Checkpoint: 43-57 hours, 11/12 failures potentially fixed**

6. **Cat 1:** DOT engine → **32-40 hours**
   **→ Final: 75-97 hours, 12/12 failures potentially fixed**

**TOTAL INCREMENTAL: 75-97 hours**

**Success Rate Projection:**
- After step 2 (Cat 5 + 3b): ~40-50% (weapon + parser fixes)
- After step 3 (+ Cat 3a): ~50-60% (crashes fixed, but may not add DPS)
- After step 4 (+ Cat 4): ~60-65% (totems working)
- After step 5 (+ Cat 2): ~70-75% (spells working)
- After step 6 (+ Cat 1): ~75-85% (full coverage)

**Risks:**
- **Cascading dependencies:** Spell/DOT fixes may uncover more gaps
- **Unknown unknowns:** 20% buffer may not be enough
- **Validation thrashing:** Fix → test → discover new gap → repeat
- **Scope creep:** Could easily balloon to 100-150 hours

---

### Approach B: Hybrid (MinimalCalc for attacks, subprocess for spells/DOT)

**Implementation:**
1. **Cat 5:** Fix weapon stubs → **2-3 hours**
2. **Cat 3b:** Fix parser → **3-4 hours**
3. **Cat 3a:** Fix Lua crashes → **6-8 hours**
4. **Add subprocess fallback:** If skill is NOT attack → route to external PoB → **8-12 hours**
   - Detect spell/DOT/totem skills
   - Call external PoB process with full build XML
   - Parse PoB output and extract DPS
   - Handle errors gracefully

**TOTAL HYBRID: 19-27 hours**

**Success Rate Projection:**
- Attack skills: Continue using fast MinimalCalc path (311 DPS for Lightning Arrow)
- Spell/DOT/totem: Use full PoB subprocess (guaranteed correct, ~50-100ms overhead)
- **Expected: 100% coverage** (all skill types supported)

**Trade-offs:**
- **Pro:** Known scope, guaranteed coverage
- **Pro:** Preserves MinimalCalc performance for attack builds
- **Pro:** No risk of validation thrashing
- **Con:** Performance hit for spell builds (~50-100ms per calculation)
- **Con:** Two code paths to maintain

---

### Approach C: Full Subprocess (replace MinimalCalc entirely)

**Implementation:**
1. **Cat 3b:** Fix parser → **3-4 hours** (still needed to load builds)
2. **Replace MinimalCalc with external PoB:** → **12-16 hours**
   - Remove MinimalCalc.lua integration
   - Always call external PoB process
   - Parse full PoB output (DPS, life, defenses)
   - Batch multiple builds for efficiency
3. **Optimize subprocess performance:** → **4-6 hours**
   - Process pooling
   - Build XML caching
   - Parallel calculation

**TOTAL SUBPROCESS: 19-26 hours**

**Success Rate Projection:**
- **100% coverage** (PoB handles everything correctly)

**Trade-offs:**
- **Pro:** Guaranteed complete coverage forever
- **Pro:** No future gaps (PoB updates flow through automatically)
- **Pro:** Known fixed scope
- **Con:** Performance impact for ALL builds (~50-100ms overhead)
- **Con:** Throws away MinimalCalc work (sunk cost)
- **Con:** External dependency on PoB process stability

---

## Recommendation Matrix

| Approach | Total Effort | Success Rate | Performance | Risk | Maintenance |
|----------|-------------|--------------|-------------|------|-------------|
| **Incremental** | 75-97 hrs | 75-85% | Fast (MinimalCalc) | **VERY HIGH** | High complexity |
| **Hybrid** | 19-27 hrs | **100%** | Mixed (fast attacks, slow spells) | **LOW** | Two code paths |
| **Subprocess** | 19-26 hrs | **100%** | Slower all builds | **VERY LOW** | Simple, stable |

**Decision Framework (from Sprint Change Proposal):**
- If total ≤16 hrs → Incremental ✗ (75-97 hrs >> 16 hrs)
- If 16-40 hrs → Hybrid ✓ (19-27 hrs fits)
- If >40 hrs → Full subprocess ✓ (19-26 hrs is below threshold, but subprocess is safer)

**Conclusion:** Both **Hybrid** and **Subprocess** approaches are viable. Incremental approach is **NOT recommended** due to extreme effort and validation risk.

---

## Next Steps

**Task 4:** Create detailed decision matrix comparing Hybrid vs Subprocess approaches
**Task 5:** Write executive summary and recommendation for Alec
