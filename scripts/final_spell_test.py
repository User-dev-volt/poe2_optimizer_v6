"""Final test to understand spell calculation status"""

from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.calculator.build_calculator import calculate_build_stats
from tests.integration.test_epic2_validation import load_build_from_xml

# Test spell build
print("=" * 70)
print("FINAL SPELL TEST - witch_frost_mage_91")
print("=" * 70)

spell_build_path = Path("tests/fixtures/realistic_builds/witch_frost_mage_91.xml")
spell_build = load_build_from_xml(spell_build_path)

print(f"\nBuild Info:")
print(f"  Name: {spell_build.build_name}")
print(f"  Class: {spell_build.character_class.value}, Level: {spell_build.level}")
print(f"  Skills: {[f'{s.name} (ID: {s.skill_id})' for s in spell_build.skills if s.enabled]}")
print(f"  Allocated nodes: {len(spell_build.passive_nodes)}")

# Calculate with hybrid routing
print(f"\nCalculating...")
try:
    stats = calculate_build_stats(spell_build)

    print(f"\nResults:")
    print(f"  ✓ Calculation succeeded!")
    print(f"  DPS: {stats.total_dps:.2f}")
    print(f"  Life: {stats.life}")
    print(f"  Energy Shield: {stats.energy_shield}")
    print(f"  Mana: {stats.mana}")

    if stats.total_dps > 0:
        print(f"\n{'='*70}")
        print(f"SUCCESS: Spell build produced DPS = {stats.total_dps:.2f}")
        print(f"{'='*70}")
    else:
        print(f"\n{'='*70}")
        print(f"ISSUE: Spell build returned DPS = 0")
        print(f"This confirms spells need additional MinimalCalc.lua work")
        print(f"{'='*70}")

except Exception as e:
    print(f"\n{'='*70}")
    print(f"ERROR: Calculation failed")
    print(f"Exception: {e}")
    print(f"{'='*70}")
