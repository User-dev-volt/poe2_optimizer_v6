from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.integration.test_story_2_9_1_phase1_weapons import load_build_from_xml, calculate_build_stats, FIXTURES_DIR

builds = [
    ('Mace (warrior_earthquake_89)', 'warrior_earthquake_89.xml'),
    ('Spear L71 (warrior_spear_71)', 'warrior_spear_71.xml'),
    ('Spear L45 (warrior_spear_45)', 'warrior_spear_45.xml'),
    ('Bow (deadeye_lightning_arrow_76)', 'deadeye_lightning_arrow_76.xml')
]

print('\n' + '='*70)
print('PHASE 1 WEAPON BUILD VALIDATION - FINAL RESULTS')
print('='*70)
for name, filename in builds:
    build = load_build_from_xml(FIXTURES_DIR / filename)
    stats = calculate_build_stats(build)
    status = 'PASS (DPS > 0)' if stats.total_dps > 0 else 'FAIL (DPS = 0)'
    print(f'{name:40s} {stats.total_dps:8.2f} DPS  [{status}]')
print('='*70)
