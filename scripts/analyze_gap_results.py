"""Analyze gap analysis results and extract skill information.

This script:
1. Reads the validation results JSON
2. Reads one sample XML from each build to get skill information
3. Creates a categorized summary of failures
"""

import json
from pathlib import Path
import sys

# Add project root
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from src.parsers.xml_utils import parse_xml


def get_skill_info_from_xml(xml_path: Path):
    """Extract main skill information from build XML."""
    try:
        xml_str = xml_path.read_text(encoding='utf-8')
        data = parse_xml(xml_str)

        pob_root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
        skills_section = pob_root.get("Skills", {})

        # Get skill groups
        skill_groups = skills_section.get("SkillSet", {}).get("SkillGroup", [])
        if isinstance(skill_groups, dict):
            skill_groups = [skill_groups]

        main_skills = []
        for group in skill_groups:
            # Get the first skill gem in each group (main skill)
            gems = group.get("Gem", [])
            if isinstance(gems, dict):
                gems = [gems]

            for gem in gems:
                if gem.get("@enabled") != "false":
                    skill_name = gem.get("@nameSpec", gem.get("@skillId", "Unknown"))
                    skill_id = gem.get("@skillId")
                    if skill_id and not skill_id.endswith("Support"):
                        main_skills.append({
                            "name": skill_name,
                            "id": skill_id,
                            "level": gem.get("@level", "1")
                        })
                        break  # Only get first active skill from each group

        return main_skills
    except Exception as e:
        return [{"name": "Error", "id": str(e), "level": "0"}]


def categorize_skill_type(skill_name: str, skill_id: str = None):
    """Categorize skill by type based on name patterns."""
    name_lower = skill_name.lower()

    # Attack skills
    if any(word in name_lower for word in ["arrow", "strike", "slam", "shot", "throw", "spear", "ballista"]):
        # Check if it's actually a spell version
        if "lightning spear" in name_lower or "spectral throw" in name_lower:
            return "spell"
        return "attack"

    # DOT skills
    if any(word in name_lower for word in ["remnants", "essence drain", "poison", "bleed", "ignite"]):
        return "dot"

    # Spell skills
    if any(word in name_lower for word in ["mage", "frost", "storm", "fireball", "ice", "lightning"]):
        return "spell"

    # Minion skills
    if any(word in name_lower for word in ["minion", "summon", "zombie", "skeleton"]):
        return "minion"

    # Totem/trap/mine
    if any(word in name_lower for word in ["totem", "trap", "mine"]):
        return "totem/trap/mine"

    # Warcry
    if "cry" in name_lower or "shout" in name_lower:
        return "warcry"

    # Fallback
    return "unknown"


def main():
    """Main analysis function."""
    # Load results JSON
    results_path = repo_root / "docs/validation/realistic-validation-results.json"
    with open(results_path) as f:
        results_data = json.load(f)

    # Builds directory
    builds_dir = repo_root / "tests/fixtures/realistic_builds"

    # Analyze each build
    analysis = []
    for result in results_data["results"]:
        build_name = result["build_name"]
        xml_path = builds_dir / f"{build_name}.xml"

        # Get skill info
        skills = get_skill_info_from_xml(xml_path)
        main_skill = skills[0] if skills else {"name": "Unknown", "id": "Unknown", "level": "0"}

        # Categorize
        skill_type = categorize_skill_type(main_skill["name"], main_skill.get("id"))

        # Determine success/failure
        has_dps = result["baseline_dps"] > 0
        has_error = result["status"] == "error"

        analysis.append({
            "build_name": build_name,
            "skill_name": main_skill["name"],
            "skill_type": skill_type,
            "status": result["status"],
            "has_dps": has_dps,
            "baseline_dps": result["baseline_dps"],
            "pre_calc_dps": result.get("pre_calc_dps", 0),
            "error": result.get("error", None)
        })

    # Print summary
    print("\n" + "="*80)
    print("GAP ANALYSIS - BUILD SKILL CATEGORIZATION")
    print("="*80)
    print(f"\n{'Build':<35} {'Skill':<30} {'Type':<15} {'DPS':<10} {'Status'}")
    print("-"*80)

    for item in analysis:
        dps_str = f"{item['baseline_dps']:.1f}" if item['has_dps'] else "0"
        status_icon = "OK" if item['has_dps'] else ("ERROR" if item['status'] == "error" else "FAIL")

        print(f"{item['build_name']:<35} {item['skill_name'][:28]:<30} {item['skill_type']:<15} {dps_str:<10} {status_icon}")

    # Categorize failures
    print("\n" + "="*80)
    print("FAILURE CATEGORIZATION")
    print("="*80)

    categories = {}
    for item in analysis:
        if not item['has_dps'] or item['status'] == "error":
            cat = item['skill_type']
            if item['status'] == "error":
                cat = item['skill_type'] + " (error)"

            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)

    for category, items in sorted(categories.items()):
        print(f"\n{category.upper()}: {len(items)} builds")
        for item in items:
            error_note = f" - {item['error'][:60]}..." if item.get('error') else ""
            print(f"  - {item['build_name']}: {item['skill_name']}{error_note}")

    # Success breakdown
    print("\n" + "="*80)
    print("SUCCESS BREAKDOWN")
    print("="*80)

    success_items = [item for item in analysis if item['has_dps']]
    print(f"\nBuilds with DPS > 0: {len(success_items)}/15 ({len(success_items)/15*100:.1f}%)")
    for item in success_items:
        print(f"  - {item['build_name']}: {item['skill_name']} ({item['skill_type']}) = {item['baseline_dps']:.1f} DPS")


if __name__ == "__main__":
    main()
