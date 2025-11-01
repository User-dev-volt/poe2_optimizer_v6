"""Debug script to test Witch L1 calculation."""
import sys
sys.path.insert(0, "D:/poe2_optimizer_v6")

from src.parsers.pob_parser import parse_pob_code
from src.calculator.build_calculator import calculate_build_stats

# Read the Witch L1 PoB code
with open("D:/poe2_optimizer_v6/tests/fixtures/parity_builds/build_07_witch_01.txt", "r") as f:
    pob_code = f.read().strip()

print("Parsing PoB code...")
build = parse_pob_code(pob_code)

print(f"\nBuild parsed:")
print(f"  Class: {build.character_class}")
print(f"  Level: {build.level}")
print(f"  Passive nodes: {len(build.passive_nodes)}")

print("\nCalculating stats...")
try:
    stats = calculate_build_stats(build)

    print(f"\n=== OUR CALCULATED STATS ===")
    print(f"Life: {stats.life}")
    print(f"Mana: {stats.mana}")
    print(f"TotalDPS: {stats.total_dps}")
    print(f"EnergyShield: {stats.energy_shield}")
    print(f"Evasion: {stats.evasion}")
    print(f"Armour: {stats.armour}")

    # Print all available stats for debugging
    print(f"\n=== ALL AVAILABLE STATS ===")
    for attr in dir(stats):
        if not attr.startswith('_'):
            try:
                val = getattr(stats, attr)
                if not callable(val):
                    print(f"{attr}: {val}")
            except:
                pass

    print(f"\n=== EXPECTED (PoB GUI) ===")
    print(f"Life: 65")
    print(f"Mana: 67")
    print(f"TotalDPS: 0.183183")

    print(f"\n=== DISCREPANCIES ===")
    print(f"Life error: {stats.life} vs 65 ({((stats.life - 65) / 65 * 100):.1f}%)")
    print(f"Mana error: {stats.mana} vs 67 ({((stats.mana - 67) / 67 * 100):.1f}%)")
    if stats.total_dps > 0:
        print(f"DPS error: {stats.total_dps} vs 0.183183 ({((stats.total_dps - 0.183183) / 0.183183 * 100):.1f}%)")

except Exception as e:
    print(f"ERROR during calculation: {e}")
    import traceback
    traceback.print_exc()

print("\nDone.")
