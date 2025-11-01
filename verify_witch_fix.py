"""Quick verification that Witch L1 calculations are fixed."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.parsers.pob_parser import parse_pob_code
from src.calculator.build_calculator import calculate_build_stats

# Load Witch L1 build
fixtures_dir = Path(__file__).parent / "tests" / "fixtures" / "parity_builds"
witch_code = (fixtures_dir / "build_07_witch_01.txt").read_text().strip()

print("Parsing Witch L1 build...")
build = parse_pob_code(witch_code)
print(f"  Class: {build.character_class}, Level: {build.level}")

print("\nCalculating stats...")
try:
    stats = calculate_build_stats(build)

    print(f"\n✓ Calculation completed successfully!")
    print(f"\nResults:")
    print(f"  Life: {stats.life} (expected: 65)")
    print(f"  Mana: {stats.mana} (expected: 67)")
    print(f"  Evasion: {stats.evasion} (expected: 30)")
    print(f"  Fire Resist: {stats.fire_resist}% (expected: -50%)")
    print(f"  Total DPS: {stats.total_dps:.6f} (expected: 0.183183)")

    # Check if within tolerance
    life_ok = abs(stats.life - 65) <= 0.1
    mana_ok = abs(stats.mana - 67) <= 0.1
    evasion_ok = abs(stats.evasion - 30) <= 0.1
    resist_ok = abs(stats.fire_resist - (-50)) <= 0.1
    dps_ok = abs(stats.total_dps - 0.183183) <= 0.001

    print(f"\nVerification:")
    print(f"  Life: {'✓ PASS' if life_ok else '✗ FAIL'}")
    print(f"  Mana: {'✓ PASS' if mana_ok else '✗ FAIL'}")
    print(f"  Evasion: {'✓ PASS' if evasion_ok else '✗ FAIL'}")
    print(f"  Fire Resist: {'✓ PASS' if resist_ok else '✗ FAIL'}")
    print(f"  Total DPS: {'✓ PASS' if dps_ok else '✗ FAIL'}")

    if all([life_ok, mana_ok, evasion_ok, resist_ok, dps_ok]):
        print(f"\n🎉 ALL CHECKS PASSED - Full parity achieved!")
        sys.exit(0)
    else:
        print(f"\n⚠️ Some checks failed - review needed")
        sys.exit(1)

except Exception as e:
    print(f"\n✗ Calculation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
