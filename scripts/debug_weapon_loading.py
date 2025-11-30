"""Debug script to check if PoB weapon data is loading correctly."""

import sys
from pathlib import Path

# Add project root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from src.calculator.pob_engine import PoBCalculationEngine

print("Creating PoBCalculationEngine instance...")
engine = PoBCalculationEngine()

# Trigger initialization
print("Initializing engine...")
engine._ensure_initialized()

print("\nExecuting Lua code to check itemBases table...")
lua_code = """
print("Checking data.itemBases table...")
if data.itemBases then
    local count = 0
    local spear_count = 0
    local mace_count = 0

    for name, base in pairs(data.itemBases) do
        count = count + 1
        if base.type == "Spear" then
            spear_count = spear_count + 1
            if spear_count <= 3 then
                print("  Found Spear: " .. name)
                if base.weapon then
                    print("    PhysMin=" .. tostring(base.weapon.PhysicalMin) ..
                          ", PhysMax=" .. tostring(base.weapon.PhysicalMax) ..
                          ", APS=" .. tostring(base.weapon.AttackRateBase))
                end
            end
        elseif base.type == "One Handed Mace" then
            mace_count = mace_count + 1
            if mace_count <= 3 then
                print("  Found One Handed Mace: " .. name)
                if base.weapon then
                    print("    PhysMin=" .. tostring(base.weapon.PhysicalMin) ..
                          ", PhysMax=" .. tostring(base.weapon.PhysicalMax) ..
                          ", APS=" .. tostring(base.weapon.AttackRateBase))
                end
            end
        end
    end

    print("Total itemBases entries: " .. count)
    print("Spear entries: " .. spear_count)
    print("One Handed Mace entries: " .. mace_count)
else
    print("ERROR: data.itemBases is NIL!")
end

print("\\nChecking weaponTypeInfo for Spear...")
if data.weaponTypeInfo and data.weaponTypeInfo.Spear then
    print("  Spear found in weaponTypeInfo:")
    print("    name=" .. tostring(data.weaponTypeInfo.Spear.name))
    print("    oneHand=" .. tostring(data.weaponTypeInfo.Spear.oneHand))
    print("    melee=" .. tostring(data.weaponTypeInfo.Spear.melee))
    print("    flag=" .. tostring(data.weaponTypeInfo.Spear.flag))
else
    print("  ERROR: Spear NOT found in weaponTypeInfo!")
end
"""

engine._lua.execute(lua_code)

print("\n=== Debug complete ===")
