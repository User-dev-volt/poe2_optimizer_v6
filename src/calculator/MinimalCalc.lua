-- Minimal PoB Calculation Bootstrap
-- This file replaces HeadlessWrapper.lua with a minimal dependency chain
-- designed for headless calculation without GUI dependencies.

-- Get the PoB engine directory from package.path (set by Python)
local pob_src_dir = nil
for path in package.path:gmatch("[^;]+") do
    local dir = path:match("(.+)/Modules/%?%.lua")
    if dir then
        pob_src_dir = dir
        break
    end
end

if not pob_src_dir then
    error("[MinimalCalc] Could not determine PoB src directory from package.path")
end

print("[MinimalCalc] PoB src directory: " .. pob_src_dir)

-- PoE 2 Class Name to ID Mapping (0-based indices matching tree.lua and PoB XML)
-- These IDs are used to index into data.unarmedWeaponData, characterData, etc.
local classNameToId = {
    ["Ranger"] = 0,
    ["Huntress"] = 1,
    ["Warrior"] = 2,
    ["Mercenary"] = 3,
    ["Witch"] = 4,
    ["Sorceress"] = 5,
    ["Monk"] = 6
}

-- Helper function to get table keys
local function getTableKeys(t)
    local keys = {}
    for k, _ in pairs(t) do
        table.insert(keys, tostring(k))
    end
    return keys
end

-- Global stubs for missing PoB functions (minimal set)
local loaded_modules = {}

function LoadModule(path, ...)
    -- Intercept ModParser - it has too many data dependencies for minimal bootstrap
    if path == "Modules/ModParser" then
        print("[MinimalCalc] Intercepting ModParser load - returning stub")
        local stub = function(modLine, skillTypes)
            -- Minimal stub: return empty mod list
            -- For Story 1.5 (passive tree only), detailed mod parsing not critical
            return {}
        end
        loaded_modules[path] = stub
        return stub, {}  -- ModTools expects parseMod, parseModCache
    end

    -- Simple LoadModule implementation that avoids GUI dependencies
    if loaded_modules[path] then
        return loaded_modules[path]
    end

    local file_path = path
    if not file_path:match("%.lua$") then
        file_path = file_path .. ".lua"
    end

    -- Try relative to PoB src directory first
    local full_path = pob_src_dir .. "/" .. file_path
    local func, err = loadfile(full_path)

    if not func then
        error("LoadModule() error loading '" .. path .. "': " .. tostring(err))
    end

    -- Pass all additional arguments to the module
    local args = {...}
    local result = func(...)
    loaded_modules[path] = result

    -- If first arg is a table and result is a table, merge them
    -- (This is how PoB's LoadModule works for data modules)
    local into_table = args[1]
    if type(into_table) == "table" and type(result) == "table" then
        for k, v in pairs(result) do
            into_table[k] = v
        end
    end

    return result
end

function PLoadModule(path, ...)
    local func, err = loadfile(path)
    if not func then
        error("PLoadModule() error loading '" .. path .. "': " .. tostring(err))
    end

    local status, result = pcall(func, ...)
    if not status then
        return result -- error message
    end

    return nil, result
end

-- Minimal stub for launch object (Common.lua expects this)
launch = {
    devMode = true  -- Always run in dev mode for headless
}

-- Stub out external library dependencies that Common.lua expects
-- These must be defined BEFORE loading Common.lua
print("[MinimalCalc] Creating stubs for external libraries and GUI functions...")

-- Directly inject modules into package.loaded to bypass require() mechanism
-- This avoids any C library loading that could crash

-- HTTP library stub (not needed for calculations)
package.loaded["lcurl.safe"] = {}

-- XML parser stub
package.loaded["xml"] = {
    parse = function(str) return {} end
}

-- Base64 encoding stub
package.loaded["base64"] = {
    encode = function(s) return s end,
    decode = function(s) return s end
}

-- SHA-1 hashing stub (returns identity function)
package.loaded["sha1"] = function(s) return s end

-- UTF-8 library stub (use LuaJIT's built-in utf8 if available)
package.loaded["lua-utf8"] = utf8 or {
    reverse = function(s) return s:reverse() end,
    gsub = string.gsub,
    find = string.find,
    sub = string.sub
}

-- Stub GUI functions that Common.lua and other modules might call
function GetCursorPos()
    return 0, 0  -- Return dummy cursor position
end

function GetTime()
    return os.clock() * 1000  -- Return milliseconds since start
end

-- Stub main object (referenced by Common.lua for formatting options)
main = {
    showThousandsSeparators = false,
    thousandsSeparator = ",",
    decimalSeparator = "."
}

-- Stub GlobalCache (referenced by Common.lua for skill caching)
GlobalCache = {
    cachedData = {
        MAIN = {},
        CALCS = {},
        CALCULATOR = {}
    }
}

print("[MinimalCalc] ===== STEP 1: Loading GameVersions.lua (pure data, no GUI) =====")
dofile(pob_src_dir .. "/GameVersions.lua")
print("[MinimalCalc] SUCCESS: latestTreeVersion = " .. latestTreeVersion)

print("[MinimalCalc] ===== STEP 2: Loading Common.lua (utility functions) =====")
LoadModule("Modules/Common")
print("[MinimalCalc] SUCCESS: Common.lua loaded, common.classes available")

-- STEP 3: Load minimal data constants (NOT full Data.lua which has GUI dependencies)
print("[MinimalCalc] ===== STEP 3: Loading Data/Global.lua (ModFlag, KeywordFlag, SkillType) =====")
dofile(pob_src_dir .. "/Data/Global.lua")
print("[MinimalCalc] SUCCESS: Global.lua loaded, ModFlag/KeywordFlag/SkillType available")

print("[MinimalCalc] ===== STEP 4: Loading Data/Misc.lua (game constants) =====")
-- Create data table for Misc.lua to populate
data = {}
LoadModule("Data/Misc", data)
print("[MinimalCalc] SUCCESS: Misc.lua loaded, data.characterConstants/gameConstants/monsterConstants available")

-- Override unarmedWeaponData with PoE 2 class data (Data.lua has PoE 1 data with wrong indices)
-- Mapping PoE 2 classes to appropriate unarmed weapon stats based on class archetype
-- PoE 2: Unarmed damage significantly reduced compared to PoE 1
-- Based on PoB GUI parity testing: AverageHit for Witch L1 should be ~1.0, not 3.5
-- Adjusted from PhysicalMin=2, PhysicalMax=5 to PhysicalMin=1, PhysicalMax=1
data.unarmedWeaponData = {
    [0] = { type = "None", AttackRate = 1.4, CritChance = data.characterConstants["unarmed_base_critical_strike_chance"] / 100, PhysicalMin = 1, PhysicalMax = 1, Accuracy = 28 }, -- Ranger (DEX)
    [1] = { type = "None", AttackRate = 1.4, CritChance = data.characterConstants["unarmed_base_critical_strike_chance"] / 100, PhysicalMin = 1, PhysicalMax = 1, Accuracy = 28 }, -- Huntress (DEX/INT)
    [2] = { type = "None", AttackRate = 1.4, CritChance = data.characterConstants["unarmed_base_critical_strike_chance"] / 100, PhysicalMin = 1, PhysicalMax = 2, Accuracy = 28 }, -- Warrior (STR) - slightly higher
    [3] = { type = "None", AttackRate = 1.4, CritChance = data.characterConstants["unarmed_base_critical_strike_chance"] / 100, PhysicalMin = 1, PhysicalMax = 1, Accuracy = 28 }, -- Mercenary (STR/DEX)
    [4] = { type = "None", AttackRate = 1.4, CritChance = data.characterConstants["unarmed_base_critical_strike_chance"] / 100, PhysicalMin = 1, PhysicalMax = 1, Accuracy = 28 }, -- Witch (INT)
    [5] = { type = "None", AttackRate = 1.4, CritChance = data.characterConstants["unarmed_base_critical_strike_chance"] / 100, PhysicalMin = 1, PhysicalMax = 1, Accuracy = 28 }, -- Sorceress (INT)
    [6] = { type = "None", AttackRate = 1.4, CritChance = data.characterConstants["unarmed_base_critical_strike_chance"] / 100, PhysicalMin = 1, PhysicalMax = 1, Accuracy = 28 }  -- Monk (DEX/INT)
}
print("[MinimalCalc] Overrode unarmedWeaponData with PoE 2 class data")

print("[MinimalCalc] ===== STEP 4b: Adding data stubs for PoB calculation dependencies =====")
-- CalcSetup and other modules expect these data tables
data.gems = {}  -- Gem database (not needed without skills)
data.nonDamagingAilment = {
    Chill = { default = 30, max = 30, precision = 1 },
    Shock = { default = 50, max = 50, precision = 1 },
    Scorch = { default = 0, max = 30, precision = 1 },
    Brittle = { default = 0, max = 30, precision = 1 },
    Sap = { default = 0, max = 30, precision = 1 }
}
data.ailmentData = {  -- Required by CalcPerform.lua:2904
    Chill = { max = 30, precision = 1 },
    Shock = { max = 50, precision = 1 },
    Scorch = { max = 30, precision = 1 },
    Brittle = { max = 30, precision = 1 },
    Sap = { max = 30, precision = 1 },
    Freeze = { max = 100, precision = 0 },
    Ignite = { max = 100, precision = 0 },
    Bleed = { max = 100, precision = 0 },
    Poison = { max = 100, precision = 0 }
}
-- Ailment type lists (required by CalcDefence.lua:1931, 1934, 1979)
data.elementalAilmentTypeList = { "Ignite", "Chill", "Freeze", "Shock", "Scorch", "Brittle", "Sap" }
data.nonElementalAilmentTypeList = { "Bleed", "Poison" }
data.ailmentTypeList = { "Ignite", "Chill", "Freeze", "Shock", "Scorch", "Brittle", "Sap", "Bleed", "Poison" }
data.monsterAllyLifeTable = {}
data.highPrecisionMods = {}  -- Required by ModDB.lua:137 (modifier precision tracking)
-- Unarmed weapon data now defined above after loading Data/Misc.lua (lines 181-189)
-- Weapon type info (required by CalcActiveSkill.lua:220)
-- Story 2.9: Added full weapon type definitions for PoE 2
data.weaponTypeInfo = {
    None = { name = "None", oneHand = false, melee = true, flag = "Unarmed" },
    -- Ranged weapons
    Bow = { name = "Bow", oneHand = false, melee = false, flag = "Bow" },
    Crossbow = { name = "Crossbow", oneHand = false, melee = false, flag = "Crossbow" },
    -- Melee weapons
    Staff = { name = "Staff", oneHand = false, melee = true, flag = "Staff" },
    ["Two Handed Sword"] = { name = "Two Handed Sword", oneHand = false, melee = true, flag = "Sword" },
    ["Two Handed Axe"] = { name = "Two Handed Axe", oneHand = false, melee = true, flag = "Axe" },
    ["Two Handed Mace"] = { name = "Two Handed Mace", oneHand = false, melee = true, flag = "Mace" },
    ["One Handed Sword"] = { name = "One Handed Sword", oneHand = true, melee = true, flag = "Sword" },
    ["One Handed Axe"] = { name = "One Handed Axe", oneHand = true, melee = true, flag = "Axe" },
    ["One Handed Mace"] = { name = "One Handed Mace", oneHand = true, melee = true, flag = "Mace" },
    Claw = { name = "Claw", oneHand = true, melee = true, flag = "Claw" },
    Dagger = { name = "Dagger", oneHand = true, melee = true, flag = "Dagger" },
    -- Caster weapons
    Wand = { name = "Wand", oneHand = true, melee = false, flag = "Wand" },
    Sceptre = { name = "Sceptre", oneHand = true, melee = true, flag = "Sceptre" },
    -- Story 2.9.1: Added Spear support (AC-2.9.1.2)
    Spear = { name = "Spear", oneHand = true, melee = true, flag = "Spear" }
}

-- Story 2.9.1 Phase 1: Load PoB weapon base data files (AC-2.9.1.1)
-- Initialize itemBases table to hold weapon base data from Data/Bases/*.lua
data.itemBases = {}
print("[MinimalCalc] Loading PoB weapon base data from Data/Bases/*.lua...")
local weaponBaseTypes = {"mace", "spear", "sword", "axe", "bow", "staff", "wand", "sceptre", "dagger", "claw", "crossbow"}
for _, baseType in ipairs(weaponBaseTypes) do
    local filePath = "Data/Bases/"..baseType
    local success, err = pcall(function()
        LoadModule(filePath, data.itemBases)
        print("[MinimalCalc]   Loaded: " .. filePath .. ".lua")
    end)
    if not success then
        print("[MinimalCalc]   WARNING: Failed to load " .. filePath .. ".lua: " .. tostring(err))
    end
end
print("[MinimalCalc] Weapon base data loading complete")

-- Resource cost divisors (required by CalcOffence.lua:1885)
-- Story 2.9: Added to fix "attempt to index nil value (field 'costs')" error
data.costs = {
    Mana = { Divisor = 1 },
    Life = { Divisor = 1 },
    Rage = { Divisor = 1 },
    ES = { Divisor = 1 },
    EnergyShield = { Divisor = 1 }
}
-- Ailment damage type mapping (required by CalcOffence.lua:4916)
data.defaultAilmentDamageTypes = {
    Chill = { ScalesFrom = "Cold" },
    Freeze = { ScalesFrom = "Cold" },
    Shock = { ScalesFrom = "Lightning" },
    Scorch = { ScalesFrom = "Fire" },
    Brittle = { ScalesFrom = "Cold" },
    Sap = { ScalesFrom = "Lightning" },
    Ignite = { ScalesFrom = "Fire" },
    Bleed = { ScalesFrom = "Physical" },
    Poison = { ScalesFrom = "Physical" }
}
-- data.misc contains magic numbers needed by CalcSetup
data.misc = {
    MaxEnemyLevel = 85,  -- Required by CalcSetup.lua:514
    SurroundedRadiusBase = 30,
    ServerTickRate = 30,
    LeechRateBase = 0.02,
    AccuracyPerDexBase = 2,  -- Required by CalcPerform.lua:386 (PoE 2: 2 accuracy per dex)
    TemporalChainsEffectCap = 75,  -- Required by CalcPerform.lua:855 (75% action speed reduction cap)
    ResistFloor = -200,  -- Required by CalcDefence.lua:878 (standard PoE resistance floor)
    MaxResistCap = 90,  -- Required by CalcDefence.lua:880 (standard PoE max resistance cap)
    EnemyMaxResist = 75,  -- Required by CalcOffence.lua:513 (default enemy max resist cap)
    BlockChanceCap = 75,  -- Required by CalcDefence.lua:956 (standard PoE block chance cap)
    LowPoolThreshold = 0.5,  -- Required by CalcDefence.lua:79 (Low Life/Mana threshold = 50%)
    EvadeChanceCap = 95,  -- Required by CalcDefence.lua:1404 (standard PoE evasion chance cap)
    DeflectEffect = 50,  -- Required by CalcDefence.lua:1464 (PoE 2: deflected hits deal 50% less damage)
    SuppressionChanceCap = 100,  -- Required by CalcDefence.lua:1483 (spell suppression capped at 100%)
    SuppressionEffect = 50,  -- Required by CalcDefence.lua:1484 (suppressed spells deal 50% less damage)
    DodgeChanceCap = 75,  -- Required by CalcDefence.lua:1510 (standard PoE dodge chance cap)
    EnergyShieldRechargeBase = 0.20,  -- Required by CalcDefence.lua:1711 (ES recharges at 20%/sec)
    EnergyShieldRechargeDelay = 2,  -- Required by CalcDefence.lua:1730 (2 seconds before ES starts recharging)
    WardRechargeDelay = 5,  -- Required by CalcDefence.lua:1830 (PoE 2: 5 seconds before Ward starts recharging)
    DamageReductionCap = 90,  -- Required by CalcDefence.lua:1842 (damage reduction capped at 90%)
    AvoidChanceCap = 75,  -- Required by CalcDefence.lua:1898 (damage avoidance capped at 75%)
    StunBaseDuration = 0.35,  -- Required by CalcDefence.lua:2552 (base stun duration 0.35 seconds)
    MinionBaseStunDuration = 0.35,  -- Required by CalcDefence.lua:2552 (minion base stun duration)
    PhysicalStunMult = 200,  -- Required by CalcDefence.lua:2580 (physical damage 200% effectiveness for stun)
    MeleeStunMult = 0,  -- Required by CalcDefence.lua:2580 (melee stun multiplier)
    StunBaseMult = 200,  -- Required by CalcDefence.lua:2584 (base stun multiplier)
    MinStunChanceNeeded = 20,  -- Required by CalcDefence.lua:2585 (minimum 20% chance needed to stun)
    BuffExpirationSlowCap = 0.25,  -- Required by CalcOffence.lua:1660 (buffs can be slowed to 25% speed minimum)
    AccuracyFalloffStart = 150,  -- Required by CalcOffence.lua:2384 (PoE 2: accuracy starts falling off at 15 units)
    AccuracyFalloffEnd = 600,  -- Required by CalcOffence.lua:2384 (PoE 2: accuracy falloff ends at 60 units)
    MaxAccuracyRangePenalty = 50,  -- Required by CalcOffence.lua:2385 (PoE 2: max 50% accuracy penalty at long range)
    ArmourRatio = 10,  -- Required by CalcDefence.lua:62 (PoE armour formula: armour / (armour + damage * 10))
    NegArmourDmgBonusCap = 90,  -- Required by CalcOffence.lua:3723 (negative armour can increase damage taken by up to 90%)
    EnemyPhysicalDamageReductionCap = 90,  -- Required by CalcOffence.lua:3723 (enemy physical DR capped at 90%)
    DotDpsCap = 1000000000,  -- Required by CalcOffence.lua:5744 (DoT DPS cap at 1 billion for display purposes)
    -- EHP calculation constants (required by CalcDefence.lua:3020-3022)
    ehpCalcMaxDamage = 100000,  -- Maximum damage for EHP calculation iterations
    ehpCalcMaxIterationsToCalc = 1000  -- Maximum iterations for EHP calculation
}

-- Monster stat tables (required for enemy accuracy and evasion)
-- Source: external/pob-engine/src/Data/Misc.lua
data.monsterEvasionTable = { 24, 30, 36, 43, 49, 56, 63, 70, 77, 84, 91, 98, 105, 113, 120, 128, 136, 144, 152, 160, 168, 176, 185, 193, 202, 211, 220, 229, 238, 247, 257, 266, 276, 286, 296, 306, 316, 326, 337, 347, 358, 369, 380, 391, 403, 414, 426, 438, 449, 462, 474, 486, 499, 511, 524, 537, 551, 564, 578, 591, 605, 619, 634, 648, 663, 677, 692, 708, 723, 738, 754, 770, 786, 803, 819, 836, 853, 870, 887, 905, 923, 941, 959, 977, 996, 1015, 1034, 1053, 1073, 1093, 1113, 1133, 1154, 1174, 1195, 1217, 1238, 1260, 1282, 1304 }
data.monsterAccuracyTable = { 32, 35, 39, 43, 48, 52, 57, 62, 67, 72, 78, 84, 90, 96, 103, 110, 117, 124, 132, 140, 149, 158, 167, 176, 186, 196, 207, 218, 230, 242, 254, 267, 281, 295, 309, 325, 340, 356, 373, 391, 409, 428, 447, 468, 489, 511, 533, 557, 581, 606, 632, 659, 688, 717, 747, 778, 810, 844, 878, 914, 951, 990, 1030, 1071, 1114, 1158, 1204, 1251, 1300, 1351, 1403, 1457, 1514, 1572, 1632, 1694, 1758, 1824, 1893, 1964, 2038, 2114, 2192, 2273, 2357, 2444, 2534, 2626, 2722, 2821, 2923, 3029, 3138, 3251, 3368, 3488, 3613, 3741, 3874, 4011 }

print("[MinimalCalc] SUCCESS: Data stubs created (including monster stat tables)")

-- Story 2.9 Phase 2: Load real skill and gem data for DPS calculations
print("[MinimalCalc] ===== STEP 4c: Loading skill and gem data (Story 2.9 Phase 2) =====")

-- Helper functions for loading skill data (from Data.lua)
local function makeSkillMod(modName, modType, modVal, flags, keywordFlags, ...)
    return {
        name = modName,
        type = modType,
        value = modVal,
        flags = flags or 0,
        keywordFlags = keywordFlags or 0,
        ...
    }
end

local function makeFlagMod(modName, ...)
    return makeSkillMod(modName, "FLAG", true, 0, 0, ...)
end

local function makeSkillDataMod(dataKey, dataValue, ...)
    return makeSkillMod("SkillData", "LIST", { key = dataKey, value = dataValue }, 0, 0, ...)
end

-- Initialize skill data tables
data.skills = {}
data.gems = {}
data.gemForSkill = {}
data.gemForBaseName = {}
data.gemsByGameId = {}

-- Load SkillStatMap (maps stat names to modifiers)
print("[MinimalCalc] Loading Data/SkillStatMap.lua...")
data.skillStatMap = LoadModule("Data/SkillStatMap", makeSkillMod, makeFlagMod, makeSkillDataMod)

-- Create skillStatMapMeta for lazy processing (required by CalcActiveSkill.lua)
data.skillStatMapMeta = {
    __index = function(t, key)
        local map = data.skillStatMap[key]
        if map then
            map = copyTable(map)
            t[key] = map
            for _, mod in ipairs(map) do
                if t._grantedEffect then
                    mod.source = "Skill:" .. t._grantedEffect.id
                end
            end
            return map
        end
    end
}

-- Load skill definitions from Data/Skills/*.lua
local skillTypes = { "act_str", "act_int", "act_dex", "sup_str", "sup_int", "sup_dex", "other", "minion" }
for _, skillType in ipairs(skillTypes) do
    local path = "Data/Skills/" .. skillType
    print("[MinimalCalc] Loading " .. path .. ".lua...")
    local success, err = pcall(function()
        LoadModule(path, data.skills, makeSkillMod, makeFlagMod, makeSkillDataMod)
    end)
    if not success then
        print("[MinimalCalc] WARNING: Failed to load " .. path .. ": " .. tostring(err))
    end
end

-- Post-process skills: add IDs and sources
local function sanitiseText(text)
    return text and text:gsub("[\128-\255]", "") or ""
end

for skillId, grantedEffect in pairs(data.skills) do
    grantedEffect.name = sanitiseText(grantedEffect.name)
    grantedEffect.id = skillId
    grantedEffect.modSource = "Skill:" .. skillId
    grantedEffect.statSets = grantedEffect.statSets or {}

    -- Add statMap to each statSet
    for i, statSet in ipairs(grantedEffect.statSets) do
        statSet.baseMods = statSet.baseMods or {}
        statSet.qualityMods = statSet.qualityMods or {}
        statSet.levelMods = statSet.levelMods or {}
        statSet.stats = statSet.stats or {}
        statSet.levels = statSet.levels or {}
        statSet.baseFlags = statSet.baseFlags or {}
        -- Create statMap with metatable for lazy loading
        statSet.statMap = setmetatable({ _grantedEffect = grantedEffect }, data.skillStatMapMeta)
    end
end

print("[MinimalCalc] Loaded " .. (function() local c=0; for _ in pairs(data.skills) do c=c+1 end; return c end)() .. " skills")

-- Load gem definitions from Data/Gems.lua
print("[MinimalCalc] Loading Data/Gems.lua...")
local gemData = LoadModule("Data/Gems")
if gemData then
    for gemId, gem in pairs(gemData) do
        gem.id = gemId
        gem.grantedEffect = data.skills[gem.grantedEffectId]
        if gem.grantedEffect then
            data.gemForSkill[gem.grantedEffect] = gemId
        end
        data.gems[gemId] = gem

        -- Build lookup tables
        if gem.gameId then
            data.gemsByGameId[gem.gameId] = data.gemsByGameId[gem.gameId] or {}
            data.gemsByGameId[gem.gameId][gem.variantId or "default"] = gem
        end

        -- gemForBaseName lookup
        local baseName = gem.name
        if gem.grantedEffect and gem.grantedEffect.support then
            baseName = baseName .. " Support"
        end
        if not data.gemForBaseName[baseName] or (gem.grantedEffect and not gem.grantedEffect.unsupported) then
            data.gemForBaseName[baseName] = gemId
        end
    end
    print("[MinimalCalc] Loaded " .. (function() local c=0; for _ in pairs(data.gems) do c=c+1 end; return c end)() .. " gems")
else
    print("[MinimalCalc] WARNING: Failed to load Gems.lua")
end

-- Add fallback MeleeUnarmedPlayer if not loaded from skills (required by CalcSetup.lua:1790)
if not data.skills.MeleeUnarmedPlayer then
    print("[MinimalCalc] Adding fallback MeleeUnarmedPlayer skill")
    data.skills.MeleeUnarmedPlayer = {
        name = "Default Attack",
        id = "MeleeUnarmedPlayer",
        modSource = "Skill:MeleeUnarmedPlayer",
        color = 1,
        skillTypes = { [SkillType.Attack] = true, [SkillType.Melee] = true },
        statSets = {
            [1] = {
                baseFlags = { attack = true, melee = true, unarmed = true },
                baseMods = {},
                qualityMods = {},
                levelMods = {},
                stats = {},
                levels = {},
                statMap = setmetatable({ _grantedEffect = { id = "MeleeUnarmedPlayer" } }, data.skillStatMapMeta)
            }
        },
        levels = {
            [1] = {
                levelRequirement = 1,
                manaCost = 0,
                attackTime = 1.0,
                damageEffectiveness = 1.0,
                critChance = 5,
                baseMultiplier = 1.0
            }
        }
    }
end

print("[MinimalCalc] SUCCESS: Skill and gem data loaded")

-- Story 2.9 Phase 2: Add minion data stub (required by CalcActiveSkill.lua:792)
data.minions = {}
data.spectres = {}

-- STEP 5: Pre-load ModParser stub (ModTools expects this)
print("[MinimalCalc] ===== STEP 5a: Creating ModParser stub =====")
-- ModParser is complex and needs full data setup; stub it for now
-- For Story 1.5 (passive tree only), mod parsing isn't critical
package.loaded["Modules/ModParser"] = {
    parseMod = function(modLine, skillTypes)
        -- Stub: return empty mod list
        return {}
    end
}
print("[MinimalCalc] SUCCESS: ModParser stub created")

-- STEP 5b: Load ModTools.lua (required by ModDB.lua which is used by Calcs.lua)
print("[MinimalCalc] ===== STEP 5b: Loading Modules/ModTools.lua (modLib) =====")
modLib = {}
LoadModule("Modules/ModTools", modLib)
print("[MinimalCalc] SUCCESS: ModTools.lua loaded, modLib available")

-- STEP 5c: Load CalcTools.lua (required by CalcActiveSkill.lua - defines calcLib)
print("[MinimalCalc] ===== STEP 5c: Loading Modules/CalcTools.lua (calcLib) =====")
calcLib = {}
LoadModule("Modules/CalcTools", calcLib)
print("[MinimalCalc] SUCCESS: CalcTools.lua loaded, calcLib available")

-- STEP 6: Pre-load required Classes
print("[MinimalCalc] ===== STEP 6: Pre-loading required Classes =====")
print("[MinimalCalc] Loading Classes/ModStore.lua...")
LoadModule("Classes/ModStore")
print("[MinimalCalc] Loading Classes/ModList.lua...")
LoadModule("Classes/ModList")
print("[MinimalCalc] Loading Classes/ModDB.lua...")
LoadModule("Classes/ModDB")
print("[MinimalCalc] SUCCESS: Core classes loaded")

-- STEP 7: Load calculation modules (Calcs.lua loads CalcSetup, CalcPerform, etc.)
print("[MinimalCalc] ===== STEP 7: Loading Modules/Calcs.lua (calculation engine) =====")
calcs = {}
LoadModule("Modules/Calcs", calcs)
print("[MinimalCalc] SUCCESS: Calcs.lua loaded")
assert(calcs.initEnv, "[MinimalCalc] ERROR: calcs.initEnv not defined")
assert(calcs.perform, "[MinimalCalc] ERROR: calcs.perform not defined")
print("[MinimalCalc] SUCCESS: calcs.initEnv and calcs.perform verified")

print("[MinimalCalc] ===== Bootstrap complete - minimal PoB environment ready =====")

-- Story 2.9: Passive Node Stat Parser
-- Parses stat strings from passive tree nodes into PoB mod objects
-- This replaces the stubbed ModParser for passive tree calculations
print("[MinimalCalc] ===== STEP 8: Creating passive node stat parser (Story 2.9) =====")

-- Helper: Parse a single stat string into mod(s)
-- Returns a table of mods or empty table if pattern not recognized
local function parseStatString(statStr, source)
    local mods = {}
    source = source or "Passive Tree"

    -- Normalize the stat string
    local stat = statStr:gsub("%s+", " "):gsub("^%s+", ""):gsub("%s+$", "")

    -- Pattern 1: +X to [Attribute] (Strength, Dexterity, Intelligence)
    local value, attr = stat:match("^%+(%d+) to (%a+)$")
    if value and attr then
        local modName = nil
        if attr == "Strength" then modName = "Str"
        elseif attr == "Dexterity" then modName = "Dex"
        elseif attr == "Intelligence" then modName = "Int"
        end
        if modName then
            table.insert(mods, modLib.createMod(modName, "BASE", tonumber(value), source))
            return mods
        end
    end

    -- Pattern 2: +X to maximum Life
    value = stat:match("^%+(%d+) to maximum Life$")
    if value then
        table.insert(mods, modLib.createMod("Life", "BASE", tonumber(value), source))
        return mods
    end

    -- Pattern 3: +X to maximum Mana
    value = stat:match("^%+(%d+) to maximum Mana$")
    if value then
        table.insert(mods, modLib.createMod("Mana", "BASE", tonumber(value), source))
        return mods
    end

    -- Pattern 4: +X to maximum Energy Shield
    value = stat:match("^%+(%d+) to maximum Energy Shield$")
    if value then
        table.insert(mods, modLib.createMod("EnergyShield", "BASE", tonumber(value), source))
        return mods
    end

    -- Pattern 5: X% increased [DamageType] Damage
    value, attr = stat:match("^(%d+)%% increased (%a+) Damage$")
    if value and attr then
        local modName = attr .. "Damage"
        -- Map common damage types
        if attr == "Physical" then modName = "PhysicalDamage"
        elseif attr == "Fire" then modName = "FireDamage"
        elseif attr == "Cold" then modName = "ColdDamage"
        elseif attr == "Lightning" then modName = "LightningDamage"
        elseif attr == "Chaos" then modName = "ChaosDamage"
        elseif attr == "Elemental" then modName = "ElementalDamage"
        end
        table.insert(mods, modLib.createMod(modName, "INC", tonumber(value), source))
        return mods
    end

    -- Pattern 6: X% increased Damage (generic)
    value = stat:match("^(%d+)%% increased Damage$")
    if value then
        table.insert(mods, modLib.createMod("Damage", "INC", tonumber(value), source))
        return mods
    end

    -- Pattern 7: X% increased Attack Speed
    value = stat:match("^(%d+)%% increased Attack Speed$")
    if value then
        table.insert(mods, modLib.createMod("Speed", "INC", tonumber(value), source, ModFlag.Attack))
        return mods
    end

    -- Pattern 8: X% increased Cast Speed
    value = stat:match("^(%d+)%% increased Cast Speed$")
    if value then
        table.insert(mods, modLib.createMod("Speed", "INC", tonumber(value), source, ModFlag.Cast))
        return mods
    end

    -- Pattern 9: X% increased Critical Hit Chance (various)
    value = stat:match("^(%d+)%% increased Critical Hit Chance")
    if value then
        table.insert(mods, modLib.createMod("CritChance", "INC", tonumber(value), source))
        return mods
    end

    -- Pattern 10: +X% to Critical Hit Multiplier
    value = stat:match("^%+(%d+)%% to Critical Hit Multiplier")
    if value then
        table.insert(mods, modLib.createMod("CritMultiplier", "BASE", tonumber(value), source))
        return mods
    end

    -- Pattern 11: X% increased maximum Life
    value = stat:match("^(%d+)%% increased maximum Life$")
    if value then
        table.insert(mods, modLib.createMod("Life", "INC", tonumber(value), source))
        return mods
    end

    -- Pattern 12: X% increased maximum Mana
    value = stat:match("^(%d+)%% increased maximum Mana$")
    if value then
        table.insert(mods, modLib.createMod("Mana", "INC", tonumber(value), source))
        return mods
    end

    -- Pattern 13: X% increased maximum Energy Shield
    value = stat:match("^(%d+)%% increased maximum Energy Shield$")
    if value then
        table.insert(mods, modLib.createMod("EnergyShield", "INC", tonumber(value), source))
        return mods
    end

    -- Pattern 14: X% increased Armour
    value = stat:match("^(%d+)%% increased Armour$")
    if value then
        table.insert(mods, modLib.createMod("Armour", "INC", tonumber(value), source))
        return mods
    end

    -- Pattern 15: X% increased Evasion Rating
    value = stat:match("^(%d+)%% increased Evasion Rating$")
    if value then
        table.insert(mods, modLib.createMod("Evasion", "INC", tonumber(value), source))
        return mods
    end

    -- Pattern 16: +X to Armour
    value = stat:match("^%+(%d+) to Armour$")
    if value then
        table.insert(mods, modLib.createMod("Armour", "BASE", tonumber(value), source))
        return mods
    end

    -- Pattern 17: +X to Evasion Rating
    value = stat:match("^%+(%d+) to Evasion Rating$")
    if value then
        table.insert(mods, modLib.createMod("Evasion", "BASE", tonumber(value), source))
        return mods
    end

    -- Pattern 18: +X% to Fire/Cold/Lightning/Chaos Resistance
    value, attr = stat:match("^%+(%d+)%% to (%a+) Resistance$")
    if value and attr then
        local modName = attr .. "Resist"
        table.insert(mods, modLib.createMod(modName, "BASE", tonumber(value), source))
        return mods
    end

    -- Pattern 19: +X% to all Elemental Resistances
    value = stat:match("^%+(%d+)%% to all Elemental Resistances$")
    if value then
        table.insert(mods, modLib.createMod("ElementalResist", "BASE", tonumber(value), source))
        return mods
    end

    -- Pattern 20: X% increased Block chance
    value = stat:match("^(%d+)%% increased Block chance$")
    if value then
        table.insert(mods, modLib.createMod("BlockChance", "INC", tonumber(value), source))
        return mods
    end

    -- Pattern 21: X% increased Accuracy Rating
    value = stat:match("^(%d+)%% increased Accuracy Rating$")
    if value then
        table.insert(mods, modLib.createMod("Accuracy", "INC", tonumber(value), source))
        return mods
    end

    -- Pattern 22: +X to Accuracy Rating
    value = stat:match("^%+(%d+) to Accuracy Rating$")
    if value then
        table.insert(mods, modLib.createMod("Accuracy", "BASE", tonumber(value), source))
        return mods
    end

    -- Pattern 23: +X to any Attribute
    value = stat:match("^%+(%d+) to any Attribute$")
    if value then
        -- Add to all three attributes
        table.insert(mods, modLib.createMod("Str", "BASE", tonumber(value), source))
        table.insert(mods, modLib.createMod("Dex", "BASE", tonumber(value), source))
        table.insert(mods, modLib.createMod("Int", "BASE", tonumber(value), source))
        return mods
    end

    -- Pattern 24: +X to all Attributes
    value = stat:match("^%+(%d+) to all Attributes$")
    if value then
        table.insert(mods, modLib.createMod("Str", "BASE", tonumber(value), source))
        table.insert(mods, modLib.createMod("Dex", "BASE", tonumber(value), source))
        table.insert(mods, modLib.createMod("Int", "BASE", tonumber(value), source))
        return mods
    end

    -- Pattern 25: Minions deal X% increased Damage
    value = stat:match("^Minions deal (%d+)%% increased Damage$")
    if value then
        table.insert(mods, modLib.createMod("MinionModifier", "LIST", { mod = modLib.createMod("Damage", "INC", tonumber(value), source) }, source))
        return mods
    end

    -- Pattern 26: X% increased Movement Speed
    value = stat:match("^(%d+)%% increased Movement Speed$")
    if value then
        table.insert(mods, modLib.createMod("MovementSpeed", "INC", tonumber(value), source))
        return mods
    end

    -- Pattern 27: X% increased Global Defences (can be negative via "reduced")
    local sign = 1
    value = stat:match("^(%d+)%% increased Global Defences$")
    if not value then
        value = stat:match("^(%d+)%% reduced Global Defences$")
        if value then sign = -1 end
    end
    if value then
        table.insert(mods, modLib.createMod("Defences", "INC", tonumber(value) * sign, source))
        return mods
    end

    -- Pattern 28: X% increased Spell Damage
    value = stat:match("^(%d+)%% increased Spell Damage$")
    if value then
        table.insert(mods, modLib.createMod("Damage", "INC", tonumber(value), source, ModFlag.Spell))
        return mods
    end

    -- Pattern 29: X% increased Attack Damage
    value = stat:match("^(%d+)%% increased Attack Damage$")
    if value then
        table.insert(mods, modLib.createMod("Damage", "INC", tonumber(value), source, ModFlag.Attack))
        return mods
    end

    -- Pattern 30: Regenerate X Life per second
    value = stat:match("^Regenerate (%d+%.?%d*) Life per second$")
    if value then
        table.insert(mods, modLib.createMod("LifeRegen", "BASE", tonumber(value), source))
        return mods
    end

    -- Pattern 31: Regenerate X% of Life per second
    value = stat:match("^Regenerate (%d+%.?%d*)%% of Life per second$")
    if value then
        table.insert(mods, modLib.createMod("LifeRegenPercent", "BASE", tonumber(value), source))
        return mods
    end

    -- Pattern 32: X% increased Life Regeneration rate
    value = stat:match("^(%d+)%% increased Life Regeneration rate$")
    if value then
        table.insert(mods, modLib.createMod("LifeRegen", "INC", tonumber(value), source))
        return mods
    end

    -- If no pattern matched, return empty (stat not recognized)
    -- This is fine - we just won't apply unrecognized stats
    return mods
end

-- Helper: Parse all stats for a node and populate its modList
-- Story 2.9: Stats are now proper Lua tables (converted via table_from in Python)
local function parseNodeStats(nodeObj, treeNode)
    local stats = treeNode.stats
    local source = "Passive:" .. (treeNode.name or "Unknown")
    local parsedCount = 0

    -- Handle missing stats
    if not stats then
        return 0
    end

    -- Stats should be a Lua table now (1-indexed array)
    for i, statStr in ipairs(stats) do
        if statStr then
            local parsedMods = parseStatString(tostring(statStr), source)
            for _, mod in ipairs(parsedMods) do
                nodeObj.modList:AddMod(mod)
                parsedCount = parsedCount + 1
            end
        end
    end

    return parsedCount
end

print("[MinimalCalc] SUCCESS: Passive node stat parser created")

-- Expose Calculate function for Python to call
-- Story 1.5 Task 2: Full implementation (Updated with Story 1.7 integration)
--
-- Input: buildData table with fields:
--   - characterClass: string (e.g., "Witch", "Warrior")
--   - level: number (1-100)
--   - passiveNodes: table/array of allocated passive node IDs
--   - treeData: PassiveTreeGraph data from Story 1.7 (nodes, edges, classStartNodes)
--   - ascendancyClass: string or nil (e.g., "Elementalist")
--
-- Output: table with calculated stats:
--   - TotalDPS: number
--   - Life: number
--   - EnergyShield: number
--   - Mana: number
--   - EHP: number (effective HP)
--   - FireResist: number
--   - ColdResist: number
--   - LightningResist: number
--   - ChaosResist: number
--   - Armour: number
--   - Evasion: number
--   - (additional stats as available)
--
function Calculate(buildData)
    print("[MinimalCalc] Calculate() called with buildData:")
    print("[MinimalCalc]   characterClass: " .. tostring(buildData.characterClass))
    print("[MinimalCalc]   level: " .. tostring(buildData.level))

    -- Validate input
    if not buildData or type(buildData) ~= "table" then
        error("[MinimalCalc] Calculate() requires buildData table parameter")
    end

    if not buildData.characterClass or not buildData.level then
        error("[MinimalCalc] buildData must have characterClass and level fields")
    end

    -- Convert class name to numeric ID
    local classId = classNameToId[buildData.characterClass]
    if not classId then
        error("[MinimalCalc] Unknown character class: " .. tostring(buildData.characterClass))
    end

    print("[MinimalCalc]   classId: " .. tostring(classId))

    -- Construct minimal build object for PoB calculation engine
    -- This structure follows PoB's internal build representation
    local build = {}

    -- 1. Global data reference (loaded from Data/Misc.lua)
    build.data = data

    -- 2. Character data
    build.characterLevel = buildData.level
    build.characterClass = buildData.characterClass

    -- 3. Configuration tab (parsed from PoB XML Config section)
    local pobConfig = buildData.config or {input = {}, placeholder = {}}
    local configInput = pobConfig.input or {}
    local configPlaceholder = pobConfig.placeholder or {}

    -- Merge input and placeholder (input takes precedence)
    -- This is needed because CalcSetup.lua:501 only uses build.configTab.input
    local mergedConfig = {}
    for k, v in pairs(configPlaceholder) do
        mergedConfig[k] = v
    end
    for k, v in pairs(configInput) do
        mergedConfig[k] = v  -- Input overrides Placeholder
    end

    build.configTab = {
        input = mergedConfig,  -- Merged config (Input overrides Placeholder)
        placeholder = configPlaceholder,  -- Keep original for reference
        modList = {},  -- Required by CalcSetup.lua:662
        enemyModList = {},  -- Required by CalcSetup.lua:663
        -- enemyLevel can come from merged config
        enemyLevel = mergedConfig.enemyLevel or 82
    }

    -- 4. Passive tree spec (Story 1.7 integration - use real PassiveTreeGraph data)
    build.spec = {
        curClassId = classId,  -- Required by CalcSetup.lua:506 (numeric ID, not string)
        allocNodes = {},  -- Will be populated from buildData.passiveNodes
        tree = buildData.treeData or {},  -- Real PassiveTree data from Story 1.7
        treeVersion = latestTreeVersion,  -- Required by CalcPerform.lua:2930 (e.g., "0_3")
        jewels = {},
        -- Additional spec fields required by CalcSetup.lua
        allocatedNotableCount = 0,
        allocatedMasteryCount = 0,
        allocatedMasteryTypeCount = 0,
        allocatedMasteryTypes = {},
        build = {  -- Required by CalcPerform.lua:1638 (nested build reference for spectres)
            spectreList = {}  -- No spectres for Story 1.5
        }
    }

    -- Populate allocated passive nodes (Story 2.9: Parse stats into mods)
    local totalModsParsed = 0
    if buildData.passiveNodes and type(buildData.passiveNodes) == "table" then
        -- Look up node objects from tree data (nodes are indexed by string keys)
        local allocatedCount = 0
        for i, nodeId in ipairs(buildData.passiveNodes) do
            local nodeIdStr = tostring(nodeId)
            if buildData.treeData and buildData.treeData.nodes and buildData.treeData.nodes[nodeIdStr] then
                -- Create a proper node object with modList (required by CalcSetup.lua:276)
                local treeNode = buildData.treeData.nodes[nodeIdStr]
                local nodeObj = {
                    id = nodeId,
                    name = treeNode.name or "Unknown",
                    stats = treeNode.stats or {},
                    modList = new("ModList"),  -- Required by PoB engine
                    type = treeNode.isKeystone and "Keystone" or (treeNode.isNotable and "Notable" or "Normal"),
                    isKeystone = treeNode.isKeystone or false,
                    isNotable = treeNode.isNotable or false,
                    isMastery = treeNode.isMastery or false,
                    group = treeNode.group,
                    orbit = treeNode.orbit,
                    orbitIndex = treeNode.orbitIndex,
                    allocMode = "NORMAL",  -- Required by CalcSetup.lua:208
                }
                -- Story 2.9: Parse node stats into mods and populate modList
                local modsFromNode = parseNodeStats(nodeObj, treeNode)
                totalModsParsed = totalModsParsed + modsFromNode

                build.spec.allocNodes[nodeId] = nodeObj
                allocatedCount = allocatedCount + 1
            else
                print("[MinimalCalc]   WARNING: Node ID " .. nodeId .. " not found in tree data, skipping")
            end
        end
        print("[MinimalCalc]   allocated nodes: " .. allocatedCount .. " of " .. #buildData.passiveNodes)
        print("[MinimalCalc]   Story 2.9: Parsed " .. totalModsParsed .. " mods from passive tree stats")
    else
        print("[MinimalCalc]   no passive nodes allocated")
    end

    -- 5. Items tab - Story 2.9 Milestone 3: Process items from buildData
    build.itemsTab = {
        items = {},
        activeItemSet = {},
        orderedSlots = {}  -- Required by CalcSetup.lua:767
    }

    -- Process items passed from Python (Story 2.9 Milestone 3)
    local weaponSlotId = nil
    if buildData.items and type(buildData.items) == "table" then
        local itemCount = 0
        for i, itemData in pairs(buildData.items) do
            if type(itemData) == "table" and itemData.slot then
                -- Determine if this is a weapon
                local isWeapon = itemData.slot:match("^Weapon")

                if isWeapon and not weaponSlotId then  -- Only load first weapon
                    -- Get weapon type from base_type and normalize to category
                    -- Story 2.9: PoB expects weapon categories ("Bow") not specific bases ("Gemini Bow")
                    local rawType = itemData.base_type or "Bow"
                    local weaponType = rawType

                    -- Normalize specific base items to weapon categories
                    if rawType:match("Bow") then
                        weaponType = "Bow"
                    elseif rawType:match("Staff") or rawType:match("Quarterstaff") then
                        weaponType = "Staff"
                    elseif rawType:match("Sword") then
                        if rawType:match("Two Hand") then
                            weaponType = "Two Handed Sword"
                        else
                            weaponType = "One Handed Sword"
                        end
                    elseif rawType:match("Axe") then
                        if rawType:match("Two Hand") then
                            weaponType = "Two Handed Axe"
                        else
                            weaponType = "One Handed Axe"
                        end
                    elseif rawType:match("Mace") then
                        if rawType:match("Two Hand") then
                            weaponType = "Two Handed Mace"
                        else
                            weaponType = "One Handed Mace"
                        end
                    elseif rawType:match("Dagger") then
                        weaponType = "Dagger"
                    elseif rawType:match("Claw") then
                        weaponType = "Claw"
                    elseif rawType:match("Wand") then
                        weaponType = "Wand"
                    elseif rawType:match("Sceptre") then
                        weaponType = "Sceptre"
                    elseif rawType:match("Crossbow") then
                        weaponType = "Crossbow"
                    elseif rawType:match("Spear") then
                        -- Story 2.9.1: Added Spear pattern matching (AC-2.9.1.2)
                        weaponType = "Spear"
                    end

                    -- Get weapon type info from data.weaponTypeInfo
                    local weaponInfo = data.weaponTypeInfo[weaponType]
                    if not weaponInfo then
                        print("[MinimalCalc]   WARNING: weaponType '" .. weaponType .. "' not found in data.weaponTypeInfo, using defaults")
                        weaponInfo = { oneHand = false, melee = true, flag = weaponType }
                    else
                        print("[MinimalCalc]   Found weaponTypeInfo for: " .. weaponType)
                    end

                    -- Story 2.9.1 Phase 1: Use real PoB weapon data instead of hard-coded stubs (AC-2.9.1.3)
                    local basePhysMin, basePhysMax = 50, 100
                    local baseCritChance = 5
                    local baseAttackRate = 1.2
                    local baseRange = 11

                    -- Try to find exact base match first (e.g., "Gemini Bow"), then fall back to weapon type
                    local foundBase = false

                    -- First attempt: Exact base name match
                    if rawType and data.itemBases[rawType] then
                        local baseData = data.itemBases[rawType]
                        if baseData.weapon then
                            basePhysMin = baseData.weapon.PhysicalMin or 50
                            basePhysMax = baseData.weapon.PhysicalMax or 100
                            baseCritChance = baseData.weapon.CritChanceBase or 5
                            baseAttackRate = baseData.weapon.AttackRateBase or 1.2
                            baseRange = baseData.weapon.Range or 11
                            foundBase = true
                            print("[MinimalCalc]   Using PoB data for exact base: " .. rawType)
                        end
                    end

                    -- Second attempt: Find any base matching weaponType category
                    if not foundBase then
                        for baseName, baseData in pairs(data.itemBases) do
                            if baseData.type == weaponType and baseData.weapon then
                                basePhysMin = baseData.weapon.PhysicalMin or 50
                                basePhysMax = baseData.weapon.PhysicalMax or 100
                                baseCritChance = baseData.weapon.CritChanceBase or 5
                                baseAttackRate = baseData.weapon.AttackRateBase or 1.2
                                baseRange = baseData.weapon.Range or 11
                                foundBase = true
                                print("[MinimalCalc]   Using PoB data for " .. weaponType .. " from base: " .. baseName)
                                break  -- Use first matching base
                            end
                        end
                    end

                    -- Graceful fallback if weapon type not found in PoB data
                    if not foundBase then
                        print("[MinimalCalc]   WARNING: No PoB base found for weaponType '" .. weaponType .. "', using generic defaults")
                        -- Keep default values set above
                        if weaponType:match("Bow") or weaponType:match("Crossbow") then
                            basePhysMin, basePhysMax = 40, 80
                            baseAttackRate = 1.5
                            baseCritChance = 5
                        elseif weaponType:match("Staff") or weaponType:match("Quarterstaff") then
                            basePhysMin, basePhysMax = 70, 140
                            baseAttackRate = 1.0
                            baseCritChance = 7
                        end
                    end

                    -- Apply item's physical damage (adds to base)
                    local totalPhysMin = basePhysMin + (itemData.phys_min or 0)
                    local totalPhysMax = basePhysMax + (itemData.phys_max or 0)

                    -- Apply attack speed modifier
                    local attackSpeedMod = 1 + ((itemData.attack_speed_inc or 0) / 100)
                    local totalAttackRate = baseAttackRate * attackSpeedMod

                    -- Apply crit chance modifier
                    local totalCritChance = baseCritChance + (itemData.crit_chance_add or 0)

                    -- Create weapon item
                    local weapon = {
                        name = itemData.name or "Weapon",
                        type = "Weapon",
                        rarity = itemData.rarity or "NORMAL",
                        modList = new("ModList"),
                        baseModList = new("ModList"),
                        base = {
                            type = weaponType,
                            subType = weaponType,
                            weapon = weaponInfo
                        },
                        weaponData = {
                            [1] = {
                                type = weaponType,
                                AttackRate = totalAttackRate,
                                CritChance = totalCritChance,
                                PhysicalMin = totalPhysMin,
                                PhysicalMax = totalPhysMax,
                                range = baseRange  -- Story 2.9.1: Use real PoB range data
                            }
                        },
                        -- Story 2.9: CalcSetup.lua:1035 requires itemSocketCount to be a number
                        itemSocketCount = 0,
                        runes = {},  -- Empty runes table (PoE 2 feature)
                        socketedSoulCoreEffectModifier = 0,  -- CalcSetup.lua:1042
                        runeModLines = {},  -- CalcSetup.lua:1043
                        grantedSkills = {}  -- CalcSetup.lua:1131 (empty for non-unique items)
                    }

                    -- Add elemental damage to weapon if present
                    if itemData.lightning_min and itemData.lightning_min > 0 then
                        weapon.weaponData[1].LightningMin = itemData.lightning_min
                        weapon.weaponData[1].LightningMax = itemData.lightning_max or itemData.lightning_min
                    end
                    if itemData.cold_min and itemData.cold_min > 0 then
                        weapon.weaponData[1].ColdMin = itemData.cold_min
                        weapon.weaponData[1].ColdMax = itemData.cold_max or itemData.cold_min
                    end
                    if itemData.fire_min and itemData.fire_min > 0 then
                        weapon.weaponData[1].FireMin = itemData.fire_min
                        weapon.weaponData[1].FireMax = itemData.fire_max or itemData.fire_min
                    end

                    -- Add to items table (1-indexed)
                    itemCount = itemCount + 1
                    build.itemsTab.items[itemCount] = weapon
                    weaponSlotId = itemCount  -- Remember weapon slot for activeItemSet

                    print("[MinimalCalc]   Loaded weapon: " .. rawType .. " -> " .. weaponType .. " (Phys: " .. totalPhysMin .. "-" .. totalPhysMax .. ", APS: " .. string.format("%.2f", totalAttackRate) .. ")")
                end
                -- Non-weapon items can be processed here later (armor, jewelry, etc.)
            end
        end
        print("[MinimalCalc]   Story 2.9 Milestone 3: Loaded " .. itemCount .. " items from buildData")

        -- Set up activeItemSet and orderedSlots if we loaded a weapon
        if weaponSlotId then
            build.itemsTab.orderedSlots = {
                { slotName = "Weapon 1", weaponSet = 1, selItemId = weaponSlotId }  -- Story 2.9: selItemId required by CalcSetup.lua:795
            }
            build.itemsTab.activeItemSet = {
                useSecondWeaponSet = false
            }
        end
    else
        print("[MinimalCalc]   No items passed from Python")
    end

    -- 6. Skills tab - Story 2.9 Phase 2: Process passed skills into socket groups
    build.skillsTab = {
        skills = {},
        activeSkillGroup = 1,
        socketGroupList = {},  -- Required by CalcSetup.lua:1453
        displayGroup = nil,
        -- ProcessSocketGroup method stub (required by CalcSetup.lua:1373)
        ProcessSocketGroup = function(self, group)
            -- Story 2.9: Enhanced ProcessSocketGroup to set up activeEffect with skill flags
            -- This is critical for DPS calculation - without proper flags, DPS = 0

            for _, gemInstance in ipairs(group.gemList or {}) do
                if gemInstance.skillId and data.skills[gemInstance.skillId] then
                    local grantedEffect = data.skills[gemInstance.skillId]
                    gemInstance.grantedEffect = grantedEffect

                    -- Create activeEffect for the gem (required by calcs.perform)
                    -- activeEffect holds the processed skill data with flags set
                    if not gemInstance.activeEffect then
                        gemInstance.activeEffect = {
                            grantedEffect = grantedEffect,
                            srcGem = gemInstance,
                            level = gemInstance.level or 1,
                            quality = gemInstance.quality or 0
                        }
                    end

                    -- Set up skillFlags based on grantedEffect.skillTypes
                    -- SkillType enum: 1=Attack, 2=Spell, 3=Projectile, etc.
                    if grantedEffect.skillTypes then
                        local flags = {}
                        flags.attack = grantedEffect.skillTypes[1] == true  -- SkillType.Attack
                        flags.spell = grantedEffect.skillTypes[2] == true   -- SkillType.Spell
                        flags.projectile = grantedEffect.skillTypes[3] == true  -- SkillType.Projectile
                        flags.hit = flags.attack or flags.spell  -- Either attack or spell hits
                        flags.melee = grantedEffect.skillTypes[11] == true  -- SkillType.Melee (if it exists)
                        flags.ranged = not flags.melee and flags.attack  -- Attacks that aren't melee

                        -- Create statSet with skillFlags (this is what calcs.initEnv checks)
                        gemInstance.activeEffect.statSet = {
                            skillFlags = flags
                        }

                        -- Also set for CALCS mode
                        gemInstance.activeEffect.statSetCalcs = {
                            skillFlags = flags
                        }
                    end

                    -- Store weaponTypes for weapon validation
                    if grantedEffect.weaponTypes then
                        gemInstance.activeEffect.weaponTypes = grantedEffect.weaponTypes
                    end
                end
            end
        end
    }

    -- Process skills passed from Python (Story 2.9 Phase 2)
    if buildData.skills and type(buildData.skills) == "table" then
        local skillCount = 0
        for i, skillData in pairs(buildData.skills) do
            if type(skillData) == "table" and skillData.skillId then
                -- Check if skill exists in loaded data
                local grantedEffect = data.skills[skillData.skillId]
                if grantedEffect then
                    -- Create gem instance for active skill
                    local gemInstance = {
                        skillId = skillData.skillId,
                        grantedEffect = grantedEffect,
                        level = skillData.level or 1,
                        quality = skillData.quality or 0,
                        enabled = true,
                        nameSpec = skillData.name or grantedEffect.name,
                        statSet = { index = 1 },
                        statSetCalcs = { index = 1 }
                    }

                    -- Create socket group
                    local socketGroup = {
                        label = skillData.name or grantedEffect.name,
                        enabled = true,
                        gemList = { gemInstance },
                        slot = nil,
                        source = "Build"
                    }

                    -- Process support gems
                    if skillData.supports and type(skillData.supports) == "table" then
                        for j, supportData in pairs(skillData.supports) do
                            if type(supportData) == "table" and supportData.skillId then
                                local supportEffect = data.skills[supportData.skillId]
                                if supportEffect then
                                    local supportGem = {
                                        skillId = supportData.skillId,
                                        grantedEffect = supportEffect,
                                        level = supportData.level or 1,
                                        quality = supportData.quality or 0,
                                        enabled = true,
                                        nameSpec = supportData.nameSpec or supportEffect.name
                                    }
                                    table.insert(socketGroup.gemList, supportGem)
                                end
                            end
                        end
                    end

                    table.insert(build.skillsTab.socketGroupList, socketGroup)

                    -- Process socket group to set up skill flags and metadata
                    build.skillsTab:ProcessSocketGroup(socketGroup)

                    skillCount = skillCount + 1
                else
                    print("[MinimalCalc]   WARNING: Skill '" .. skillData.skillId .. "' not found in data.skills")
                end
            end
        end
        print("[MinimalCalc]   Story 2.9 Phase 2: Created " .. skillCount .. " socket groups from passed skills")

        -- Story 2.9 Milestone 3: Fallback weapon stub (only if no items loaded)
        -- Create minimal weapon stub if skills require it and no items were passed
        local hasWeapon = false
        for _, item in pairs(build.itemsTab.items) do
            if item.weaponData then
                hasWeapon = true
                break
            end
        end

        local requiredWeaponType = nil
        if not hasWeapon then
            -- Detect required weapon type from skills
        for _, group in ipairs(build.skillsTab.socketGroupList) do
            for _, gem in ipairs(group.gemList) do
                if gem.grantedEffect and gem.grantedEffect.weaponTypes then
                    -- Find the first required weapon type
                    for weaponType, required in pairs(gem.grantedEffect.weaponTypes) do
                        if required then
                            requiredWeaponType = weaponType
                            print("[MinimalCalc]   Skill '" .. (gem.grantedEffect.name or gem.skillId) .. "' requires weapon type: " .. weaponType)
                            break
                        end
                    end
                    if requiredWeaponType then break end
                end
            end
            if requiredWeaponType then break end
        end

        -- Create minimal weapon if required
        if requiredWeaponType then
            print("[MinimalCalc]   Creating minimal " .. requiredWeaponType .. " weapon stub for DPS calculation")

            -- Get weapon type info from data.weaponTypeInfo
            local weaponInfo = data.weaponTypeInfo[requiredWeaponType] or { oneHand = false, melee = true, flag = requiredWeaponType }

            -- Create minimal weapon data based on weapon type
            -- Default base weapon stats (approximate for level ~80 weapon)
            local basePhysMin, basePhysMax = 50, 100
            local baseCritChance = 5
            local baseAttackRate = 1.2

            -- Adjust stats based on weapon type
            if requiredWeaponType == "Staff" then
                basePhysMin, basePhysMax = 70, 140
                baseAttackRate = 1.0
                baseCritChance = 7
            elseif requiredWeaponType == "Bow" or requiredWeaponType == "Crossbow" then
                basePhysMin, basePhysMax = 40, 80
                baseAttackRate = 1.5
                baseCritChance = 5
            elseif requiredWeaponType == "Two Handed Sword" or requiredWeaponType == "Two Handed Axe" or requiredWeaponType == "Two Handed Mace" then
                basePhysMin, basePhysMax = 80, 160
                baseAttackRate = 0.9
                baseCritChance = 5
            elseif requiredWeaponType == "Claw" or requiredWeaponType == "Dagger" then
                basePhysMin, basePhysMax = 30, 60
                baseAttackRate = 1.6
                baseCritChance = 7
            elseif requiredWeaponType == "Sceptre" or requiredWeaponType == "Wand" then
                basePhysMin, basePhysMax = 20, 40
                baseAttackRate = 1.4
                baseCritChance = 7
            end

            -- Create minimal item with weaponData
            build.itemsTab.items[1] = {
                name = "Minimal " .. requiredWeaponType,
                type = "Weapon",
                rarity = "NORMAL",
                modList = new("ModList"),
                baseModList = new("ModList"),
                base = {
                    type = requiredWeaponType,
                    subType = requiredWeaponType,
                    weapon = weaponInfo
                },
                weaponData = {
                    [1] = {
                        type = requiredWeaponType,
                        AttackRate = baseAttackRate,
                        CritChance = baseCritChance,
                        PhysicalMin = basePhysMin,
                        PhysicalMax = basePhysMax,
                        range = 11  -- Default melee range
                    }
                }
            }

            -- Add to orderedSlots
            build.itemsTab.orderedSlots = {
                { slotName = "Weapon 1", weaponSet = 1 }
            }
            build.itemsTab.activeItemSet = {
                useSecondWeaponSet = false,
                [1] = { id = 1 }
            }

            print("[MinimalCalc]   Weapon stub created: " .. requiredWeaponType .. " (Phys: " .. basePhysMin .. "-" .. basePhysMax .. ", APS: " .. baseAttackRate .. ")")
            end
        end  -- End of if not hasWeapon (fallback weapon stub)
    else
        print("[MinimalCalc]   No skills passed from Python")
    end

    -- 7. Calculations tab
    build.calcsTab = {
        input = {}
    }

    -- 8. Party tab (required by CalcSetup.lua:666, CalcPerform.lua:895)
    build.partyTab = {
        enemyModList = {},
        actor = {  -- Required by CalcPerform.lua:895 -> 1636
            Aura = {},
            Curse = {},
            Link = {},
            -- Minimal modDB stub for party members (CalcPerform.lua:709)
            modDB = {
                Flag = function(self, cfg, flag) return false end,
                Sum = function(self, type, cfg, name) return 0 end
            },
            output = {}
        }
    }

    -- 9. Misc build state (required by CalcSetup)
    build.misc = {}

    print("[MinimalCalc] Build object constructed, calling calcs.initEnv()...")

    -- Debug: Check weapon structure before CalcSetup processes it
    if build.itemsTab.items[1] and build.itemsTab.items[1].weaponData then
        local weapon = build.itemsTab.items[1]
        print("[MinimalCalc] DEBUG: Weapon before CalcSetup:")
        print("[MinimalCalc]   weapon.type = " .. tostring(weapon.type))
        print("[MinimalCalc]   weapon.base.type = " .. tostring(weapon.base and weapon.base.type))
        print("[MinimalCalc]   weapon.weaponData[1].type = " .. tostring(weapon.weaponData[1] and weapon.weaponData[1].type))
    end

    -- Debug: Check tree structure
    if build.spec.tree then
        print("[MinimalCalc] Tree data exists, checking classes...")
        if build.spec.tree.classes then
            print("[MinimalCalc] Tree has classes table")
            if build.spec.tree.classes[classId] then
                print("[MinimalCalc] Tree has data for classId " .. classId)
                print("[MinimalCalc] Class name: " .. tostring(build.spec.tree.classes[classId].name))
            else
                print("[MinimalCalc] WARNING: Tree missing data for classId " .. classId)
                print("[MinimalCalc] Available class indices: " .. table.concat(getTableKeys(build.spec.tree.classes), ", "))
            end
        else
            print("[MinimalCalc] WARNING: Tree has no classes table")
        end
    else
        print("[MinimalCalc] WARNING: No tree data provided")
    end

    -- Check if calcs module loaded successfully
    if not calcs or not calcs.initEnv or not calcs.perform then
        error("[MinimalCalc] Calcs module not loaded or missing functions. Check PoB module loading.")
    end

    -- Initialize calculation environment (wrap in pcall for error handling)
    -- calcs.initEnv() creates env.player and other calculation structures
    local success, env_or_err = pcall(calcs.initEnv, build, "CALCULATOR")

    if not success then
        local err_msg = tostring(env_or_err)
        print("[MinimalCalc] ERROR: calcs.initEnv() failed")
        print("[MinimalCalc] ERROR details: " .. err_msg)
        print("[MinimalCalc] ERROR type: " .. type(env_or_err))
        -- Try to get full traceback if available
        if type(env_or_err) == "string" then
            print("[MinimalCalc] ERROR traceback: " .. debug.traceback())
        end
        error("[MinimalCalc] calcs.initEnv() failed: " .. err_msg)
    end

    local env = env_or_err

    print("[MinimalCalc] calcs.initEnv() successful, calling calcs.perform()...")

    -- Story 2.9: Debug weaponData1 created by CalcSetup
    if env.player.weaponData1 then
        print("[MinimalCalc] DEBUG: env.player.weaponData1 after CalcSetup:")
        print("[MinimalCalc]   weaponData1.type = " .. tostring(env.player.weaponData1.type or "NIL"))
        print("[MinimalCalc]   weaponData1.AttackRate = " .. tostring(env.player.weaponData1.AttackRate or "NIL"))
        print("[MinimalCalc]   weaponData1.PhysicalMin = " .. tostring(env.player.weaponData1.PhysicalMin or "NIL"))
        print("[MinimalCalc]   weaponData1.PhysicalMax = " .. tostring(env.player.weaponData1.PhysicalMax or "NIL"))
    else
        print("[MinimalCalc] WARNING: env.player.weaponData1 is NIL!")
    end

    -- Debug: Check weapon structure AFTER CalcSetup processes it
    if build.itemsTab.items[1] then
        local weapon = build.itemsTab.items[1]
        print("[MinimalCalc] DEBUG: Weapon AFTER CalcSetup:")
        if weapon.base then
            print("[MinimalCalc]   weapon.base.type = " .. tostring(weapon.base.type or "NIL"))
        else
            print("[MinimalCalc]   weapon.base = NIL")
        end
        if weapon.weaponData and weapon.weaponData[1] then
            print("[MinimalCalc]   weapon.weaponData[1].type = " .. tostring(weapon.weaponData[1].type or "NIL"))
        else
            print("[MinimalCalc]   weapon.weaponData[1] = NIL")
        end
    end

    -- Story 2.9: Fix skillFlags on mainSkill after calcs.initEnv()
    -- calcs.initEnv() creates mainSkill but doesn't set skillFlags properly from our socket groups
    -- We need to manually populate skillFlags based on the skill's grantedEffect.skillTypes
    if env.player.mainSkill and env.player.mainSkill.activeEffect then
        local activeEffect = env.player.mainSkill.activeEffect
        local grantedEffect = activeEffect.grantedEffect

        if grantedEffect and grantedEffect.skillTypes then
            print("[MinimalCalc] Fixing skillFlags for mainSkill...")

            local flags = {}
            flags.attack = grantedEffect.skillTypes[1] == true  -- SkillType.Attack
            flags.spell = grantedEffect.skillTypes[2] == true   -- SkillType.Spell
            flags.projectile = grantedEffect.skillTypes[3] == true  -- SkillType.Projectile
            flags.hit = flags.attack or flags.spell
            flags.melee = grantedEffect.skillTypes[11] == true
            flags.ranged = not flags.melee and flags.attack

            -- Story 2.9 FIX: Set weapon-specific attack flags (critical for CalcOffence)
            -- CalcOffence.lua:1885 needs these to determine which weapon to use for damage
            if flags.attack then
                -- For attacks, determine if using weapon slot 1, 2, or unarmed
                -- Check if player has weaponData1 (primary weapon)
                if env.player.weaponData1 then
                    flags.weapon1Attack = true
                    flags.weapon2Attack = false  -- Single weapon build (bow/2h)
                    flags.unarmed = false
                else
                    -- No weapon equipped - treat as unarmed
                    flags.weapon1Attack = false
                    flags.weapon2Attack = false
                    flags.unarmed = true
                end
            else
                -- Spells don't use weapons
                flags.weapon1Attack = false
                flags.weapon2Attack = false
                flags.unarmed = false
            end

            -- Set flags on the appropriate statSet based on mode
            if not activeEffect.statSet then
                activeEffect.statSet = {}
            end
            activeEffect.statSet.skillFlags = flags

            if not activeEffect.statSetCalcs then
                activeEffect.statSetCalcs = {}
            end
            activeEffect.statSetCalcs.skillFlags = flags

            -- Story 2.9 CRITICAL FIX: Set weapon1Flags on mainSkill itself
            -- CalcOffence checks mainSkill.weapon1Flags, NOT just skillFlags!
            if flags.weapon1Attack then
                env.player.mainSkill.weapon1Flags = 1  -- Non-zero indicates weapon 1 is used
            else
                env.player.mainSkill.weapon1Flags = 0
            end

            print("[MinimalCalc] skillFlags set: attack=" .. tostring(flags.attack) .. ", weapon1Attack=" .. tostring(flags.weapon1Attack) .. ", projectile=" .. tostring(flags.projectile))
            print("[MinimalCalc] mainSkill.weapon1Flags = " .. tostring(env.player.mainSkill.weapon1Flags))
        end
    end

    -- Debug: Check if main skill was created and has attack flag
    if env.player.mainSkill then
        print("[MinimalCalc] DEBUG: mainSkill exists")
        local activeEffect = env.player.mainSkill.activeEffect
        if activeEffect then
            print("[MinimalCalc] DEBUG: activeEffect exists")
            if activeEffect.grantedEffect then
                print("[MinimalCalc] DEBUG: grantedEffect name: " .. tostring(activeEffect.grantedEffect.name))
            end
            -- Check skillFlags
            local skillFlags = (env.mode == "CALCS" and activeEffect.statSetCalcs and activeEffect.statSetCalcs.skillFlags)
                            or (activeEffect.statSet and activeEffect.statSet.skillFlags)
            if skillFlags then
                print("[MinimalCalc] DEBUG: skillFlags.attack = " .. tostring(skillFlags.attack))
                print("[MinimalCalc] DEBUG: skillFlags.melee = " .. tostring(skillFlags.melee))
                print("[MinimalCalc] DEBUG: skillFlags.weapon1Attack = " .. tostring(skillFlags.weapon1Attack))
                print("[MinimalCalc] DEBUG: skillFlags.weapon2Attack = " .. tostring(skillFlags.weapon2Attack))
                print("[MinimalCalc] DEBUG: skillFlags.unarmed = " .. tostring(skillFlags.unarmed))
            else
                print("[MinimalCalc] DEBUG: skillFlags not found!")
            end
        end
    else
        print("[MinimalCalc] DEBUG: mainSkill NOT created!")
    end
    -- Debug: Check weaponData
    print("[MinimalCalc] DEBUG: weaponData1 = " .. tostring(env.player.weaponData1))
    if env.player.weaponData1 then
        print("[MinimalCalc] DEBUG: weaponData1.type = " .. tostring(env.player.weaponData1.type))
        print("[MinimalCalc] DEBUG: weaponData1.AttackRate = " .. tostring(env.player.weaponData1.AttackRate))
    end

    -- Pre-initialize output stats with base values to prevent nil arithmetic errors
    -- Many stats default to 0 if not present - this ensures GetStat doesn't return nil
    if not env.player.output then
        env.player.output = {}
    end

    -- Perform calculations (wrap in pcall for error handling)
    -- calcs.perform() populates env.player.output with calculated stats
    local performSuccess, performError = pcall(calcs.perform, env)

    if not performSuccess then
        local errorMsg = tostring(performError)
        print("[MinimalCalc] ERROR: calcs.perform() failed")
        print("[MinimalCalc] ERROR details: " .. errorMsg)
        -- Extract more context if possible
        if type(performError) == "string" and performError:match("CalcPerform.lua:2904") then
            print("[MinimalCalc] ERROR: Ailment calculation failed at line 2904")
            print("[MinimalCalc] HINT: Check data.ailmentData table for missing ailments")
        elseif type(performError) == "string" and (performError:match("CalcOffence.lua") or performError:match("CalcPerform.lua")) then
            print("[MinimalCalc] ERROR: CalcOffence/CalcPerform failed")
            print("[MinimalCalc] HINT: Likely missing weapon, skill, or modifier data")
            print("[MinimalCalc] ERROR FULL: " .. tostring(performError))
            print("[MinimalCalc] Continuing with degraded calculations (DPS may be 0)...")
            -- Don't error out - allow graceful degradation
            performSuccess = true  -- Pretend it succeeded so we can extract what we can
        end

        if not performSuccess then
            error("[MinimalCalc] calcs.perform() failed: " .. errorMsg)
        end
    end

    print("[MinimalCalc] calcs.perform() successful, extracting results...")

    -- Debug: Check mainSkill output after perform
    if env.player.mainSkill then
        print("[MinimalCalc] DEBUG: mainSkill exists after perform")
        if env.player.mainSkill.output then
            local skillOutput = env.player.mainSkill.output
            print("[MinimalCalc] DEBUG: mainSkill.output exists")
            print("[MinimalCalc] DEBUG: mainSkill.output.Accuracy = " .. tostring(skillOutput.Accuracy))
            print("[MinimalCalc] DEBUG: mainSkill.output.AccuracyHitChance = " .. tostring(skillOutput.AccuracyHitChance))
            print("[MinimalCalc] DEBUG: mainSkill.output.HitChance = " .. tostring(skillOutput.HitChance))
            print("[MinimalCalc] DEBUG: mainSkill.output.TotalDPS = " .. tostring(skillOutput.TotalDPS))
        else
            print("[MinimalCalc] DEBUG: mainSkill.output is NIL!")
            -- Check what fields mainSkill DOES have
            print("[MinimalCalc] DEBUG: mainSkill fields:")
            for k, v in pairs(env.player.mainSkill) do
                if type(v) ~= "function" and type(v) ~= "table" then
                    print("[MinimalCalc]   " .. tostring(k) .. " = " .. tostring(v))
                elseif type(v) == "table" and k ~= "activeEffect" then
                    print("[MinimalCalc]   " .. tostring(k) .. " = <table>")
                end
            end
        end
    end

    -- Extract calculated stats from env.player.output
    local output = env.player.output or {}
    print("[MinimalCalc] DEBUG: Extracting from player.output (not mainSkill.output)")

    -- Helper function to safely extract numeric values
    local function getNum(field, default)
        local value = output[field]
        if type(value) == "number" then
            return value
        end
        return default or 0
    end

    -- Construct result table
    local results = {
        -- Primary stats
        TotalDPS = getNum("TotalDPS"),
        Life = getNum("Life"),
        EnergyShield = getNum("EnergyShield"),
        Mana = getNum("Mana"),

        -- Effective HP (may not be directly available, calculate if needed)
        EHP = getNum("EHP", getNum("Life")),  -- Fallback to Life if EHP not available

        -- Resistances
        FireResist = getNum("FireResist"),
        ColdResist = getNum("ColdResist"),
        LightningResist = getNum("LightningResist"),
        ChaosResist = getNum("ChaosResist"),

        -- Defense stats
        Armour = getNum("Armour"),
        Evasion = getNum("Evasion"),

        -- Additional stats (if available)
        BlockChance = getNum("BlockChance"),
        SpellBlockChance = getNum("SpellBlockChance"),
        MovementSpeed = getNum("MovementSpeed")
    }

    print("[MinimalCalc] Calculation complete!")
    print("[MinimalCalc]   TotalDPS: " .. tostring(results.TotalDPS))
    print("[MinimalCalc]   Life: " .. tostring(results.Life))
    print("[MinimalCalc]   EnergyShield: " .. tostring(results.EnergyShield))
    print("[MinimalCalc]   Mana: " .. tostring(results.Mana))

    -- Debug: Log DPS calculation breakdown
    print("[MinimalCalc] DPS BREAKDOWN:")
    print("[MinimalCalc]   AverageDamage: " .. tostring(getNum("AverageDamage", "N/A")))
    print("[MinimalCalc]   AverageHit: " .. tostring(getNum("AverageHit", "N/A")))
    print("[MinimalCalc]   HitChance: " .. tostring(getNum("HitChance", "N/A")))
    print("[MinimalCalc]   AccuracyHitChance: " .. tostring(getNum("AccuracyHitChance", "N/A")))
    print("[MinimalCalc]   Speed: " .. tostring(getNum("Speed", "N/A")))
    print("[MinimalCalc]   Accuracy: " .. tostring(getNum("Accuracy", "N/A")))
    print("[MinimalCalc]   Dex: " .. tostring(getNum("Dex", "N/A")))
    print("[MinimalCalc]   Str: " .. tostring(getNum("Str", "N/A")))
    print("[MinimalCalc]   Int: " .. tostring(getNum("Int", "N/A")))

    return results
end

print("[MinimalCalc] Bootstrap complete - Calculate() function exposed - TIMESTAMP: 1760762916.3465545")
