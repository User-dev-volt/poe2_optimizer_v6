# Diagnostic Report: PoB Main Skill Selection Issue

**Story**: 2.9.2 Spell/DOT MinimalCalc Enhancement
**Date**: 2025-12-01
**Agent**: Amelia (Dev Agent)
**Status**: Root cause identified

---

## Executive Summary

Spell builds return DPS = 0 not because spell damage calculation is missing, but because **the wrong skill is being selected for DPS calculation**. PoB is calculating DPS for Pain Offering (a minion buff) instead of the actual damaging spells like Fireball or Frost Bomb.

**Root Cause**: The `mainSocketGroup` attribute from PoB XML is not being read and passed to MinimalCalc, causing it to default to socket group #1 (Pain Offering) instead of the user-selected spell.

---

## Investigation Findings

### Finding #1: PoB's Main Skill Selection Logic (CalcSetup.lua)

**Location**: `external/pob-engine/src/Modules/CalcSetup.lua:1731-1743`

```lua
if index == env.mainSocketGroup and #socketGroupSkillList > 0 then
    local activeSkillIndex
    if env.mode == "CALCS" then
        group.mainActiveSkillCalcs = m_min(#socketGroupSkillList, group.mainActiveSkillCalcs or 1)
        activeSkillIndex = group.mainActiveSkillCalcs
    else
        activeSkillIndex = m_min(#socketGroupSkillList, group.mainActiveSkill or 1)
    end
    env.player.mainSkill = socketGroupSkillList[activeSkillIndex]
end
```

**How it works**:
1. PoB selects socket group at index `env.mainSocketGroup`
2. Within that group, selects skill at index `mainActiveSkillCalcs` (defaults to 1)
3. This becomes `env.player.mainSkill`

### Finding #2: mainSocketGroup Source

**Location**: `external/pob-engine/src/Modules/Build.lua:936`

```lua
self.mainSocketGroup = tonumber(xml.attrib.mainSkillIndex)
                    or tonumber(xml.attrib.mainSocketGroup)
                    or 1
```

**Location**: `external/pob-engine/src/Modules/CalcSetup.lua:1465-1466`

```lua
env.calcsInput.skill_number = m_min(m_max(#build.skillsTab.socketGroupList, 1),
                                    env.calcsInput.skill_number or 1)
env.mainSocketGroup = env.calcsInput.skill_number
```

**How it works**:
- In GUI mode: Reads from XML attribute `mainSocketGroup` or `mainSkillIndex`
- In CALCS mode: Uses `env.calcsInput.skill_number`
- **Defaults to 1 if not set**

### Finding #3: MinimalCalc Socket Group Creation

**Location**: `src/calculator/MinimalCalc.lua:1252-1312`

MinimalCalc creates **ONE socket group per skill**:

```lua
for i, skillData in pairs(buildData.skills) do
    -- Create gem instance
    local gemInstance = { ... }

    -- Create socket group
    local socketGroup = {
        label = skillData.name or grantedEffect.name,
        enabled = true,
        gemList = { gemInstance },
        slot = nil,
        source = "Build"
    }

    table.insert(build.skillsTab.socketGroupList, socketGroup)
    -- ...
end
```

**Result**:
- Socket Group #1 = Pain Offering
- Socket Group #2 = Hypothermia
- Socket Group #3 = Flame Wall
- Socket Group #4 = Frost Bomb ← **Actual damaging spell!**
- etc.

### Finding #4: Missing Data Flow

**Problem**: The build XML contains `mainSocketGroup` but it never reaches MinimalCalc!

1. **XML File** (`witch_frost_mage_91.xml`):
   ```xml
   <Build ... mainSocketGroup="2" ...>
   ```

2. **BuildData Model** (`src/models/build_data.py`):
   - ❌ Does NOT have `main_socket_group` field
   - ✅ Has: `character_class`, `level`, `skills`, `items`, etc.

3. **PoB Parser** (`src/parsers/pob_parser.py`):
   - ❌ Does NOT extract `mainSocketGroup` from XML

4. **MinimalCalc.lua** (`src/calculator/MinimalCalc.lua`):
   - ❌ Does NOT set `env.calcsInput.skill_number`
   - Defaults to 1, selecting Pain Offering instead of the actual spell

### Finding #5: Actual Build Configuration

**Example**: `witch_frost_mage_91` build

**XML**: `mainSocketGroup="2"`
**Expected**: Calculate DPS for socket group #2
**Actual**: Calculates DPS for socket group #1 (Pain Offering)

**Skills in Build**:
1. Pain Offering (Minion/Buff) ← **Currently selected (wrong!)**
2. Hypothermia (Likely a support gem or aura) ← **Should be selected!**
3. Flame Wall (Spell)
4. Frost Bomb (Spell)
5. Leap Slam (Attack)
6. Blink (Movement)
7. Sigil of Power (Buff)
8. Discipline (Aura)

### Finding #6: Spell Detection Code is CORRECT

**Location**: `src/calculator/MinimalCalc.lua:1635-1651`

The spell detection using `skillTypes[SkillType.Spell]` is **working as intended**:

```lua
local skillTypes = env.player.mainSkill.skillTypes
local isSpell = skillTypes and skillTypes[SkillType.Spell]
```

**Test Results**:
- Pain Offering: `skillTypes[SkillType.Spell] = nil` ✅ Correct (it's a Buff/Minion skill)
- Pain Offering has types: Buff, Minion, Offering, Area, Duration

The code correctly identifies Pain Offering as NOT a spell. The problem is that Pain Offering shouldn't be the main skill in the first place!

---

## Impact Analysis

### Current Behavior
- **All spell builds**: Calculate DPS for first skill in build (usually a buff/aura)
- **Result**: DPS = 0 (correct for non-damaging skills)
- **Epic 2 validation**: 4/15 builds pass (only weapon builds)

### After Fix
- **Spell builds**: Calculate DPS for user-selected main skill
- **Expected Result**: DPS > 0 for actual damaging spells
- **Epic 2 validation**: Should achieve 100% success rate (15/15 builds)

---

## Solution Options

### Option A: Pass mainSocketGroup from Python to Lua (RECOMMENDED)

**Pros**:
- Respects user's skill selection from PoB GUI
- Minimal changes to calculation logic
- Consistent with PoB's intended behavior

**Cons**:
- Requires changes across 3 components (parser, model, MinimalCalc)

**Implementation Steps**:
1. Add `main_socket_group: int` field to BuildData model
2. Extract `mainSocketGroup` attribute in pob_parser.py
3. Pass it to MinimalCalc via `buildData.mainSocketGroup`
4. Set `build.mainSocketGroup` in MinimalCalc before calling `calcs.initEnv()`

**Estimated Effort**: 1-2 hours

---

### Option B: Auto-select highest DPS skill

**Pros**:
- Automatically finds the damaging skill
- No dependency on XML attributes

**Cons**:
- Requires calculating ALL skills (performance hit)
- May not match user's intent
- More complex logic

**Estimated Effort**: 4-6 hours

---

### Option C: Heuristic skill selection (find first spell/attack)

**Pros**:
- Simple logic: skip buffs/auras, find first damaging skill
- No XML dependency

**Cons**:
- May select wrong skill if multiple damaging skills present
- Doesn't respect user preference

**Estimated Effort**: 2-3 hours

---

## Recommended Approach

**Option A** is recommended because:
1. Respects the user's skill selection (mainSocketGroup is explicitly set in PoB)
2. Minimal performance impact
3. Consistent with PoB's design
4. Lowest risk of selecting wrong skill

---

## Next Steps

1. ✅ **Complete**: Diagnosis and root cause analysis
2. **Pending**: Implement Option A (pass mainSocketGroup)
3. **Pending**: Test with spell builds (verify DPS > 0)
4. **Pending**: Continue with spell base damage extraction (Task 2.2+)
5. **Pending**: Epic 2 validation (15/15 builds)

---

## Related Files

- **PoB Engine**: `external/pob-engine/src/Modules/CalcSetup.lua:1731-1743`
- **Python Model**: `src/models/build_data.py:45-83`
- **Parser**: `src/parsers/pob_parser.py`
- **Calculator**: `src/calculator/MinimalCalc.lua:1252-1312`
- **Test Builds**: `tests/fixtures/realistic_builds/witch_frost_mage_91.xml`

---

**End of Diagnostic Report**
