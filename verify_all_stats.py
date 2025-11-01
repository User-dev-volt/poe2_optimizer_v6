"""Verify all Witch L1 stats - ASCII only output."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.parsers.pob_parser import parse_pob_code
from src.calculator.build_calculator import calculate_build_stats

fixtures_dir = Path(__file__).parent / "tests" / "fixtures" / "parity_builds"
witch_code = (fixtures_dir / "build_07_witch_01.txt").read_text().strip()

build = parse_pob_code(witch_code)
stats = calculate_build_stats(build)

print("\n=== WITCH L1 STATS VERIFICATION ===")
print(f"Life:         {stats.life} (expected: 65)")
print(f"Mana:         {stats.mana} (expected: 67)")
print(f"Evasion:      {stats.evasion} (expected: 30)")
print(f"Fire Resist:  {stats.fire_resist}% (expected: -50%)")
print(f"Cold Resist:  {stats.cold_resist}% (expected: -50%)")
print(f"Lightning:    {stats.lightning_resist}% (expected: -50%)")
print(f"Total DPS:    {stats.total_dps:.6f} (expected: 0.183183)")

# Check tolerances
checks = {
    "Life": abs(stats.life - 65) <= 0.1,
    "Mana": abs(stats.mana - 67) <= 0.1,
    "Evasion": abs(stats.evasion - 30) <= 0.1,
    "Fire Resist": abs(stats.fire_resist - (-50)) <= 0.1,
    "Cold Resist": abs(stats.cold_resist - (-50)) <= 0.1,
    "Lightning Resist": abs(stats.lightning_resist - (-50)) <= 0.1,
    "Total DPS": abs(stats.total_dps - 0.183183) <= 0.001
}

print("\n=== TOLERANCE CHECK (0.1%) ===")
for stat, passed in checks.items():
    status = "PASS" if passed else "FAIL"
    print(f"{stat:20s}: {status}")

all_pass = all(checks.values())
print(f"\n=== OVERALL: {'ALL PASS' if all_pass else 'FAILURES DETECTED'} ===")
sys.exit(0 if all_pass else 1)
