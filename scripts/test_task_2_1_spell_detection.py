"""
Test Task 2.1: Debug spell base damage extraction and detection
Tests witch_frost_mage_91 to verify spell detection logic works
"""
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.calculator.build_calculator import calculate_build_stats
from tests.integration.test_story_2_9_1_phase1_weapons import load_build_from_xml

def test_spell_detection():
    """Test spell detection and base damage extraction"""

    # Load witch_frost_mage_91 build (mainSocketGroup=2)
    fixture_path = Path(__file__).parent.parent / "tests" / "fixtures" / "realistic_builds" / "witch_frost_mage_91.xml"

    if not fixture_path.exists():
        print(f"ERROR: Build fixture not found: {fixture_path}")
        return

    print(f"Loading build from: {fixture_path}")

    # Parse build using updated loader (which now extracts mainSocketGroup)
    print("\n=== Parsing Build ===")
    build_data = load_build_from_xml(fixture_path)
    print(f"Build name: {build_data.build_name}")
    print(f"Class: {build_data.character_class.value}")
    print(f"Level: {build_data.level}")
    print(f"Main Socket Group: {build_data.main_socket_group}")  # Story 2.9.2: Verify correct skill selection
    print(f"Skills: {[s.name for s in build_data.skills if s.enabled]}")

    # Calculate with hybrid routing
    print("\n=== Calculating Build ===")
    print("(Check debug output for spell detection messages)")

    result = calculate_build_stats(build_data)

    print("\n=== Results ===")
    print(f"Life: {result.life}")
    print(f"Energy Shield: {result.energy_shield}")
    print(f"Total DPS: {result.total_dps}")

    # Check if spell detection worked
    if result.total_dps > 0:
        print("\n[SUCCESS] Spell DPS > 0")
        print(f"   DPS = {result.total_dps}")
    else:
        print("\n[FAILED] Spell DPS = 0")
        print("   Spell base damage extraction not working correctly")

        # Additional diagnostics
        if hasattr(result, 'main_skill_name'):
            print(f"   Main skill: {result.main_skill_name}")

    return result

if __name__ == "__main__":
    test_spell_detection()
