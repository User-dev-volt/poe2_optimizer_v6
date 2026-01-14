"""
Debug script to show ALL skills in a build and their types
Helps identify which skill is actually the damaging spell
"""
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.calculator.pob_engine import PoBCalculationEngine
from tests.integration.test_story_2_9_1_phase1_weapons import load_build_from_xml

def inspect_all_skills(build_xml_path):
    """Load a build and inspect ALL skills to find spells"""

    build = load_build_from_xml(Path(build_xml_path))

    print(f"\n{'='*70}")
    print(f"Build: {build.build_name}")
    print(f"{'='*70}\n")

    print(f"Total skills: {len(build.skills)}")

    for idx, skill in enumerate(build.skills):
        print(f"\n--- Skill {idx+1}: {skill.name} (ID: {skill.skill_id}) ---")
        print(f"  Enabled: {skill.enabled}")
        if hasattr(skill, 'slot'):
            print(f"  Slot: {skill.slot}")
        if hasattr(skill, 'gems') and skill.gems:
            print(f"  Gems: {len(skill.gems)}")
            for gem in skill.gems:
                gem_name = getattr(gem, 'name', 'Unknown')
                gem_level = getattr(gem, 'level', '?')
                print(f"    - {gem_name} (Level {gem_level})")

if __name__ == "__main__":
    # Test multiple builds to find one with a real damaging spell
    builds_to_test = [
        "tests/fixtures/realistic_builds/bloodmage_remnants_95.xml",
        "tests/fixtures/realistic_builds/witch_frost_mage_91.xml",
        "tests/fixtures/realistic_builds/gemling_frost_mage_100.xml",
    ]

    for build_path in builds_to_test:
        try:
            inspect_all_skills(build_path)
        except Exception as e:
            print(f"\nERROR loading {build_path}: {e}")
