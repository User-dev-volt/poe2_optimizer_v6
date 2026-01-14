"""Debug script to examine skill flags in PoB data"""

import sys
sys.path.insert(0, 'src')

from calculator.pob_engine import PoBCalculationEngine

# Initialize engine
engine = PoBCalculationEngine()
engine._ensure_initialized()
lua = engine._lua

# Get skills data
skills = lua.globals().data.skills

# Sample a few skills to understand the structure
print("=== Sample Skill Flags ===\n")

sample_skills = [
    "LightningArrowPlayer",  # Attack skill
    "FrostBoltPlayer",  # Spell skill
    "ExplosiveSpearPlayer",  # Attack skill (spear)
    "BallLightningPlayer",  # Spell skill
]

for skill_id in sample_skills:
    skill = skills[skill_id] if skill_id in skills else None
    if skill:
        print(f"\n{skill_id}:")
        print(f"  Name: {skill.name}")

        # Check skillTypes
        if hasattr(skill, 'skillTypes'):
            skill_types = []
            for st in skill.skillTypes.keys():
                skill_types.append(str(st))
            print(f"  skillTypes: {skill_types}")

        # Check baseFlags from first statSet
        if hasattr(skill, 'statSets') and len(skill.statSets) > 0:
            first_statset = list(skill.statSets.values())[0]
            if hasattr(first_statset, 'baseFlags'):
                flags = []
                for flag in first_statset.baseFlags.keys():
                    flags.append(str(flag))
                print(f"  baseFlags: {flags}")
    else:
        print(f"\n{skill_id}: NOT FOUND")

print("\n=== All Available Skill IDs (first 20) ===")
count = 0
for skill_id in skills.keys():
    print(f"  - {skill_id}")
    count += 1
    if count >= 20:
        break
