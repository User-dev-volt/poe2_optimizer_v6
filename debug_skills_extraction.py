"""Debug skills extraction from PoB XML."""

from src.parsers.xml_utils import parse_xml
from src.parsers.pob_parser import _extract_skills
import json

# Load real PoB build
build_path = "tests/fixtures/realistic_builds/deadeye_lightning_arrow_76.xml"
print(f"Analyzing skills from: {build_path}\n")

with open(build_path, "r", encoding="utf-8") as f:
    xml_content = f.read()

pob_data = parse_xml(xml_content)
pob_section = pob_data.get("PathOfBuilding2", {})

# Extract skills
skills = _extract_skills(pob_section)

print(f"Extracted {len(skills)} skills:\n")
for i, skill in enumerate(skills, 1):
    print(f"Skill {i}:")
    print(f"  name: {skill.name}")
    print(f"  skill_id: {skill.skill_id}")
    print(f"  level: {skill.level}")
    print(f"  quality: {skill.quality}")
    print(f"  enabled: {skill.enabled}")
    print(f"  support_gems: {len(skill.support_gems)} supports")
    if skill.support_gems:
        for j, support in enumerate(skill.support_gems, 1):
            print(f"    Support {j}: {support}")
    print()

# Check for potential issues
print("\n=== POTENTIAL ISSUES ===")
for i, skill in enumerate(skills, 1):
    if not skill.skill_id:
        print(f"⚠️ Skill {i} ({skill.name}) has no skill_id")
    if not skill.enabled:
        print(f"⚠️ Skill {i} ({skill.name}) is disabled")
    if skill.support_gems:
        for j, support in enumerate(skill.support_gems, 1):
            if not isinstance(support, dict):
                print(f"⚠️ Skill {i} support {j} is not a dict: {type(support)}")
            elif 'skillId' not in support:
                print(f"⚠️ Skill {i} support {j} missing skillId: {support}")
