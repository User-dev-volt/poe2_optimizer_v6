"""Check how to get actual stat values for gem levels"""

import sys
sys.path.insert(0, str(__file__).replace('scripts\\check_stat_values.py', ''))

from src.calculator.pob_engine import PoBCalculationEngine

# Initialize engine
engine = PoBCalculationEngine()
engine._ensure_initialized()
lua = engine._lua

# Check Ball Lightning
skill_id = 'BallLightningPlayer'
skill = lua.globals().data.skills[skill_id]

print("="*80)
print(f"=== {skill.name} - Stat Values by Level ===")
print("="*80)

# Get the skillStatMap
stat_map = lua.globals().data.skillStatMap

# Check statSet 1
if hasattr(skill, 'statSets') and 1 in skill.statSets:
    statSet = skill.statSets[1]

    print(f"\nStatSet 1 has {len(statSet.stats)} stats")

    # For each stat, get the stat name
    for stat_idx, stat_name in statSet.stats.items():
        print(f"\n--- Stat {stat_idx}: {stat_name} ---")

        # Check if this stat has levelProgression in skillStatMap
        if stat_name in stat_map:
            stat_data = stat_map[stat_name]
            print(f"  SkillStatMap entry found!")

            # Check what fields stat_data has
            print(f"  Fields in stat_data:")
            for key in stat_data.keys():
                val = stat_data[key]
                if type(val).__name__ == 'LuaTable':
                    # If it's a table, show how many entries
                    try:
                        table_len = len(val)
                        print(f"    {key}: <table with {table_len} entries>")

                        # If it's a levelProgression table, show a few entries
                        if key == 'levelProgression' and table_len > 0:
                            print(f"      Sample values:")
                            for i, entry in val.items():
                                if i <= 5 or i == 20:  # Show first 5 and level 20
                                    print(f"        Level {i}: {entry}")
                    except:
                        print(f"    {key}: <table>")
                else:
                    print(f"    {key}: {val}")
        else:
            print(f"  Not found in skillStatMap")

        # Only check first 2 stats (min and max damage)
        if stat_idx >= 2:
            break

print("\n" + "="*80)
