"""Inventory tailored optimization corpus builds

This script inventories Alec's provided tailored builds and creates a manifest
showing what we have and what we still need to generate.

Usage:
    python scripts/inventory_tailored_corpus.py
"""

import sys
from pathlib import Path

# Add project root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

import json
from typing import Dict, List
from src.parsers.xml_utils import parse_xml
from src.models.build_data import BuildData, CharacterClass

def load_build_from_xml_file(xml_path: Path) -> BuildData:
    """Load BuildData from XML file"""
    xml_str = xml_path.read_text(encoding='utf-8')
    data = parse_xml(xml_str)

    pob_root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
    if not pob_root:
        raise ValueError("Missing PathOfBuilding root element")

    build_section = pob_root.get("Build")
    if not build_section:
        raise ValueError("Missing Build section")

    class_name = build_section.get("@className")
    character_class = CharacterClass(class_name) if class_name else CharacterClass.WITCH

    level = int(build_section.get("@level", "90"))
    ascendancy = build_section.get("@ascendClassName")
    if ascendancy == "None":
        ascendancy = None

    tree_section = pob_root.get("Tree", {})
    spec = tree_section.get("Spec", {}) if isinstance(tree_section, dict) else {}
    nodes_str = spec.get("@nodes", "") if isinstance(spec, dict) else ""

    passive_nodes = set()
    if nodes_str:
        try:
            passive_nodes = set(int(node_id.strip()) for node_id in nodes_str.split(",") if node_id.strip())
        except ValueError:
            pass

    return BuildData(
        character_class=character_class,
        level=level,
        ascendancy=ascendancy,
        passive_nodes=passive_nodes,
        items=[],
        skills=[]
    )


def parse_filename(filename: str) -> Dict[str, any]:
    """Parse tailored build filename to extract metadata

    Format: class_category_level_Xpoints.xml
    Example: mercenary_hip_88_10points.xml
    """
    parts = filename.replace('.xml', '').split('_')

    if len(parts) < 4:
        return None

    char_class = parts[0]
    category = parts[1]  # hip, mip, lip
    level = int(parts[2])
    points_str = parts[3]  # "10points"
    unallocated = int(points_str.replace('points', ''))

    category_map = {
        'hip': 'high_improvement_potential',
        'mip': 'medium_improvement_potential',
        'lip': 'low_improvement_potential'
    }

    return {
        'character_class': char_class.capitalize(),
        'category': category_map.get(category, category),
        'level': level,
        'expected_unallocated': unallocated
    }


def main():
    """Inventory tailored corpus"""
    tailored_dir = repo_root / "tests" / "fixtures" / "parity_builds" / "tailored"

    if not tailored_dir.exists():
        print(f"ERROR: Tailored directory not found: {tailored_dir}")
        return

    print("="*60)
    print("TAILORED OPTIMIZATION CORPUS INVENTORY")
    print("="*60)
    print()

    builds = []
    category_counts = {'high_improvement_potential': 0, 'medium_improvement_potential': 0, 'low_improvement_potential': 0}
    class_counts = {}

    xml_files = sorted(tailored_dir.glob("*.xml"))

    print(f"Found {len(xml_files)} builds in tailored corpus\n")

    for xml_path in xml_files:
        filename = xml_path.name
        metadata = parse_filename(filename)

        if not metadata:
            print(f"WARNING: Could not parse filename: {filename}")
            continue

        # Load build to get actual data
        build = load_build_from_xml_file(xml_path)
        allocated = len(build.passive_nodes)

        # Calculate unallocated (level-based formula from PoE2)
        # Level 1 = 0 points, Level 2-100 = 1 point per level
        total_available = max(0, build.level - 1)
        actual_unallocated = total_available - allocated

        build_info = {
            'filename': filename,
            'character_class': metadata['character_class'],
            'category': metadata['category'],
            'level': build.level,
            'ascendancy': build.ascendancy,
            'allocated_points': allocated,
            'expected_unallocated': metadata['expected_unallocated'],
            'actual_unallocated': actual_unallocated,
            'total_available': total_available
        }

        builds.append(build_info)
        category_counts[metadata['category']] += 1
        class_counts[metadata['character_class']] = class_counts.get(metadata['character_class'], 0) + 1

        # Print summary
        match = "[OK]" if actual_unallocated == metadata['expected_unallocated'] else "[MISMATCH]"
        print(f"{match} {filename}")
        print(f"   Class: {metadata['character_class']}, Level: {build.level}, Category: {metadata['category'].upper()}")
        print(f"   Allocated: {allocated}, Unallocated: {actual_unallocated} (expected: {metadata['expected_unallocated']})")
        print()

    print("="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    print()

    print(f"Total builds: {len(builds)}")
    print()

    print("By Category:")
    for cat, count in sorted(category_counts.items()):
        cat_display = cat.replace('_', ' ').title()
        print(f"  {cat_display}: {count}")
    print()

    print("By Class:")
    for cls, count in sorted(class_counts.items()):
        print(f"  {cls}: {count}")
    print()

    print("="*60)
    print("CORPUS COMPLETION STATUS")
    print("="*60)
    print()

    target_hip = 10
    target_mip = 15
    target_lip = 5
    target_optimal = 5
    target_total = target_hip + target_mip + target_lip + target_optimal

    current_hip = category_counts['high_improvement_potential']
    current_mip = category_counts['medium_improvement_potential']
    current_lip = category_counts['low_improvement_potential']
    current_optimal = 0  # Not provided yet

    print(f"High Improvement Potential (HIP):    {current_hip}/{target_hip}  (need {target_hip - current_hip} more)")
    print(f"Medium Improvement Potential (MIP):  {current_mip}/{target_mip}  (need {target_mip - current_mip} more)")
    print(f"Low Improvement Potential (LIP):     {current_lip}/{target_lip}  (have {current_lip - target_lip} extra)")
    print(f"Already Optimal (control):           {current_optimal}/{target_optimal}  (need {target_optimal} more)")
    print()
    print(f"TOTAL: {len(builds)}/{target_total}  (need {target_total - len(builds)} more builds)")
    print()

    # Save manifest
    output_path = tailored_dir / "corpus_inventory.json"
    inventory = {
        'total_builds': len(builds),
        'category_counts': category_counts,
        'class_counts': class_counts,
        'builds': builds,
        'targets': {
            'high_improvement_potential': target_hip,
            'medium_improvement_potential': target_mip,
            'low_improvement_potential': target_lip,
            'already_optimal': target_optimal,
            'total': target_total
        },
        'needs': {
            'high_improvement_potential': max(0, target_hip - current_hip),
            'medium_improvement_potential': max(0, target_mip - current_mip),
            'low_improvement_potential': max(0, target_lip - current_lip),
            'already_optimal': target_optimal
        }
    }

    with open(output_path, 'w') as f:
        json.dump(inventory, f, indent=2)

    print(f"Inventory saved to: {output_path}")
    print()


if __name__ == "__main__":
    main()
