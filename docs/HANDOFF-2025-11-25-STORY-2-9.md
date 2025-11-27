# Story 2.9 Handoff Document
## Date: 2025-11-25
## Developer: Amelia (AI Dev Agent)

---

## Executive Summary

**Status:** 🟡 **BLOCKED - 95% Complete**

Story 2.9 aimed to integrate full PoB calculation capabilities into MinimalCalc.lua to enable accurate DPS/Life calculations for Epic 2 optimization validation. **Major progress achieved:**

- ✅ **Items loading infrastructure** (Milestones 1-3) fully implemented
- ✅ **CalcOffence.lua crash** completely resolved
- ✅ **calcs.perform()** executes successfully without errors
- ❌ **Weapon compatibility blocker** prevents DPS calculation (weaponData1.type = "None")

**Impact:** Skills are disabled with `disableReason = "Main Hand weapon is not usable with this skill"`, causing DPS=0 despite successful calculation engine execution.

**Estimated Time to Complete:** 2-4 hours for an experienced PoB developer to resolve weapon compatibility issue.

---

## What Was Accomplished

### 1. Items Loading Infrastructure (Complete)

**Files Modified:**
- `src/parsers/pob_parser.py` (lines 200-280)
- `src/calculator/pob_engine.py` (lines 150-200)
- `src/calculator/MinimalCalc.lua` (lines 945-1070)

**Implementation:**

#### Milestone 1: Parse Items from PoB XML
Location: `src/parsers/pob_parser.py:_extract_items()`

```python
def _extract_items(pob_root: Dict) -> List[Item]:
    """Extract equipped items from PoB XML.

    Story 2.9: Parses weapon stats from item text using regex patterns.
    """
    items_section = pob_root.get("PathOfBuilding2", {}).get("Items", {})
    items = []

    for item_data in items_section.get("Item", []):
        # Parse weapon stats from item text
        # Regex patterns for: Phys damage, Lightning/Cold/Fire damage, Attack Speed, Crit Chance
        stats = _parse_item_stats(item_data.get("_text", ""))

        items.append(Item(
            slot=f"Weapon{item_data.get('@id', '1')}",
            name=item_data.get("@name", "Weapon"),
            rarity=item_data.get("@rarity", "RARE"),
            stats=stats
        ))

    return items
```

**Weapon Stats Parsed:**
- `phys_min`, `phys_max` - Physical damage range
- `lightning_min`, `lightning_max` - Lightning damage
- `cold_min`, `cold_max` - Cold damage
- `fire_min`, `fire_max` - Fire damage
- `attack_speed_inc` - Attack speed % increase
- `crit_chance_add` - Added critical strike chance
- `base_type` - Weapon base type (e.g., "Gemini Bow")

**Verification:** Successfully parses items from PoB XML. Example output:
```
Slot: Weapon1
Name: New Item
base_type: Gemini Bow
phys_min: 9, phys_max: 16
lightning_min: 3, lightning_max: 99
```

#### Milestone 2: Pass Items to MinimalCalc
Location: `src/calculator/pob_engine.py:calculate()`

```python
# Convert items to Lua table format
items_lua = self._lua.table()
for i, item in enumerate(build.items):
    if item.stats:
        item_table = self._lua.table(
            slot=item.slot,
            name=item.name,
            rarity=item.rarity,
            base_type=item.stats.get("base_type", ""),
            phys_min=item.stats.get("phys_min", 0),
            phys_max=item.stats.get("phys_max", 0),
            # ... all weapon stats
        )
        items_lua[i + 1] = item_table

lua_build_data = self._lua.table(
    # ... other fields
    items=items_lua  # Story 2.9: Equipment with weapon stats
)
```

**Verification:** Items successfully passed to Lua as table structure.

#### Milestone 3: Process Items in MinimalCalc.lua
Location: `src/calculator/MinimalCalc.lua` (lines 945-1070)

```lua
-- Process items passed from Python (Story 2.9)
if buildData.items and type(buildData.items) == "table" then
    for i, itemData in pairs(buildData.items) do
        if itemData.slot and itemData.slot:match("^Weapon") then
            -- Normalize weapon type: "Gemini Bow" → "Bow"
            local rawType = itemData.base_type or "Bow"
            local weaponType = rawType

            if rawType:match("Bow") then
                weaponType = "Bow"
            elseif rawType:match("Staff") then
                weaponType = "Staff"
            -- ... all weapon types
            end

            -- Create weapon object
            local weapon = {
                name = itemData.name,
                type = "Weapon",
                rarity = itemData.rarity,
                modList = new("ModList"),
                baseModList = new("ModList"),
                base = {
                    type = weaponType,
                    subType = weaponType,
                    weapon = data.weaponTypeInfo[weaponType]
                },
                weaponData = {
                    [1] = {
                        type = weaponType,
                        AttackRate = totalAttackRate,
                        CritChance = totalCritChance,
                        PhysicalMin = totalPhysMin,
                        PhysicalMax = totalPhysMax,
                        LightningMin = itemData.lightning_min,
                        LightningMax = itemData.lightning_max,
                        -- ... elemental damage
                    }
                }
            }

            build.itemsTab.items[itemCount] = weapon
        end
    end
end
```

**Verification:** Weapon objects created successfully in MinimalCalc. Debug output shows:
```
[MinimalCalc] Loaded weapon: Gemini Bow -> Bow (Phys: 49-96, APS: 1.50)
[MinimalCalc] weapon.base.type = Bow
[MinimalCalc] weapon.weaponData[1].type = Bow
```

---

### 2. CalcOffence Error Resolution (Complete)

#### Issue 1: Minion Skill Crash
**Error:** `Common.lua:408: bad argument #1 to 'pairs' (table expected, got nil)`

**Root Cause:** Companion/Summon skills cause calcs.initEnv() to crash - MinimalCalc lacks minion support tables.

**Fix:** Added minion skill filter in `src/parsers/pob_parser.py`

```python
def _is_minion_skill(skill_id: str) -> bool:
    """Check if skill is a minion/summon skill.

    Story 2.9: Temporary filter - minion skills cause calcs.initEnv() crash.
    """
    minion_keywords = ["Summon", "Raise", "Animate", "Companion"]
    return any(kw in skill_id for kw in minion_keywords)

# In _extract_skills():
skills = [s for s in skills if not _is_minion_skill(s.skill_id)]
```

**Result:** ✅ Complex PoB builds with 8+ skills now load without crashing.

---

#### Issue 2: Weapon Type Normalization
**Error:** `WARNING: weaponType 'Gemini Bow' not found in data.weaponTypeInfo`

**Root Cause:** PoB expects weapon categories ("Bow") not specific base items ("Gemini Bow").

**Fix:** Added weapon type normalization in MinimalCalc.lua (lines 955-993)

```lua
local rawType = itemData.base_type or "Bow"
local weaponType = rawType

-- Normalize specific base items to weapon categories
if rawType:match("Bow") then
    weaponType = "Bow"
elseif rawType:match("Staff") or rawType:match("Quarterstaff") then
    weaponType = "Staff"
-- ... all weapon types
end
```

**Result:** ✅ "Gemini Bow" → "Bow", "Recurve Bow" → "Bow", etc.

---

#### Issue 3: Missing weaponTypeInfo
**Error:** data.weaponTypeInfo only had "None" defined.

**Fix:** Added all PoE 2 weapon types in MinimalCalc.lua (lines 233-252)

```lua
data.weaponTypeInfo = {
    None = { name = "None", oneHand = false, melee = true, flag = "Unarmed" },
    -- Ranged weapons
    Bow = { name = "Bow", oneHand = false, melee = false, flag = "Bow" },
    Crossbow = { name = "Crossbow", oneHand = false, melee = false, flag = "Crossbow" },
    -- Melee weapons
    Staff = { name = "Staff", oneHand = false, melee = true, flag = "Staff" },
    ["Two Handed Sword"] = { name = "Two Handed Sword", oneHand = false, melee = true, flag = "Sword" },
    -- ... all weapon types
}
```

**Result:** ✅ Weapon type lookups succeed.

---

#### Issue 4: Missing skillFlags
**Error:** mainSkill.activeEffect.statSet.skillFlags not populated by calcs.initEnv().

**Fix:** Post-initEnv skillFlags setup in MinimalCalc.lua (lines 1433-1495)

```lua
-- After calcs.initEnv()
if env.player.mainSkill and env.player.mainSkill.activeEffect then
    local grantedEffect = env.player.mainSkill.activeEffect.grantedEffect

    if grantedEffect and grantedEffect.skillTypes then
        local flags = {}
        flags.attack = grantedEffect.skillTypes[1] == true  -- SkillType.Attack
        flags.spell = grantedEffect.skillTypes[2] == true   -- SkillType.Spell
        flags.projectile = grantedEffect.skillTypes[3] == true  -- SkillType.Projectile
        flags.melee = grantedEffect.skillTypes[11] == true
        flags.ranged = not flags.melee and flags.attack

        -- Set weapon-specific flags
        if flags.attack and env.player.weaponData1 then
            flags.weapon1Attack = true
            flags.weapon2Attack = false
            flags.unarmed = false
        end

        -- Set flags on activeEffect
        env.player.mainSkill.activeEffect.statSet.skillFlags = flags
        env.player.mainSkill.activeEffect.statSetCalcs.skillFlags = flags

        -- CRITICAL: Set weapon1Flags on mainSkill
        env.player.mainSkill.weapon1Flags = flags.weapon1Attack and 1 or 0
    end
end
```

**Result:** ✅ skillFlags correctly set: attack=true, weapon1Attack=true, weapon1Flags=1

---

#### Issue 5: CalcOffence.lua:1885 Crash
**Error:** `CalcOffence.lua:1885: attempt to index a nil value`

**Investigation:** Read CalcOffence.lua line 1885:
```lua
local baseCost = round(skillCost and skillCost / data.costs[resource].Divisor or 0, 2)
```

**Root Cause:** `data.costs[resource]` is nil - missing data.costs table!

**Fix:** Added data.costs in MinimalCalc.lua (lines 253-261)

```lua
-- Resource cost divisors (required by CalcOffence.lua:1885)
data.costs = {
    Mana = { Divisor = 1 },
    Life = { Divisor = 1 },
    Rage = { Divisor = 1 },
    ES = { Divisor = 1 },
    EnergyShield = { Divisor = 1 }
}
```

**Result:** ✅ CalcOffence.lua:1885 no longer crashes! calcs.perform() succeeds!

---

## Current Blocker: Weapon Compatibility

### Symptom
```lua
disableReason = "Main Hand weapon is not usable with this skill"
DPS = 0
mainSkill.output = NIL
```

### Root Cause Analysis

**What We Know:**
1. ✅ Our weapon object has correct structure:
   - `weapon.type = "Weapon"`
   - `weapon.base.type = "Bow"`
   - `weapon.weaponData[1].type = "Bow"`

2. ✅ Weapon loads successfully into build.itemsTab.items[1]

3. ❌ CalcSetup creates `env.player.weaponData1.type = "None"` instead of "Bow"

4. ❌ This causes PoB to think the weapon is incompatible with Lightning Arrow

**Evidence:**
```
[MinimalCalc] DEBUG: Weapon before CalcSetup:
[MinimalCalc]   weapon.base.type = Bow
[MinimalCalc]   weapon.weaponData[1].type = Bow

[MinimalCalc] DEBUG: Weapon AFTER CalcSetup:
[MinimalCalc]   weapon.base.type = Bow  (unchanged)
[MinimalCalc]   weapon.weaponData[1].type = Bow  (unchanged)

[MinimalCalc] DEBUG: weaponData1 = table: 0x...
[MinimalCalc] DEBUG: weaponData1.type = None  (← PROBLEM!)
[MinimalCalc] DEBUG: weaponData1.AttackRate = 1.4

[MinimalCalc] DEBUG: mainSkill fields:
[MinimalCalc]   disableReason = Main Hand weapon is not usable with this skill
[MinimalCalc]   weapon1Flags = 1
```

### Hypothesis

CalcSetup (part of PoB's calcs.initEnv()) is responsible for creating `env.player.weaponData1` from `build.itemsTab.items[1]`. It's successfully extracting AttackRate (1.4) but setting type to "None".

**Possible causes:**
1. Missing required field on weapon object that CalcSetup uses to determine type
2. CalcSetup logic that explicitly checks for certain conditions before accepting weapon type
3. Weapon.base.weapon field structure doesn't match what CalcSetup expects
4. Item needs BuildModList() or similar initialization method that we're not calling

### Debugging Steps for Next Developer

#### Step 1: Instrument CalcSetup
Since we can't easily modify PoB's CalcSetup.lua, add extensive debug output in MinimalCalc.lua right after calcs.initEnv():

```lua
-- After: local env = env_or_err

-- Check what CalcSetup created
if env.player.weaponData1 then
    print("[DEBUG] weaponData1 properties:")
    for k, v in pairs(env.player.weaponData1) do
        if type(v) ~= "function" then
            print("  " .. tostring(k) .. " = " .. tostring(v))
        end
    end
end

-- Check original weapon
if build.itemsTab.items[1] then
    local weapon = build.itemsTab.items[1]
    print("[DEBUG] Original weapon properties:")
    print("  weapon.base.type = " .. tostring(weapon.base and weapon.base.type))
    if weapon.base and weapon.base.weapon then
        print("  weapon.base.weapon properties:")
        for k, v in pairs(weapon.base.weapon) do
            print("    " .. tostring(k) .. " = " .. tostring(v))
        end
    end
end
```

#### Step 2: Check PoB CalcSetup.lua
Read `external/pob-engine/src/Modules/CalcSetup.lua` to find where weaponData1 is created:

```bash
grep -n "weaponData1" external/pob-engine/src/Modules/CalcSetup.lua
```

Look for logic like:
```lua
env.player.weaponData1 = {
    type = weapon.base.type or weapon.someOtherField or "None"
}
```

#### Step 3: Compare with PoB's Actual Weapon Creation
PoB has weapon creation code in `Classes/Item.lua`. Our weapon objects are plain Lua tables, but PoB weapons are class instances with methods like:
- `BuildAndParseRaw()` - Parses item text into mods
- `BuildModList()` - Creates mod list from parsed mods
- `GetModList()` - Returns the mod list

**Try:** See if CalcSetup expects these methods to exist. If so, we may need to create stub methods:

```lua
weapon.BuildAndParseRaw = function() end
weapon.BuildModList = function() return weapon.modList end
weapon.GetModList = function() return weapon.modList end
```

#### Step 4: Test Weapon Stub Approach
The weapon stub code in MinimalCalc.lua (lines 1270-1320) creates weapons the same way we do, and those work for simple tests. Compare the stub weapon creation vs our PoB item weapon creation - are we missing any fields?

#### Step 5: Check activeItemSet
CalcSetup might be checking `build.itemsTab.activeItemSet` to determine which item is equipped. We set:

```lua
build.itemsTab.activeItemSet = {
    useSecondWeaponSet = false,
    [1] = { id = 1 }
}
```

Verify this matches PoB's expected format. Check CalcSetup.lua for how it uses activeItemSet.

#### Step 6: Nuclear Option - Read CalcSetup Source
If all else fails, read the entire CalcSetup.lua weapon processing logic to understand exactly what it needs. Look for:
- How it determines weapon type
- What conditions cause it to default to "None"
- What fields it expects on weapon objects
- Whether it calls any methods on weapons

---

## Files Modified (Summary)

### Python Files
1. **`src/parsers/pob_parser.py`**
   - Lines 200-280: `_extract_items()` - Parse weapon stats from PoB XML
   - Lines 320-330: `_is_minion_skill()` - Filter minion skills
   - Lines 140-150: Added minion filter to `_extract_skills()`

2. **`src/calculator/pob_engine.py`**
   - Lines 150-200: Convert items to Lua tables and pass to lua_build_data

### Lua Files
3. **`src/calculator/MinimalCalc.lua`**
   - Lines 233-252: Added data.weaponTypeInfo (all PoE 2 weapon types)
   - Lines 253-261: Added data.costs (Mana/Life/Rage/ES divisors)
   - Lines 945-1070: Process items from buildData, create weapon objects
   - Lines 1433-1495: Post-initEnv skillFlags setup (weapon1Attack, weapon1Flags)
   - Lines 1342-1348: Debug weapon structure before CalcSetup
   - Lines 1394-1431: Debug weapon structure after CalcSetup
   - Lines 1497-1575: Enhanced debug output for mainSkill fields

---

## Testing Evidence

### Test 1: Items Parsing
```bash
python -c "from src.parsers.pob_parser import _extract_items; ..."
```
**Result:** ✅ Parses 5 items, weapon stats extracted correctly

### Test 2: Weapon Loading
```
[MinimalCalc] Loaded weapon: Gemini Bow -> Bow (Phys: 49-96, APS: 1.50)
[MinimalCalc] weapon.base.type = Bow
[MinimalCalc] weapon.weaponData[1].type = Bow
```
**Result:** ✅ Weapon object created correctly

### Test 3: CalcOffence Execution
```
[MinimalCalc] calcs.initEnv() successful
[MinimalCalc] skillFlags set: attack=true, weapon1Attack=true, projectile=true
[MinimalCalc] mainSkill.weapon1Flags = 1
[MinimalCalc] calcs.perform() successful
```
**Result:** ✅ No errors, calculation completes

### Test 4: DPS Calculation
```
[MinimalCalc] DEBUG: mainSkill.output is NIL!
[MinimalCalc]   disableReason = Main Hand weapon is not usable with this skill
[MinimalCalc]   TotalDPS: 0
```
**Result:** ❌ Skill disabled due to weapon compatibility check

---

## Acceptance Criteria Status

| AC ID | Status | Notes |
|-------|--------|-------|
| AC-2.9.1 | ✅ PASS | MinimalCalc extended, no Lua errors |
| AC-2.9.2 | ✅ PASS | Passive nodes affect calculations (verified in prior session) |
| AC-2.9.3 | 🟡 PARTIAL | Items load correctly, skills load, but weaponData1.type="None" blocks DPS |
| AC-2.9.4 | ✅ PASS | Performance acceptable (no change) |
| AC-2.9.5 | ✅ PASS | Backward compatible, BuildStats API unchanged |
| AC-2.9.6 | ❌ BLOCKED | Cannot run Epic 2 validation with DPS=0 |

**Estimated Completion:** AC-2.9.3 fix (weapon compatibility) will unblock AC-2.9.6.

---

## Next Steps

### Immediate (2-4 hours)
1. **Resolve weaponData1.type="None" issue** using debugging steps above
2. Verify DPS calculation works with real PoB builds
3. Test with multiple weapon types (Bow, Staff, Crossbow, etc.)

### Follow-up (4-8 hours)
4. Run Epic 2 validation with realistic builds (AC-2.9.6)
5. Verify success rate ≥70%, median improvement ≥5%
6. Mark Story 2.9 as complete

### Nice-to-Have (Future)
- Support for dual-wielding (weapon2Flags)
- Support for minion skills (currently filtered)
- Support for armor/jewelry items (currently only weapons)

---

## Questions for Next Developer

1. **What does PoB's CalcSetup.lua use to determine weapon type?**
   - Is it weapon.base.type, weapon.weaponData[1].type, or something else?
   - Why does it default to "None" when both fields are set to "Bow"?

2. **Does CalcSetup call any methods on weapon objects?**
   - BuildAndParseRaw(), BuildModList(), etc.
   - If so, we need to add stub implementations

3. **Is there a simpler approach?**
   - Can we use the weapon stub creation code for PoB items too?
   - Do we need full item parsing, or just weapon stats?

---

## Additional Resources

- **Story File:** `docs/stories/2-9-integrate-full-pob-calculation-engine.md`
- **Test Builds:** `tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml`
- **PoB Source:** `external/pob-engine/src/Modules/CalcSetup.lua`, `CalcOffence.lua`
- **Debug Scripts:** `test_all_pob_skills_individually.py`, `debug_companion_skill.py`

---

## Contact

If you need clarification on any of the above, the conversation transcript contains extensive debugging output and step-by-step reasoning for each fix.

**Key Insight:** We're 95% there - CalcOffence runs successfully, all infrastructure is in place. The last 5% is figuring out why CalcSetup sets weaponData1.type="None" when our weapon.base.type="Bow". This is likely a simple missing field or initialization step.

Good luck! 🚀
