"""Test each PoB skill individually to find problematic one."""

from src.parsers.xml_utils import parse_xml
from src.parsers.pob_parser import _extract_character_class, _extract_level, _extract_passive_nodes, _extract_skills, _extract_items, _extract_config
from src.models.build_data import BuildData
from src.calculator.build_calculator import calculate_build_stats

# Load PoB build
build_path = "tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml"
with open(build_path, "r", encoding="utf-8") as f:
    xml_content = f.read()

pob_data = parse_xml(xml_content)
pob_section = pob_data.get("PathOfBuilding2", {})

# Extract components (reuse for all tests)
build_section = pob_section.get("Build", {})
char_class = _extract_character_class(build_section)
level = _extract_level(build_section)
passive_nodes = _extract_passive_nodes(pob_section)
all_skills = _extract_skills(pob_section)
items = _extract_items(pob_data)
config = _extract_config(pob_section)

print(f"Testing {len(all_skills)} skills individually...\n")

# Test each skill alone
for i, skill in enumerate(all_skills, 1):
    build = BuildData(
        character_class=char_class,
        level=level,
        passive_nodes=set(list(passive_nodes)[:10]),  # Use fewer passives for speed
        skills=[skill],
        items=items,
        config=config
    )

    try:
        stats = calculate_build_stats(build)
        print(f"[OK] Skill {i}: {skill.name} - DPS={stats.total_dps:.2f}")
    except Exception as e:
        print(f"[FAIL] Skill {i}: {skill.name}")
        print(f"  Error: {str(e)[:100]}")
        if "pairs" in str(e):
            print(f"  WARNING: This skill triggers the Common.lua:408 error!")

print("\n=== Testing combinations ===")
# Test first 5
try:
    build = BuildData(char_class=char_class, level=level, passive_nodes=set(list(passive_nodes)[:10]), skills=all_skills[:5], items=items, config=config)
    stats = calculate_build_stats(build)
    print(f"[OK] Skills 1-5: DPS={stats.total_dps:.2f}")
except Exception as e:
    print(f"[FAIL] Skills 1-5: {str(e)[:80]}")

# Test all 9
try:
    build = BuildData(char_class=char_class, level=level, passive_nodes=set(list(passive_nodes)[:10]), skills=all_skills, items=items, config=config)
    stats = calculate_build_stats(build)
    print(f"[OK] All 9 skills: DPS={stats.total_dps:.2f}")
except Exception as e:
    print(f"[FAIL] All 9 skills: {str(e)[:80]}")
