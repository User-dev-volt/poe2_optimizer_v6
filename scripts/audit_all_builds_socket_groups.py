"""
Audit all 15 realistic builds to check mainSocketGroup settings.
Identify which socket groups have damaging skills vs buff/minion skills.
"""
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.parsers.xml_utils import parse_xml
from src.parsers.pob_parser import _extract_skills, _is_minion_skill

# List of all 15 realistic builds
ALL_BUILDS = [
    # Weapon builds (4) - Working
    "deadeye_lightning_arrow_76",
    "warrior_earthquake_89",
    "warrior_spear_45",
    "warrior_spear_71",

    # Spell/DOT/Totem builds (11) - Need verification
    "bloodmage_remnants_95",
    "gemling_frost_mage_100",
    "witch_frost_mage_91",
    "titan_totem_90",
    "warrior_ballista_93",
    "lich_frost_mage_90",
    "lich_storm_mage_90",
    "ritualist_lightning_spear_96",
    "titan_infernal_cry_72",
    "witch_essence_drain_86",
    "titan_falling_thunder_99",
]

# Known damaging skill types
DAMAGING_KEYWORDS = [
    "bolt", "arrow", "spear", "ball", "blast", "strike", "slam", "throw",
    "shot", "storm", "fire", "ice", "frost", "lightning", "chaos", "drain",
    "barrage", "nova", "wave", "pulse", "thunder", "earthquake", "shockwave"
]

# Known buff/support skills (non-damaging)
BUFF_KEYWORDS = [
    "offering", "stance", "aura", "banner", "blasphemy", "curse",
    "presence", "effigy", "totem", "ritual", "blessing"
]

def is_likely_damaging_skill(skill_name: str, gem_names: list) -> str:
    """Categorize skill as damaging, buff, minion, or unknown."""
    name_lower = skill_name.lower()
    gems_lower = [g.lower() for g in gem_names]

    # Check for minion skills
    if any("minion" in g or "skeletal" in g for g in gems_lower):
        return "MINION"

    # Check for buff skills
    if any(kw in name_lower for kw in BUFF_KEYWORDS):
        return "BUFF"

    # Check for damaging skills
    if any(kw in name_lower for kw in DAMAGING_KEYWORDS):
        return "DAMAGE"

    # Check gem names for damage indicators
    if any(any(kw in g for kw in DAMAGING_KEYWORDS) for g in gems_lower):
        return "DAMAGE"

    # Check gem names for buffs
    if any(any(kw in g for kw in BUFF_KEYWORDS) for g in gems_lower):
        return "BUFF"

    return "UNKNOWN"

def audit_build(build_name: str):
    """Audit a single build's mainSocketGroup and skills."""
    fixture_path = project_root / "tests" / "fixtures" / "realistic_builds" / f"{build_name}.xml"

    if not fixture_path.exists():
        return {"error": f"File not found: {fixture_path}"}

    xml_str = fixture_path.read_text(encoding='utf-8')
    data = parse_xml(xml_str)
    pob_root = data.get('PathOfBuilding2') or data.get('PathOfBuilding')

    # Get mainSocketGroup
    build_section = pob_root.get('Build', {})
    main_socket_group = int(build_section.get('@mainSocketGroup', '1'))

    # Get Skills section
    skills_section = pob_root.get('Skills', {})
    skill_set = skills_section.get('SkillSet', {})

    # Handle if SkillSet is a list
    if isinstance(skill_set, list):
        skill_set = skill_set[0] if skill_set else {}

    skills = skill_set.get('Skill', [])
    if isinstance(skills, dict):
        skills = [skills]

    # Extract skills using parser
    extracted_skills = _extract_skills(pob_root)

    # Get main skill details
    main_skill_xml = skills[main_socket_group - 1] if main_socket_group <= len(skills) else None

    if main_skill_xml:
        enabled = main_skill_xml.get('@enabled', 'true')
        gems = main_skill_xml.get('Gem', [])
        if isinstance(gems, dict):
            gems = [gems]
        gem_names = [g.get('@nameSpec', 'Unknown') for g in gems if isinstance(g, dict)]
        main_skill_name = gem_names[0] if gem_names else "Unknown"

        # Categorize
        category = is_likely_damaging_skill(main_skill_name, gem_names)
    else:
        enabled = "N/A"
        gem_names = []
        main_skill_name = "NOT FOUND"
        category = "ERROR"

    # Check if extracted
    extracted_skill_names = [s.name for s in extracted_skills if s.enabled]
    main_skill_extracted = any(main_skill_name in name for name in extracted_skill_names) if main_skill_name != "Unknown" else False

    return {
        "build": build_name,
        "mainSocketGroup": main_socket_group,
        "total_xml_skills": len(skills),
        "total_extracted_skills": len(extracted_skills),
        "main_skill_name": main_skill_name,
        "main_skill_enabled": enabled,
        "main_skill_category": category,
        "main_skill_extracted": main_skill_extracted,
        "all_gem_names": gem_names,
        "extracted_skills": extracted_skill_names[:5]  # First 5 for reference
    }

def main():
    """Audit all builds and generate report."""
    print("=" * 100)
    print("AUDIT: All 15 Realistic Builds - mainSocketGroup Settings")
    print("=" * 100)
    print()

    results = []
    for build_name in ALL_BUILDS:
        result = audit_build(build_name)
        results.append(result)

    # Print summary table
    print(f"{'Build Name':<30} {'MSG':<4} {'Main Skill':<25} {'Cat':<8} {'Extr?':<6} {'#XML':<5} {'#Ext':<5}")
    print("-" * 100)

    for r in results:
        if "error" in r:
            print(f"{r.get('build', 'Unknown'):<30} ERROR: {r['error']}")
            continue

        build = r['build'][:29]
        msg = str(r['mainSocketGroup'])
        main_skill = r['main_skill_name'][:24]
        cat = r['main_skill_category']
        extr = "YES" if r['main_skill_extracted'] else "NO"
        xml_count = str(r['total_xml_skills'])
        ext_count = str(r['total_extracted_skills'])

        # Color code based on category
        marker = ""
        if cat == "DAMAGE":
            marker = "[OK]"
        elif cat == "BUFF" or cat == "MINION":
            marker = "[FIX]"
        else:
            marker = "[?]"

        print(f"{build:<30} {msg:<4} {main_skill:<25} {cat:<8} {extr:<6} {xml_count:<5} {ext_count:<5} {marker}")

    print()
    print("=" * 100)
    print("LEGEND:")
    print("  MSG = mainSocketGroup (socket group selected for DPS calculation)")
    print("  Cat = Category: DAMAGE (good), BUFF/MINION (needs fix), UNKNOWN (needs investigation)")
    print("  Extr? = Was main skill extracted by parser? (NO means minion skill filtered out)")
    print("  #XML = Total skills in XML, #Ext = Total skills extracted by parser")
    print("=" * 100)
    print()

    # Count issues
    needs_fix = [r for r in results if r.get('main_skill_category') in ['BUFF', 'MINION']]
    needs_check = [r for r in results if r.get('main_skill_category') == 'UNKNOWN']
    ok = [r for r in results if r.get('main_skill_category') == 'DAMAGE']

    print(f"Summary:")
    print(f"  [OK] DAMAGE: {len(ok)} builds")
    print(f"  [FIX] BUFF/MINION: {len(needs_fix)} builds")
    print(f"  [?] UNKNOWN: {len(needs_check)} builds")
    print()

    if needs_fix:
        print("Builds needing mainSocketGroup fix:")
        for r in needs_fix:
            print(f"  - {r['build']}: {r['main_skill_name']} ({r['main_skill_category']})")
            print(f"    Suggested: Find damaging skill in extracted list: {r['extracted_skills']}")

    if needs_check:
        print("\nBuilds needing investigation:")
        for r in needs_check:
            print(f"  - {r['build']}: {r['main_skill_name']} - Check if damaging or buff")

if __name__ == "__main__":
    main()
