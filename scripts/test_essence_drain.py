"""
Test witch_essence_drain_86 - DOT spell build
"""
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.calculator.build_calculator import calculate_build_stats
from tests.integration.test_story_2_9_1_phase1_weapons import load_build_from_xml

def test_essence_drain():
    """Test Essence Drain DOT spell build"""

    fixture_path = Path(__file__).parent.parent / "tests" / "fixtures" / "realistic_builds" / "witch_essence_drain_86.xml"

    if not fixture_path.exists():
        print(f"ERROR: Build fixture not found: {fixture_path}")
        return

    print(f"Loading build from: {fixture_path}")

    # Parse build
    build_data = load_build_from_xml(fixture_path)

    print("\n=== Build Info ===")
    print(f"Build name: {build_data.build_name}")
    print(f"Class: {build_data.character_class.value}")
    print(f"Level: {build_data.level}")
    print(f"Main Socket Group: {build_data.main_socket_group}")
    print(f"\nSkills extracted ({len(build_data.skills)} total):")
    for i, skill in enumerate(build_data.skills, 1):
        status = "ENABLED" if skill.enabled else "disabled"
        marker = " <-- SELECTED" if i == build_data.main_socket_group else ""
        print(f"  {i}. {skill.name:25} [{status}]{marker}")

    # Calculate with hybrid routing
    print("\n=== Calculating Build ===")
    print("(Check debug output for DOT spell detection and base damage)")

    result = calculate_build_stats(build_data)

    print("\n=== Results ===")
    print(f"Life: {result.life}")
    print(f"Energy Shield: {result.energy_shield}")
    print(f"Total DPS: {result.total_dps}")

    # Check if spell detection worked
    if result.total_dps > 0:
        print("\n[SUCCESS] Essence Drain DOT spell DPS > 0!")
        print(f"   DPS = {result.total_dps}")
    else:
        print("\n[NOTE] Essence Drain DOT spell DPS = 0")
        print("   DOT calculation may require additional implementation (Task 2.5-2.6)")

    return result

if __name__ == "__main__":
    test_essence_drain()
