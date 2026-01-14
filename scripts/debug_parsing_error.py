#!/usr/bin/env python3
"""
Debug the 'list' object has no attribute 'get' error
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.integration.test_story_2_9_1_phase1_weapons import load_build_from_xml
import traceback

def test_problematic_builds():
    """Test builds that are throwing parsing errors"""

    problem_builds = [
        "lich_storm_mage_90.xml",
        "titan_infernal_cry_72.xml",
    ]

    for filename in problem_builds:
        print(f"\n{'='*80}")
        print(f"Testing: {filename}")
        print('='*80)

        fixture_path = Path(__file__).parent.parent / "tests" / "fixtures" / "realistic_builds" / filename

        try:
            build = load_build_from_xml(fixture_path)
            print(f"[OK] Build loaded successfully")
            print(f"  Skills: {len(build.skills)}")
            print(f"  Main socket group: {build.main_socket_group}")

        except Exception as e:
            print(f"[FAIL] Error loading build:")
            print(f"  Error type: {type(e).__name__}")
            print(f"  Error message: {str(e)}")
            print(f"\nFull traceback:")
            traceback.print_exc()

if __name__ == "__main__":
    test_problematic_builds()
