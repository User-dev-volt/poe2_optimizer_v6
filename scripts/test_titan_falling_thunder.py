"""
Test titan_falling_thunder_99 build.
Story 2.9.2 - Determine expected DPS behavior for this spell build.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.calculator.build_calculator import calculate_build_stats
from tests.integration.test_story_2_9_1_phase1_weapons import load_build_from_xml

def test_titan_falling_thunder_99():
    """Test Falling Thunder spell build."""
    print("\n" + "="*80)
    print("Testing: titan_falling_thunder_99 (Falling Thunder - Spell)")
    print("="*80)

    build_file = project_root / "tests" / "fixtures" / "realistic_builds" / "titan_falling_thunder_99.xml"

    if not build_file.exists():
        print(f"[FAIL] Build file not found: {build_file}")
        return None

    # Parse build
    print("\n1. Parsing build XML...")
    try:
        build = load_build_from_xml(build_file)
        print(f"   [OK] Build loaded: Level {build.level}")
        print(f"   [OK] Main socket group: {build.main_socket_group}")
        print(f"   [OK] Total skills: {len(build.skills)}")

        print(f"\n   Skills:")
        for i, skill in enumerate(build.skills, 1):
            marker = " <-- SELECTED" if i == build.main_socket_group else ""
            print(f"     {i}. {skill.name} (level {skill.level}, {len(skill.support_gems)} supports){marker}")
    except Exception as e:
        print(f"   [FAIL] Parse error: {e}")
        import traceback
        traceback.print_exc()
        return None

    # Calculate stats
    print("\n2. Calculating build stats...")
    try:
        stats = calculate_build_stats(build)

        print(f"\n3. Results:")
        print(f"   DPS: {stats.total_dps:.2f}")
        print(f"   Life: {stats.life:.0f}")
        print(f"   ES: {stats.energy_shield:.0f}")
        print(f"   Mana: {stats.mana:.0f}")

        if stats.total_dps > 0:
            print(f"\n   [SUCCESS] Build produces DPS > 0")
            print(f"   Recommendation: Set should_have_dps=True in test")
            return True
        else:
            print(f"\n   [WARNING] DPS = 0")
            print(f"   Need to investigate: Is this a minion/buff build or calculation issue?")
            return False

    except Exception as e:
        print(f"\n   [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_titan_falling_thunder_99()
    if result is None:
        sys.exit(2)  # Error
    sys.exit(0 if result else 1)
