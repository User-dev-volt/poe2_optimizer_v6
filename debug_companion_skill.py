"""Debug the Companion skill that causes the crash."""

from src.parsers.xml_utils import parse_xml
from src.parsers.pob_parser import _extract_skills

# Load PoB build
build_path = "tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml"
with open(build_path, "r", encoding="utf-8") as f:
    xml_content = f.read()

pob_data = parse_xml(xml_content)
pob_section = pob_data.get("PathOfBuilding2", {})

# Extract skills
all_skills = _extract_skills(pob_section)

# Get Skill 9 (Companion)
companion_skill = all_skills[8]  # 0-indexed

print("=== Problematic Skill Details ===")
print(f"Name: {companion_skill.name}")
print(f"skill_id: {companion_skill.skill_id}")
print(f"level: {companion_skill.level}")
print(f"quality: {companion_skill.quality}")
print(f"enabled: {companion_skill.enabled}")
print(f"support_gems: {companion_skill.support_gems}")

print("\n=== Hypothesis ===")
print("This is a minion/summon skill. PoB's calcs.initEnv() might expect")
print("minion-related tables that we haven't initialized in MinimalCalc.lua")
print("\nChecking MinimalCalc.lua for minion support...")

# Check if MinimalCalc has minion stubs
with open("src/calculator/MinimalCalc.lua", "r", encoding="utf-8") as f:
    lua_content = f.read()
    if "data.minions" in lua_content:
        print("- data.minions is initialized")
    else:
        print("- data.minions NOT found (might be the issue!)")

    if "data.spectres" in lua_content:
        print("- data.spectres is initialized")
    else:
        print("- data.spectres NOT found")

print("\n=== Solution ===")
print("MinimalCalc.lua needs proper minion table initialization for SummonBeastPlayer")
