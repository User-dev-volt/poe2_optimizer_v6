#!/usr/bin/env python3
"""Debug script to examine totem build structure"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parsers.pob_parser import parse_build_from_file
from calculator.pob_engine import PoBCalculationEngine

# Load warrior_ballista build
build_path = Path(__file__).parent.parent / 'tests' / 'fixtures' / 'realistic_builds' / 'warrior_ballista_93.xml'
build = parse_build_from_file(str(build_path))

print(f"Build: {build.build_name}")
print(f"Class: {build.character_class}")
print(f"Level: {build.level}")
print(f"\nSkills ({len(build.skills)} total):")
for i, skill in enumerate(build.skills, 1):
    print(f"  {i}. {skill.gem_name} (enabled: {skill.enabled}, level: {skill.level})")

print(f"\nmainSocketGroup: {build.main_socket_group}")

# Try to calculate
print("\n" + "="*60)
print("Attempting calculation with PoB engine...")
print("="*60)

engine = PoBCalculationEngine()
try:
    result = engine.calculate(build)
    print(f"\nResult:")
    print(f"  TotalDPS: {result.total_dps}")
    print(f"  Life: {result.life}")
    print(f"  ES: {result.energy_shield}")
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
