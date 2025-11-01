"""Debug DPS calculation in detail."""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.parsers.pob_parser import parse_pob_code
from src.calculator.build_calculator import calculate_build_stats

# Load the Witch L1 build
build_path = project_root / "tests" / "fixtures" / "parity_builds" / "build_07_witch_01.txt"
with open(build_path, 'r', encoding='utf-8') as f:
    pob_code = f.read()

print("Parsing PoB code...")
build_data = parse_pob_code(pob_code)

print(f"Character: {build_data.character_class}, Level: {build_data.level}")
print(f"Passive nodes: {len(build_data.passive_nodes) if build_data.passive_nodes else 0}")

print("\nCalculating stats...")
stats = calculate_build_stats(build_data)

print("\n=== OUR CALCULATION RESULTS ===")
print(f"TotalDPS: {stats.total_dps}")
print(f"Life: {stats.life}")
print(f"Mana: {stats.mana}")
print(f"Energy Shield: {stats.energy_shield}")
print(f"Evasion: {stats.evasion}")

print("\n=== EXPECTED (from PoB GUI) ===")
print("TotalDPS: 0.183183")
print("Life: 65")
print("Mana: 67")
print("Evasion: 30")
print("HitChance: 13%")

print("\n=== ANALYSIS ===")
if stats.total_dps > 0.183183:
    ratio = stats.total_dps / 0.183183
    print(f"Our DPS is {ratio:.1f}x higher than expected")
    print(f"If hit chance (13%) were missing, we'd expect {ratio:.1f}x = ~7.7x error")
    print(f"Actual error suggests hit chance ~100% instead of ~13%")

print("\nDone!")
