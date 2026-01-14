"""Debug script to examine spell base damage data in PoB"""

import sys
sys.path.insert(0, str(__file__).replace('scripts\\debug_spell_data.py', ''))

from src.calculator.pob_engine import PoBCalculationEngine

# Initialize engine
engine = PoBCalculationEngine()
engine._ensure_initialized()
lua = engine._lua

# Get Ball Lightning spell data
skill = lua.globals().data.skills['BallLightningPlayer']

print("=== Ball Lightning Spell Data ===\n")
print(f"Skill Name: {skill.name}")
print(f"Skill ID: {skill.id}")

# Check level data
if hasattr(skill, 'levels') and len(skill.levels) > 0:
    # Get level 20 data (index 20 in Lua 1-indexed table)
    level_20 = list(skill.levels.values())[19] if len(skill.levels) >= 20 else list(skill.levels.values())[0]

    print(f"\nLevel 20 Data:")
    print(f"  Level Requirement: {level_20.levelRequirement if hasattr(level_20, 'levelRequirement') else 'N/A'}")
    print(f"  Mana Cost: {level_20.manaCost if hasattr(level_20, 'manaCost') else 'N/A'}")

    # Look for base damage fields
    print(f"\n  Available fields:")
    for key in level_20.keys():
        val = level_20[key]
        print(f"    {key}: {val}")
else:
    print("  No level data found")

# Check stat sets for spell damage
print(f"\nStat Sets:")
if hasattr(skill, 'statSets') and len(skill.statSets) > 0:
    first_statset = list(skill.statSets.values())[0]

    # Check for stats
    if hasattr(first_statset, 'stats'):
        print(f"  Stats in statSet[1]:")
        for stat_id in first_statset.stats.keys():
            print(f"    - {stat_id}")

    # Check baseFlags
    if hasattr(first_statset, 'baseFlags'):
        print(f"  Base Flags:")
        for flag in first_statset.baseFlags.keys():
            print(f"    - {flag}")
