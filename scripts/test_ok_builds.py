"""
Test the builds marked as [OK] in audit to verify they actually produce DPS > 0
"""
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.calculator.build_calculator import calculate_build_stats
from tests.integration.test_story_2_9_1_phase1_weapons import load_build_from_xml

# Builds marked as [OK] in audit (excluding 4 weapon builds already tested)
OK_BUILDS = [
    "warrior_ballista_93",          # Siege Ballista
    "ritualist_lightning_spear_96", # Lightning Spear (spell)
    "titan_falling_thunder_99",     # Falling Thunder (spell)
]

def test_build(build_name: str):
    """Test a single build."""
    fixture_path = project_root / "tests" / "fixtures" / "realistic_builds" / f"{build_name}.xml"

    if not fixture_path.exists():
        print(f"ERROR: {build_name}.xml not found")
        return None

    build_data = load_build_from_xml(fixture_path)

    # Show main skill
    main_skill = build_data.skills[build_data.main_socket_group - 1] if build_data.main_socket_group <= len(build_data.skills) else None
    main_skill_name = main_skill.name if main_skill else "Unknown"

    # Calculate
    result = calculate_build_stats(build_data)

    return {
        "build": build_name,
        "main_skill": main_skill_name,
        "main_socket_group": build_data.main_socket_group,
        "dps": result.total_dps,
        "life": result.life,
        "success": result.total_dps > 0
    }

def main():
    """Test all OK builds."""
    print("=" * 80)
    print("Testing [OK] builds from audit")
    print("=" * 80)
    print()

    results = []
    for build_name in OK_BUILDS:
        print(f"Testing {build_name}...")
        result = test_build(build_name)
        if result:
            results.append(result)
            status = "[SUCCESS]" if result['success'] else "[FAILED]"
            print(f"  {status} {result['main_skill']}: DPS = {result['dps']:.2f}")
        print()

    print("=" * 80)
    print("Summary:")
    print("=" * 80)
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    print(f"  {success_count}/{total_count} builds producing DPS > 0")

    if success_count < total_count:
        print("\nFailed builds:")
        for r in results:
            if not r['success']:
                print(f"  - {r['build']}: {r['main_skill']} (mainSocketGroup={r['main_socket_group']})")

if __name__ == "__main__":
    main()
