#!/usr/bin/env python3
"""
Test warrior_ballista_93 build
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.calculator.build_calculator import calculate_build_stats
from tests.integration.test_story_2_9_1_phase1_weapons import load_build_from_xml

def test_warrior_ballista():
    """Test warrior_ballista_93 build"""

    fixture_path = Path(__file__).parent.parent / "tests" / "fixtures" / "realistic_builds" / "warrior_ballista_93.xml"

    print("="*80)
    print("Testing: warrior_ballista_93")
    print("="*80)

    # Parse build
    build = load_build_from_xml(fixture_path)

    print(f"\nBuild info (before override):")
    print(f"  Character: {build.character_class} Level {build.level}")
    print(f"  mainSocketGroup from XML: {build.main_socket_group}")
    print(f"  Total skills: {len(build.skills)}")

    # Override mainSocketGroup to 1 to select Siege Ballista (Story 2.9.2)
    build.main_socket_group = 1
    print(f"  mainSocketGroup OVERRIDE: {build.main_socket_group} (to test Siege Ballista)")

    print(f"\nSkills:")
    for i, skill in enumerate(build.skills, 1):
        marker = " <-- SELECTED" if i == build.main_socket_group else ""
        print(f"  {i}. {skill.name:30} (level {skill.level:2}, {len(skill.support_gems)} supports){marker}")

    # Calculate
    print(f"\nAttempting calculation...")
    try:
        stats = calculate_build_stats(build)
        print(f"[OK] Calculation successful")
        print(f"\nResults:")
        print(f"  Total DPS: {stats.total_dps}")
        print(f"  Life: {stats.life}")
        print(f"  ES: {stats.energy_shield}")
        print(f"  Mana: {stats.mana}")

        if stats.total_dps > 0:
            print(f"\n[SUCCESS] Build produces DPS > 0")
        else:
            print(f"\n[WARNING] Build produces DPS = 0")
            print(f"  Check MinimalCalc logs for disableReason")

    except Exception as e:
        print(f"[FAIL] Calculation failed:")
        print(f"  Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_warrior_ballista()
