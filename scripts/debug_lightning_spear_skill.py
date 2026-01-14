#!/usr/bin/env python3
"""
Debug script to examine Lightning Spear skill data
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.integration.test_story_2_9_1_phase1_weapons import load_build_from_xml

def debug_lightning_spear_skill():
    """Examine the Lightning Spear skill in ritualist build"""
    fixture_path = Path(__file__).parent.parent / "tests" / "fixtures" / "realistic_builds" / "ritualist_lightning_spear_96.xml"

    if not fixture_path.exists():
        print(f"ERROR: Build fixture not found: {fixture_path}")
        return

    build = load_build_from_xml(fixture_path)

    print("="*80)
    print(f"Build: ritualist_lightning_spear_96")
    print(f"mainSocketGroup: {build.main_socket_group}")
    print(f"Total skills: {len(build.skills)}")
    print("="*80)

    # Lightning Spear is at position 10
    if build.main_socket_group <= len(build.skills):
        skill = build.skills[build.main_socket_group - 1]
        print(f"\n[Main Skill at position {build.main_socket_group}]")
        print(f"  Name: {skill.name}")
        print(f"  Enabled: {skill.enabled}")
        print(f"  Level: {skill.level}")
        print(f"  Supports ({len(skill.support_gems)}):")
        for support in skill.support_gems:
            if isinstance(support, dict):
                print(f"    - {support.get('name', 'Unknown')} (level {support.get('level', '?')})")
            else:
                print(f"    - {support.name} (level {support.level})")
    else:
        print(f"\nERROR: mainSocketGroup {build.main_socket_group} out of range")

    print(f"\n[All Skills]")
    for i, skill in enumerate(build.skills, 1):
        marker = " <-- SELECTED" if i == build.main_socket_group else ""
        print(f"  {i:2}. {skill.name:30} (level {skill.level:2}, {len(skill.support_gems)} supports){marker}")

if __name__ == "__main__":
    debug_lightning_spear_skill()
