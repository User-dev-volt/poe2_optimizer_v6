"""Test if selItemId fix resolves weaponData1.type issue."""

from src.parsers.xml_utils import parse_xml
from src.parsers.pob_parser import _extract_character_class, _extract_level, _extract_passive_nodes, _extract_skills, _extract_items, _extract_config
from src.models.build_data import BuildData
from src.calculator.pob_engine import PoBCalculationEngine

# Use realistic build from fixtures
build_path = r"tests\fixtures\realistic_builds\deadeye_lightning_arrow_76.xml"

with open(build_path, 'r', encoding='utf-8') as f:
    xml_content = f.read()

# Parse XML and extract build components
pob_data = parse_xml(xml_content)
pob_section = pob_data.get("PathOfBuilding2", {})
build_section = pob_section.get("Build", {})

char_class = _extract_character_class(build_section)
level = _extract_level(build_section)
passive_nodes = _extract_passive_nodes(pob_section)
skills = _extract_skills(pob_section)
items = _extract_items(pob_data)
config = _extract_config(pob_section)

build = BuildData(
    character_class=char_class,
    level=level,
    ascendancy=None,
    passive_nodes=passive_nodes,
    skills=skills,
    items=items,
    config=config
)

print(f"Build: {build.character_class} L{build.level}")
print(f"Items: {len(build.items)}")
print(f"Skills: {len(build.skills)}")

# Calculate stats
engine = PoBCalculationEngine()
stats = engine.calculate(build)

print(f"\nResults:")
print(f"  DPS: {stats.total_dps:.1f}")
print(f"  Life: {stats.life:.0f}")
print(f"  EHP: {stats.effective_hp:.0f}")

# Check if DPS > 0 (success!)
if stats.total_dps > 0:
    print("\n✅ SUCCESS! DPS calculated correctly!")
    print("   weaponData1.type issue RESOLVED!")
else:
    print("\n❌ FAIL: DPS still 0")
    print("   Need further debugging")
