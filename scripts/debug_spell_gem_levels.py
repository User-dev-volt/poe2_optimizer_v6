"""Enhanced debug script to examine spell gem level data and stat mapping"""

import sys
sys.path.insert(0, str(__file__).replace('scripts\\debug_spell_gem_levels.py', ''))

from src.calculator.pob_engine import PoBCalculationEngine

# Initialize engine
engine = PoBCalculationEngine()
engine._ensure_initialized()
lua = engine._lua

# Examine Pain Offering (the spell used by witch_frost_mage_91)
skill_id = 'PainOfferingPlayer'
skill = lua.globals().data.skills[skill_id]

print("="*80)
print(f"=== {skill.name} ({skill_id}) ===")
print("="*80)

# Check skillTypes
print("\nSkill Types:")
if hasattr(skill, 'skillTypes'):
    for idx, is_type in skill.skillTypes.items():
        if is_type:
            print(f"  Type[{idx}] = {is_type}")

# Get SkillStatMap to understand stat ID meanings
stat_map = lua.globals().data.skillStatMap
print("\n" + "="*80)
print("=== SkillStatMap (First 20 entries) ===")
print("="*80)
stat_count = 0
for stat_id, stat_data in stat_map.items():
    if stat_count < 20:
        print(f"  {stat_id}: {stat_data}")
        stat_count += 1

# Examine level data
print("\n" + "="*80)
print(f"=== {skill.name} Level Data ===")
print("="*80)

if hasattr(skill, 'levels'):
    print(f"\nTotal levels available: {len(skill.levels)}")

    # Check a few key levels (1, 10, 20)
    for level_num in [1, 10, 20]:
        if level_num in skill.levels:
            level_data = skill.levels[level_num]
            print(f"\n--- Level {level_num} ---")
            print(f"  levelRequirement: {level_data.levelRequirement if hasattr(level_data, 'levelRequirement') else 'N/A'}")
            print(f"  critChance: {level_data.critChance if hasattr(level_data, 'critChance') else 'N/A'}")

            if hasattr(level_data, 'cost'):
                print(f"  cost: {level_data.cost}")

            # Check all available fields
            print(f"  All fields at level {level_num}:")
            for key in level_data.keys():
                val = level_data[key]
                print(f"    {key}: {val}")

# Examine statSets (this contains the damage stat IDs)
print("\n" + "="*80)
print(f"=== {skill.name} StatSets ===")
print("="*80)

if hasattr(skill, 'statSets'):
    print(f"\nTotal statSets: {len(skill.statSets)}")

    for set_idx in skill.statSets.keys():
        statSet = skill.statSets[set_idx]
        print(f"\n--- StatSet {set_idx} ---")

        # Check stats
        if hasattr(statSet, 'stats'):
            print(f"  Stats:")
            for stat_id in statSet.stats.keys():
                stat_value = statSet.stats[stat_id]
                print(f"    Stat ID {stat_id}: {stat_value}")

                # Try to find the stat in skillStatMap
                if stat_id in stat_map:
                    print(f"      -> Mapped to: {stat_map[stat_id]}")

        # Check baseFlags
        if hasattr(statSet, 'baseFlags'):
            print(f"  Base Flags:")
            for flag_key in statSet.baseFlags.keys():
                print(f"    {flag_key}: {statSet.baseFlags[flag_key]}")

# Check Gems.lua data for this gem
print("\n" + "="*80)
print("=== Gems.lua Data ===")
print("="*80)

gems = lua.globals().data.gems
gem_name = "Pain Offering"
if hasattr(gems, gem_name) or gem_name in gems:
    gem_data = gems[gem_name]
    print(f"\nGem '{gem_name}' found in gems table")
    print(f"Fields:")
    for key in gem_data.keys():
        print(f"  {key}: {gem_data[key]}")
else:
    print(f"\nGem '{gem_name}' not found in gems table")
    print("\nSearching for gems with 'Pain' or 'Offering'...")
    for gem_key in list(gems.keys())[:50]:  # Check first 50
        if 'Pain' in str(gem_key) or 'Offering' in str(gem_key):
            print(f"  Found: {gem_key}")

print("\n" + "="*80)
