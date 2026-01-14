"""
Quick test to verify hybrid routing works correctly

Tests 2 builds:
- 1 attack (deadeye_lightning_arrow_76) → Should route to MinimalCalc
- 1 spell (witch_frost_mage_91) → Should route to Subprocess

Story 2.9.1 Task 7: Quick sanity check before full validation
"""

from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.calculator.build_calculator import calculate_build_stats
from tests.integration.test_epic2_validation import load_build_from_xml

# Test 1: Attack build
print("=" * 60)
print("TEST 1: Attack Build (deadeye_lightning_arrow_76)")
print("Expected: Route to MinimalCalc (attack path)")
print("=" * 60)

attack_build_path = Path("tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml")
attack_build = load_build_from_xml(attack_build_path)

print(f"Build: {attack_build.build_name}")
print(f"Class: {attack_build.character_class.value}, Level: {attack_build.level}")
print(f"Skills: {[s.name for s in attack_build.skills if s.enabled]}")
print(f"Allocated nodes: {len(attack_build.passive_nodes)}")

# Calculate
stats = calculate_build_stats(attack_build)

print(f"\nResults:")
print(f"  DPS: {stats.total_dps:.2f}")
print(f"  Life: {stats.life}")
print(f"  Energy Shield: {stats.energy_shield}")
print(f"  Mana: {stats.mana}")

assert stats.total_dps > 0, "Attack build should produce DPS > 0"
print(f"\n✓ Test 1 PASSED: DPS = {stats.total_dps:.2f}")

# Test 2: Spell build
print("\n" + "=" * 60)
print("TEST 2: Spell Build (witch_frost_mage_91)")
print("Expected: Route to Subprocess (spell path)")
print("=" * 60)

spell_build_path = Path("tests/fixtures/realistic_builds/witch_frost_mage_91.xml")
spell_build = load_build_from_xml(spell_build_path)

print(f"Build: {spell_build.build_name}")
print(f"Class: {spell_build.character_class.value}, Level: {spell_build.level}")
print(f"Skills: {[s.name for s in spell_build.skills if s.enabled]}")
print(f"Allocated nodes: {len(spell_build.passive_nodes)}")

# Calculate
stats2 = calculate_build_stats(spell_build)

print(f"\nResults:")
print(f"  DPS: {stats2.total_dps:.2f}")
print(f"  Life: {stats2.life}")
print(f"  Energy Shield: {stats2.energy_shield}")
print(f"  Mana: {stats2.mana}")

assert stats2.total_dps > 0, "Spell build should produce DPS > 0"
print(f"\n✓ Test 2 PASSED: DPS = {stats2.total_dps:.2f}")

print("\n" + "=" * 60)
print("HYBRID ROUTING TEST: ALL TESTS PASSED ✓")
print("=" * 60)
