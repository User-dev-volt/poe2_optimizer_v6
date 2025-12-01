"""Verify that skill data is properly loaded with statSets.levels and stats"""

import sys
sys.path.insert(0, str(__file__).replace('scripts\\verify_skill_data_loaded.py', ''))

from src.calculator.pob_engine import PoBCalculationEngine

# Initialize engine
engine = PoBCalculationEngine()
engine._ensure_initialized()
lua = engine._lua

# Check Ball Lightning
skill_id = 'BallLightningPlayer'
skill = lua.globals().data.skills[skill_id]

print("="*80)
print(f"=== {skill.name} - Data Verification ===")
print("="*80)

# Check statSets existence
if hasattr(skill, 'statSets'):
    print(f"\n[OK] skill.statSets exists")
    print(f"  Number of statSets: {len(skill.statSets)}")

    # Check statSet 1
    if 1 in skill.statSets:
        statSet = skill.statSets[1]
        print(f"\n[OK] statSet[1] exists")

        # Check stats array
        if hasattr(statSet, 'stats') and type(statSet.stats).__name__ == '_LuaTable':
            stats_count = len(statSet.stats) if hasattr(statSet.stats, '__len__') else len(list(statSet.stats.keys()))
            print(f"  [OK] statSet.stats exists (count: {stats_count})")

            # Print first few stats
            print(f"    First 5 stats:")
            for i in range(1, min(6, stats_count + 1)):
                if i in statSet.stats:
                    print(f"      [{i}] {statSet.stats[i]}")
        else:
            print(f"  [ERROR] statSet.stats is missing or not a table!")
            print(f"    Type: {type(statSet.stats)}")

        # Check levels array
        if hasattr(statSet, 'levels') and type(statSet.levels).__name__ == '_LuaTable':
            levels_count = len(statSet.levels) if hasattr(statSet.levels, '__len__') else len(list(statSet.levels.keys()))
            print(f"  [OK] statSet.levels exists (count: {levels_count})")

            # Print level 1 and level 20 data
            for level_num in [1, 20]:
                if level_num in statSet.levels:
                    level_data = statSet.levels[level_num]
                    print(f"    Level {level_num} data:")

                    # Try to get values as array
                    try:
                        values = []
                        for i in range(1, 10):  # Try first 10 positions
                            if i in level_data:
                                values.append(level_data[i])
                            else:
                                break
                        if values:
                            print(f"      Values: {values}")
                        else:
                            # Try getting keys
                            keys = list(level_data.keys())[:5]
                            print(f"      Keys: {keys}")
                    except Exception as e:
                        print(f"      Error reading level data: {e}")
        else:
            print(f"  [ERROR] statSet.levels is missing or not a table!")
            print(f"    Type: {type(statSet.levels)}")
    else:
        print(f"\n[ERROR] statSet[1] does not exist!")
else:
    print(f"\n[ERROR] skill.statSets does not exist!")

print("\n" + "="*80)
