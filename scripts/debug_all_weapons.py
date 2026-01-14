from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.integration.test_story_2_9_1_phase1_weapons import load_build_from_xml, FIXTURES_DIR

builds = [
    ('Mace', 'warrior_earthquake_89.xml'),
    ('Spear L71', 'warrior_spear_71.xml'),
    ('Spear L45', 'warrior_spear_45.xml'),
    ('Bow', 'deadeye_lightning_arrow_76.xml')
]

weapon_bases = ['Bow', 'Mace', 'Maul', 'Spear', 'Sword', 'Axe', 'Staff', 'Wand', 'Sceptre', 'Dagger', 'Claw', 'Crossbow']

print('\n' + '='*70)
print('WEAPON phys_damage_inc DEBUG')
print('='*70)

for name, filename in builds:
    build = load_build_from_xml(FIXTURES_DIR / filename)
    print(f"\n{name} ({filename}):")

    if build.items:
        # Find the weapon by checking base_type
        weapon = None
        for item in build.items:
            base_type = item.stats.get('base_type', '')
            if any(wb in base_type for wb in weapon_bases):
                weapon = item
                break

        if weapon:
            print(f"  Weapon: {weapon.stats.get('base_type', 'Unknown')}")
            print(f"  phys_damage_inc: {weapon.stats.get('phys_damage_inc', 0)}")
            print(f"  phys_min: {weapon.stats.get('phys_min', 0)}")
            print(f"  phys_max: {weapon.stats.get('phys_max', 0)}")
        else:
            print("  No weapon found!")
    else:
        print("  No items found!")

print('='*70)
