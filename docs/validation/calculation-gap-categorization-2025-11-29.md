# Calculation Gap Analysis - Failure Categorization
**Date:** 2025-11-29
**Story:** 2.9.x - Comprehensive Calculation Gap Analysis

## Executive Summary

**Success Rate:** 3/15 builds (20%) produce DPS > 0
**Target:** 70%+ required for Epic 2 validation
**Gap:** 50 percentage points below target

## Test Results Overview

| Category | Count | Percentage |
|----------|-------|------------|
| Success (DPS > 0) | 3 | 20% |
| Failure (DPS = 0, no crash) | 8 | 53% |
| Error (calculator crash) | 4 | 27% |
| **Total** | **15** | **100%** |

## Detailed Build Results

| Build | Skill | Type | DPS | Pre-Calc DPS | Status | Root Cause |
|-------|-------|------|-----|--------------|--------|------------|
| deadeye_lightning_arrow_76 | Lightning Arrow | Attack | 311.7 | 18,097 | ✓ SUCCESS | n/a |
| titan_falling_thunder_99 | Falling Thunder | Warcry | 226.5 | 0 | ✓ SUCCESS | n/a |
| witch_essence_drain_86 | Essence Drain | DOT | 204.0 | 33,206 | ✓ SUCCESS | n/a |
| bloodmage_remnants_95 | Life Remnants | DOT | 0 | 0 | ✗ FAIL | Cat-1: DOT calculation engine missing |
| gemling_frost_mage_100 | Frost spell | Spell | 0 | 0 | ✗ FAIL | Cat-2: Spell base damage missing |
| titan_totem_90 | Unknown Totem | Totem | 0 | 0 | ✗ FAIL | Cat-4: Totem/minion mechanics missing |
| warrior_ballista_93 | Siege Ballista | Totem | 0 | 0 | ✗ FAIL | Cat-4: Totem/minion mechanics missing |
| warrior_earthquake_89 | Mace Strike | Attack | 0 | 49,896 | ✗ FAIL | Cat-5: Weapon stub missing (1H Mace) |
| warrior_spear_45 | Explosive Spear | Attack | 0 | 165 | ✗ FAIL | Cat-5: Weapon stub missing (Spear) |
| warrior_spear_71 | Explosive Spear | Attack | 0 | 6,230 | ✗ FAIL | Cat-5: Weapon stub missing (Spear) |
| witch_frost_mage_91 | Frost spell | Spell | 0 | 0 | ✗ FAIL | Cat-2: Spell base damage missing |
| lich_frost_mage_90 | Frost spell | Spell | 0 | 0 | ⚠ ERROR | Cat-3: CalcOffence crash (Data/Global.lua:118) |
| lich_storm_mage_90 | Storm spell | Spell | 0 | 0 | ⚠ ERROR | Cat-3: Python parser error ('list'.get) |
| ritualist_lightning_spear_96 | Explosive Spear | Spell | 0 | 462,800 | ⚠ ERROR | Cat-3: CalcOffence crash (Data/Global.lua:118) |
| titan_infernal_cry_72 | Infernal Cry | Warcry | 0 | 0 | ⚠ ERROR | Cat-3: Python parser error ('list'.get) |

## Failure Categorization by Root Cause

### Category 1: DOT Calculation Engine Missing (1 build)

**Affected Builds:** bloodmage_remnants_95 (Life Remnants)

**Symptoms:**
- skillFlags.attack = false
- mainSkill.output = NIL
- TotalDPS = 0
- No crash, graceful degradation

**Root Cause:**
MinimalCalc.lua has no DOT (Damage Over Time) calculation engine. PoB's CalcOffence.lua requires:
- DOT tick rate calculations
- Ailment base damage formulas
- DOT duration and stacking mechanics

**Evidence:**
```
[MinimalCalc] DEBUG: grantedEffect name: Life Remnants
[MinimalCalc] DEBUG: skillFlags.attack = false
[MinimalCalc] DEBUG: mainSkill.output is NIL!
[MinimalCalc]   TotalDPS: 0
```

**Note:** Essence Drain (also DOT) somehow produces 204 DPS - requires investigation.

---

### Category 2: Spell Base Damage Missing (2 builds)

**Affected Builds:**
- gemling_frost_mage_100
- witch_frost_mage_91

**Symptoms:**
- skillFlags.attack = false
- mainSkill.output = NIL
- TotalDPS = 0
- No crash, graceful degradation

**Root Cause:**
Spell skills require base damage data that isn't present in MinimalCalc.lua:
- Missing Data/Gems.lua spell base damage (levels property)
- Missing spell damage effectiveness formulas
- Missing cast speed → DPS conversion

**Evidence:**
Spells have no base damage range like weapons do. They rely on gem level progression tables in Data/Gems.lua, which MinimalCalc doesn't fully integrate.

---

### Category 3: Calculator Crashes / Parser Errors (4 builds)

**Affected Builds:**
- lich_frost_mage_90 - Data/Global.lua:118 arithmetic on nil
- lich_storm_mage_90 - Python: 'list' object has no attribute 'get'
- ritualist_lightning_spear_96 - Data/Global.lua:118 arithmetic on nil
- titan_infernal_cry_72 - Python: 'list' object has no attribute 'get'

**Symptoms:**
- Calculator crashes before producing any output
- baseline_dps = 0, status = "error"

**Root Causes:**

**3a. Data/Global.lua:118 crashes (2 builds):**
```
attempt to perform arithmetic on local 'result' (a nil value)
```
Likely caused by missing skill stat mapping in SkillStatMap or incomplete skill definition.

**3b. Python parser errors (2 builds):**
```
'list' object has no attribute 'get'
```
XML parsing issue in pob_parser.py - skills section has unexpected list structure instead of dict.

**Evidence:**
These errors prevent any calculation from occurring. Unlike Categories 1-2 which gracefully return 0, these cause hard failures.

---

### Category 4: Totem/Minion Mechanics Missing (2 builds)

**Affected Builds:**
- titan_totem_90
- warrior_ballista_93 (Siege Ballista)

**Symptoms:**
- TotalDPS = 0
- No crash

**Root Cause:**
Totem and minion skills require separate damage calculation pathways:
- Totem DPS = skill DPS × totem count × totem placement speed
- Minion damage scaling uses different modifiers
- MinimalCalc.lua has empty `data.minions = {}` (line 481)

**Evidence:**
Totems and minions are fundamentally different calculation modes that PoB handles separately. MinimalCalc doesn't implement these modes.

---

### Category 5: Missing Weapon Type Stubs (3 builds)

**Affected Builds:**
- warrior_earthquake_89 (Mace Strike) - needs 1H Mace
- warrior_spear_45, warrior_spear_71 (Explosive Spear) - needs Spear

**Symptoms:**
- weaponData1.type = "None" (defaults to unarmed)
- CalcOffence.lua:2200 crashes
- Error caught, DPS = 0

**Root Cause:**
MinimalCalc.lua weapon stub creation (lines 1276-1347) only supports:
- Bow, Crossbow
- Staff
- Two-Handed Sword/Axe/Mace
- Claw, Dagger
- Wand, Sceptre

**MISSING weapon types:**
- **One-Handed Sword** (not Two-Handed)
- **One-Handed Axe** (not Two-Handed)
- **One-Handed Mace** (not Two-Handed) ← Mace Strike needs this
- **Spear** ← Explosive Spear needs this

**Evidence:**
```
[MinimalCalc] DEBUG: grantedEffect name: Mace Strike
[MinimalCalc] DEBUG: weaponData1.type = None  ← WRONG! Should be "One Handed Mace"
[MinimalCalc] ERROR: CalcOffence.lua:2200: attempt to index a nil value
```

Log shows 2,467 calculations with `weaponData1.type = None`, indicating widespread weapon stub failures.

---

## Why Do Some Skills Work?

### Success Case: Lightning Arrow (Attack)
```
grantedEffect name: Lightning Arrow
skillFlags.attack = true
weaponData1.type = Bow  ← Weapon stub created successfully
TotalDPS: 311.7  ← SUCCESS
```

### Success Case: Falling Thunder (Warcry)
```
grantedEffect name: Falling Thunder
weaponData1.type = Staff
TotalDPS: 226.5  ← SUCCESS
```
Warcries that scale with weapon damage work if weapon stub exists.

### Success Case: Essence Drain (DOT - Anomaly!)
```
grantedEffect name: Essence Drain
TotalDPS: 204.0  ← SUCCESS (unexpected!)
```
**Anomaly:** Essence Drain is a DOT skill but produces DPS. Requires investigation - may be hitting a different calculation path or have spell-like properties that MinimalCalc accidentally supports.

---

## Summary by Fix Complexity

| Category | Builds | Estimated Complexity |
|----------|--------|---------------------|
| Cat-5: Missing Weapon Stubs | 3 | **LOW** - Add 4 weapon type mappings (2-4 hours) |
| Cat-3b: Python Parser Errors | 2 | **LOW** - Fix XML parsing edge case (2-4 hours) |
| Cat-3a: Lua Calculation Crashes | 2 | **MEDIUM** - Debug skill stat mapping (4-8 hours) |
| Cat-4: Totem/Minion Mechanics | 2 | **HIGH** - Implement separate calc mode (8-16 hours) |
| Cat-2: Spell Base Damage | 2 | **HIGH** - Integrate gem level damage data (8-16 hours) |
| Cat-1: DOT Calculation Engine | 1 | **VERY HIGH** - Implement full DOT engine (16-24 hours) |

**Note:** Categories are NOT mutually exclusive - a single fix may impact multiple categories.

---

## Next Steps

1. **Task 3:** Estimate total effort for each implementation approach
2. **Task 4:** Create decision matrix (incremental vs hybrid vs subprocess)
3. **Task 5:** Write gap analysis report with recommendation for Alec
