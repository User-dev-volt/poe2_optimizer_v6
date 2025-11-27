"""Test DPS calculation with real PoB build (Story 2.9 Milestone 4)."""

from src.parsers.pob_parser import parse_pob_code

# Load a real PoB build
build_path = "tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml"
print(f"Loading build: {build_path}\n")

with open(build_path, "r", encoding="utf-8") as f:
    xml_content = f.read()

# PoB XML files need to be base64 encoded and compressed to be parsed by parse_pob_code
# Instead, let's use parse_xml directly
from src.parsers.xml_utils import parse_xml
from src.parsers.pob_parser import _extract_character_class, _extract_level, _extract_passive_nodes, _extract_skills, _extract_items, _extract_config
from src.models.build_data import BuildData

pob_data = parse_xml(xml_content)
pob_section = pob_data.get("PathOfBuilding2", {})

# Extract all build components
build_section = pob_section.get("Build", {})
char_class = _extract_character_class(build_section)
level = _extract_level(build_section)
passive_nodes = _extract_passive_nodes(pob_section)
skills = _extract_skills(pob_section)
items = _extract_items(pob_data)
config = _extract_config(pob_section)

ascendancy = None  # Can extract if needed

build = BuildData(
    character_class=char_class,
    level=level,
    ascendancy=ascendancy,
    passive_nodes=passive_nodes,
    skills=skills,
    items=items,
    config=config
)

print(f"Character: {build.character_class.value} Level {build.level}")
print(f"Passive nodes: {len(build.passive_nodes)}")
print(f"Skills: {len(build.skills)}")
print(f"Items: {len(build.items)}\n")

# Show parsed weapon
weapons = [item for item in build.items if "Weapon" in item.slot]
if weapons:
    weapon = weapons[0]
    print(f"Weapon: {weapon.name} ({weapon.stats.get('base_type', 'Unknown')})")
    print(f"  Phys Damage: {weapon.stats.get('phys_min', 0)}-{weapon.stats.get('phys_max', 0)}")
    print(f"  Lightning Damage: {weapon.stats.get('lightning_min', 0)}-{weapon.stats.get('lightning_max', 0)}")
    print(f"  Attack Speed Inc: {weapon.stats.get('attack_speed_inc', 0)}%\n")

# Calculate stats
from src.calculator.build_calculator import calculate_build_stats

try:
    stats = calculate_build_stats(build)

    print("=== CALCULATION RESULTS ===")
    print(f"DPS: {stats.total_dps:.2f}")
    print(f"Life: {stats.life}")
    print(f"Energy Shield: {stats.energy_shield}")
    print(f"Mana: {stats.mana}")
    print(f"Fire Res: {stats.resistances.get('fire', 0)}%")
    print(f"Cold Res: {stats.resistances.get('cold', 0)}%")
    print(f"Lightning Res: {stats.resistances.get('lightning', 0)}%")

    print("\n*** SUCCESS! DPS > 0 means items are loaded and working! ***")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
