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
data.weaponTypeInfo = {
    None = { name = "None", oneHand = false, melee = true, flag = "Unarmed" }
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

print("[MinimalCalc] ===== STEP 4c: Stubbing data.gems and data.skills (not needed for Story 1.5 - no skills) =====")
data.gems = {}  -- Empty table to satisfy ModParser; gem data not needed for passive-tree-only calculations
-- Add minimal default unarmed skill (required by CalcSetup.lua:1777)
data.skills = {
    MeleeUnarmedPlayer = {
        name = "Default Attack",
        color = 1,
        baseFlags = { attack = true, melee = true, unarmed = true },  -- Added unarmed flag
        baseMods = {},
        qualityMods = {},
        stats = {},
        skillTypes = { [SkillType.Attack] = true, [SkillType.Melee] = true },  -- Required by CalcActiveSkill.lua:105
        statSets = {  -- Required by CalcActiveSkill.lua:118
            [1] = {
                baseFlags = { attack = true, melee = true, unarmed = true },  -- Added unarmed flag
                mods = {},
                stats = {},  -- Required by CalcTools.lua:149
                levels = {}  -- Required by CalcTools.lua:146
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
}
print("[MinimalCalc] SUCCESS: data.gems and data.skills initialized with minimal stubs")

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

    -- Populate allocated passive nodes
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
                }
                build.spec.allocNodes[nodeId] = nodeObj
                allocatedCount = allocatedCount + 1
            else
                print("[MinimalCalc]   WARNING: Node ID " .. nodeId .. " not found in tree data, skipping")
            end
        end
        print("[MinimalCalc]   allocated nodes: " .. allocatedCount .. " of " .. #buildData.passiveNodes)
    else
        print("[MinimalCalc]   no passive nodes allocated")
    end

    -- 5. Items tab (empty for Story 1.5 scope)
    build.itemsTab = {
        items = {},
        activeItemSet = {},
        orderedSlots = {}  -- Required by CalcSetup.lua:767
    }

    -- 6. Skills tab (empty for Story 1.5 scope)
    build.skillsTab = {
        skills = {},
        activeSkillGroup = 1,
        socketGroupList = {}  -- Required by CalcSetup.lua:1453
    }

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
        end
        error("[MinimalCalc] calcs.perform() failed: " .. errorMsg)
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
