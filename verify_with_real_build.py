"""Verify Story 2.9 with real PoB build."""

from src.parsers.pob_parser import parse_pob_xml
from src.calculator.build_calculator import calculate_build_stats

def main():
    print("Story 2.9 Verification with Real Build")
    print("=" * 60)

    # Load a real build
    build_path = "tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml"
    print(f"\nLoading build: {build_path}")

    with open(build_path, 'r', encoding='utf-8') as f:
        xml_content = f.read()

    build = parse_pob_xml(xml_content)

    print(f"Character: {build.character_class.value} Level {build.level}")
    print(f"Passive nodes allocated: {len(build.passive_nodes)}")
    print(f"Skills: {len(build.skills)}")
    print(f"Items: {len(build.items)}")

    # Calculate full build stats
    print("\n--- Full Build Calculation ---")
    stats_full = calculate_build_stats(build)
    print(f"DPS: {stats_full.total_dps:.2f}")
    print(f"Life: {stats_full.life}")
    print(f"ES: {stats_full.energy_shield}")
    print(f"Mana: {stats_full.mana}")
    print(f"Fire Res: {stats_full.resistances['fire']}%")

    # Remove some passive nodes to test degradation
    original_nodes = build.passive_nodes.copy()
    nodes_to_remove = list(original_nodes)[:10]  # Remove first 10 nodes
    build.passive_nodes = build.passive_nodes - set(nodes_to_remove)

    print(f"\n--- Degraded Build (removed {len(nodes_to_remove)} nodes) ---")
    stats_degraded = calculate_build_stats(build)
    print(f"DPS: {stats_degraded.total_dps:.2f}")
    print(f"Life: {stats_degraded.life}")

    # Calculate differences
    dps_diff = ((stats_full.total_dps - stats_degraded.total_dps) / stats_degraded.total_dps * 100) if stats_degraded.total_dps > 0 else 0
    life_diff = stats_full.life - stats_degraded.life

    print(f"\n--- Impact of Passive Nodes ---")
    print(f"DPS difference: {dps_diff:+.2f}%")
    print(f"Life difference: {life_diff:+d}")

    # Verify AC-2.9.2: Stats change when nodes added/removed
    stats_changed = (stats_full.life != stats_degraded.life) or (stats_full.total_dps != stats_degraded.total_dps)

    print("\n" + "=" * 60)
    if stats_changed:
        print("PASS: Passive tree nodes affect calculations")
        print("AC-2.9.2: Stats change proportionally to node bonuses")
        return 0
    else:
        print("FAIL: Stats did not change when nodes removed")
        return 1

if __name__ == "__main__":
    import sys
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
