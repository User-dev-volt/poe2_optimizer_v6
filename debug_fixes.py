"""Debug script to test PoE 2 calculation fixes"""
import sys
sys.path.insert(0, 'D:\\poe2_optimizer_v6')

from src.parsers.xml_utils import parse_xml
from src.parsers.pob_parser import _extract_config, _extract_character_class, _extract_level, _extract_passive_nodes, _extract_items, _extract_skills, _extract_tree_version
from src.models.build_data import BuildData
from src.calculator.build_calculator import calculate_build_stats

# Load Witch Level 1 build from XML
with open('tests/fixtures/parity_builds/build_07_witch_01.xml', 'r', encoding='utf-8') as f:
    xml_str = f.read()

# Parse XML
data = parse_xml(xml_str)
pob_root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
build_section = pob_root.get("Build")

# Extract and build
build = BuildData(
    character_class=_extract_character_class(build_section),
    level=_extract_level(build_section),
    ascendancy=build_section.get("@ascendClassName"),
    passive_nodes=_extract_passive_nodes(pob_root),
    items=_extract_items(pob_root),
    skills=_extract_skills(pob_root),
    tree_version=_extract_tree_version(pob_root),
    build_name=build_section.get("@buildName"),
    notes=pob_root.get("Notes"),
    config=_extract_config(pob_root)
)

print(f"Build loaded: {build.character_class} Level {build.level}")

stats = calculate_build_stats(build)

print("\n=== CALCULATED STATS ===")
print(f"Life: {stats.life} (expected: 65)")
print(f"Mana: {stats.mana} (expected: 67)")
print(f"Evasion: {stats.evasion} (expected: 30)")
print(f"Total DPS: {stats.total_dps} (expected: 0.183)")
print(f"Fire Resist: {stats.fire_resist} (expected: -50)")
print(f"Cold Resist: {stats.cold_resist} (expected: -50)")
print(f"Lightning Resist: {stats.lightning_resist} (expected: -50)")

print("\n=== ERRORS ===")
print(f"Life error: {abs(stats.life - 65) / 65 * 100:.2f}%")
print(f"Mana error: {abs(stats.mana - 67) / 67 * 100:.2f}%")
print(f"Evasion error: {abs(stats.evasion - 30) / 30 * 100:.2f}%")
print(f"DPS error: {abs(stats.total_dps - 0.183) / 0.183 * 100:.2f}%")
print(f"Fire Resist error: {abs(stats.fire_resist - (-50))}%")
