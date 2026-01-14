#!/usr/bin/env python3
"""
Test script for ritualist_lightning_spear_96 build
Investigates Global.lua:118 error reported in status report
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.calculator.build_calculator import calculate_build_stats
from tests.integration.test_story_2_9_1_phase1_weapons import load_build_from_xml

def test_ritualist_lightning_spear():
    """Test ritualist_lightning_spear_96 build to reproduce Global.lua:118 error"""
    fixture_path = Path(__file__).parent.parent / "tests" / "fixtures" / "realistic_builds" / "ritualist_lightning_spear_96.xml"

    print("\n" + "="*80)
    print("Testing: ritualist_lightning_spear_96")
    print("="*80)

    if not fixture_path.exists():
        print(f"ERROR: Build fixture not found: {fixture_path}")
        return False

    # Parse build
    print("\n[1] Parsing build XML...")
    build = load_build_from_xml(fixture_path)
    print(f"[OK] Build parsed successfully")
    print(f"  Character: {build.character_class} Level {build.level}")
    print(f"  mainSocketGroup: {build.main_socket_group}")
    print(f"  Total skills: {len(build.skills)}")

    # Show all skills
    print(f"\n[2] Skills in build:")
    for i, skill in enumerate(build.skills, 1):
        print(f"  {i}. {skill.name} (enabled={skill.enabled})")

    # Show selected main skill
    if 1 <= build.main_socket_group <= len(build.skills):
        main_skill = build.skills[build.main_socket_group - 1]
        print(f"\n[3] Selected main skill (group {build.main_socket_group}): {main_skill.name}")
    else:
        print(f"\n[3] WARNING: mainSocketGroup {build.main_socket_group} out of range!")

    # Attempt calculation
    print(f"\n[4] Attempting calculation...")
    try:
        stats = calculate_build_stats(build)
        print(f"[OK] Calculation successful!")
        print(f"\n[5] Results:")
        print(f"  Total DPS: {stats.total_dps}")
        print(f"  Life: {stats.life}")
        print(f"  ES: {stats.energy_shield}")
        print(f"  Mana: {stats.mana}")

        if stats.total_dps > 0:
            print(f"\n[SUCCESS] Build produces DPS > 0")
        else:
            print(f"\n[WARNING] Build produces DPS = 0 (check logs for disableReason)")

    except Exception as e:
        print(f"[FAIL] Calculation FAILED with error:")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Error message: {str(e)}")

        # Check if this is the Global.lua:118 error
        if "Global.lua:118" in str(e) or "arithmetic on local 'result'" in str(e):
            print(f"\n[CONFIRMED] Global.lua:118 error reproduced!")
            print(f"  This is the error mentioned in status report")

        import traceback
        print(f"\n[DEBUG] Full traceback:")
        traceback.print_exc()

        return False

    return True

if __name__ == "__main__":
    success = test_ritualist_lightning_spear()
    sys.exit(0 if success else 1)
