#!/usr/bin/env python3
"""
Test Siege Ballista (totem attack skill)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.calculator.build_calculator import calculate_build_stats
from tests.integration.test_story_2_9_1_phase1_weapons import load_build_from_xml

def test_siege_ballista():
    """Test Siege Ballista totem attack"""

    fixture_path = Path(__file__).parent.parent / "tests" / "fixtures" / "realistic_builds" / "warrior_ballista_93.xml"

    print("="*80)
    print("Testing: warrior_ballista_93 - Siege Ballista (totem attack)")
    print("="*80)

    build = load_build_from_xml(fixture_path)

    # Override to select Siege Ballista (position 1)
    build.main_socket_group = 1

    print(f"\nBuild info:")
    print(f"  Character: {build.character_class} Level {build.level}")
    print(f"  Main skill (group {build.main_socket_group}): {build.skills[build.main_socket_group - 1].name}")
    print(f"  Skill level: {build.skills[build.main_socket_group - 1].level}")
    print(f"  Supports: {len(build.skills[build.main_socket_group - 1].support_gems)}")

    # Calculate
    print(f"\nAttempting calculation...")
    stats = calculate_build_stats(build)

    print(f"\nResults:")
    print(f"  Total DPS: {stats.total_dps}")
    print(f"  Life: {stats.life}")

    if stats.total_dps > 0:
        print(f"\n[SUCCESS] Siege Ballista (totem attack) produces DPS > 0")
        print(f"  Totem attacks work automatically in PoB - no special totem code needed!")
    else:
        print(f"\n[WARNING] Siege Ballista DPS = 0")
        print(f"  Check logs for issues")

if __name__ == "__main__":
    test_siege_ballista()
