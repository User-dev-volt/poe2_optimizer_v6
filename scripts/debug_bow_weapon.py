from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.integration.test_story_2_9_1_phase1_weapons import load_build_from_xml, FIXTURES_DIR

# Load the bow build
build = load_build_from_xml(FIXTURES_DIR / 'deadeye_lightning_arrow_76.xml')

print('\n' + '='*70)
print('BOW WEAPON DEBUG')
print('='*70)

if build.items:
    for item in build.items:
        print(f"\nItem: {item.name}")
        print(f"  Slot: {item.slot}")
        print(f"  Rarity: {item.rarity}")
        print(f"\n  Stats:")
        for key, value in item.stats.items():
            print(f"    {key}: {value}")
else:
    print("\nNo items found!")

print('='*70)
