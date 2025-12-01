"""Deep dive into stat value structure"""

import sys
sys.path.insert(0, str(__file__).replace('scripts\\deep_stat_check.py', ''))

from src.calculator.pob_engine import PoBCalculationEngine

# Initialize engine
engine = PoBCalculationEngine()
engine._ensure_initialized()
lua = engine._lua

# Check Ball Lightning
skill_id = 'BallLightningPlayer'
skill = lua.globals().data.skills[skill_id]

print("="*80)
print(f"=== {skill.name} - Deep Stat Structure ===")
print("="*80)

# Get the skillStatMap
stat_map = lua.globals().data.skillStatMap

# Check first stat: spell_minimum_base_lightning_damage
stat_name = 'spell_minimum_base_lightning_damage'
if stat_name in stat_map:
    stat_data = stat_map[stat_name]
    print(f"\nStat: {stat_name}")

    # stat_data seems to be keyed by game version (1 = PoE 2?)
    if 1 in stat_data:
        version_data = stat_data[1]
        print(f"\n  Version 1 data:")

        # Check what fields version_data has
        for key in version_data.keys():
            val = version_data[key]
            print(f"    {key}: {type(val).__name__}")

            # If it's a table, try to get some values
            if type(val).__name__ == 'LuaTable':
                try:
                    # Try treating it as an array
                    print(f"      Checking as array...")
                    for i in [1, 5, 10, 15, 20]:
                        if i in val:
                            print(f"        [{i}] = {val[i]}")
                except Exception as e:
                    print(f"      Error accessing array: {e}")

                try:
                    # Try getting all keys
                    print(f"      All keys:")
                    for k in list(val.keys())[:10]:  # First 10 keys
                        print(f"        {k}: {val[k]}")
                except Exception as e:
                    print(f"      Error getting keys: {e}")

print("\n" + "="*80)

# Also check second stat
stat_name2 = 'spell_maximum_base_lightning_damage'
if stat_name2 in stat_map:
    stat_data2 = stat_map[stat_name2]
    print(f"\nStat: {stat_name2}")

    if 1 in stat_data2:
        version_data2 = stat_data2[1]
        print(f"\n  Version 1 data has {len(version_data2)} keys")

        # Show all keys
        for key in version_data2.keys():
            val = version_data2[key]
            print(f"    {key}: {type(val).__name__}")

            if type(val).__name__ == 'LuaTable' and len(val) > 0:
                # Show a few sample values
                sample_keys = list(val.keys())[:5]
                print(f"      Sample: {[(k, val[k]) for k in sample_keys]}")

print("\n" + "="*80)
