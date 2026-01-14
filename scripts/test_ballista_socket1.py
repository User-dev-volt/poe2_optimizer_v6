#!/usr/bin/env python3
"""Test warrior_ballista with mainSocketGroup=1 (Siege Ballista)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.calculator.build_calculator import calculate_build_stats
from tests.integration.test_story_2_9_1_phase1_weapons import load_build_from_xml

fixture_path = Path(__file__).parent.parent / "tests" / "fixtures" / "realistic_builds" / "warrior_ballista_93.xml"

print("Testing warrior_ballista_93 with mainSocketGroup=1 (Siege Ballista)")
print("="*80)

# Load and override mainSocketGroup
build = load_build_from_xml(fixture_path)
print(f"Original mainSocketGroup: {build.main_socket_group}")
print(f"Skill 1: {build.skills[0].name}")
print(f"Skill 2: {build.skills[1].name}")

# Override to socket group 1 (Siege Ballista)
from dataclasses import replace
build = replace(build, main_socket_group=1)
print(f"Overridden mainSocketGroup: {build.main_socket_group}")

print("\nCalculating...")
try:
    stats = calculate_build_stats(build)
    print(f"\nResults:")
    print(f"  Total DPS: {stats.total_dps}")
    print(f"  Life: {stats.life}")
    print(f"  ES: {stats.energy_shield}")

    if stats.total_dps > 0:
        print(f"\n[SUCCESS] Totem produces DPS > 0!")
    else:
        print(f"\n[FAIL] Totem still produces DPS = 0")
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
