"""Test with first 2 skills from PoB XML."""

from src.parsers.xml_utils import parse_xml
from src.parsers.pob_parser import _extract_character_class, _extract_level, _extract_passive_nodes, _extract_skills, _extract_items, _extract_config
from src.models.build_data import BuildData

# Load PoB build
build_path = "tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml"
with open(build_path, "r", encoding="utf-8") as f:
    xml_content = f.read()

pob_data = parse_xml(xml_content)
pob_section = pob_data.get("PathOfBuilding2", {})

# Extract components
build_section = pob_section.get("Build", {})
char_class = _extract_character_class(build_section)
level = _extract_level(build_section)
passive_nodes = _extract_passive_nodes(pob_section)
all_skills = _extract_skills(pob_section)
items = _extract_items(pob_data)
config = _extract_config(pob_section)

# Test with just 2 skills
build = BuildData(
    character_class=char_class,
    level=level,
    passive_nodes=passive_nodes,
    skills=all_skills[:2],  # Only first 2 skills
    items=items,
    config=config
)

print(f"Testing with {len(build.skills)} skills from PoB XML...")
print(f"  Skill 1: {build.skills[0].name} ({build.skills[0].skill_id})")
print(f"  Skill 2: {build.skills[1].name} ({build.skills[1].skill_id})")

from src.calculator.build_calculator import calculate_build_stats

try:
    stats = calculate_build_stats(build)
    print(f"\nSUCCESS! DPS={stats.total_dps:.2f}, Life={stats.life}")
except Exception as e:
    print(f"\nFAILED: {e}")
    if "pairs" in str(e):
        print("⚠️ Same Common.lua:408 error - not quantity related")
