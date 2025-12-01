"""Check Frost Bolt spell data for base damage"""

import sys
sys.path.insert(0, str(__file__).replace('scripts\\check_frost_bolt_data.py', ''))

from src.calculator.pob_engine import PoBCalculationEngine

# Initialize engine
engine = PoBCalculationEngine()
engine._ensure_initialized()
lua = engine._lua

# Check several direct damage spells
test_spells = [
    'FrostBoltPlayer',
    'BallLightningPlayer',
    'FrostWallPlayer',
    'FrostBombPlayer',
]

for spell_id in test_spells:
    if spell_id in lua.globals().data.skills:
        skill = lua.globals().data.skills[spell_id]
        print("="*80)
        print(f"=== {skill.name} ({spell_id}) ===")
        print("="*80)

        # Check level 20 data
        if hasattr(skill, 'levels') and 20 in skill.levels:
            level_20 = skill.levels[20]
            print(f"\nLevel 20 fields:")
            for key in level_20.keys():
                print(f"  {key}: {level_20[key]}")

        # Check statSets
        if hasattr(skill, 'statSets') and 1 in skill.statSets:
            statSet = skill.statSets[1]
            print(f"\nStatSet 1 stats:")
            if hasattr(statSet, 'stats'):
                for stat_id in statSet.stats.keys():
                    stat_name = statSet.stats[stat_id]
                    print(f"  Stat ID {stat_id}: {stat_name}")

        print("\n")
