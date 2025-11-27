"""Generate corpus manifest from parity builds directory.

Inventories all builds in tests/fixtures/parity_builds/ and creates
a comprehensive manifest with metadata extracted from each XML file.

Output: tests/fixtures/optimization_corpus/corpus_manifest.json
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsers.pob_parser import parse_pob_code
from src.parsers.xml_utils import parse_xml


def extract_build_metadata(xml_path: Path) -> Dict:
    """Extract metadata from a build XML file.

    Args:
        xml_path: Path to XML build file

    Returns:
        Dictionary with build metadata
    """
    try:
        # Read XML file
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        # Parse XML
        data = parse_xml(xml_content)

        # Extract from PathOfBuilding2 or PathOfBuilding root
        pob_root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
        if not pob_root:
            return None

        build_section = pob_root.get("Build", {})

        # Extract metadata
        character_class = build_section.get("@className", "Unknown")
        level = int(build_section.get("@level", 0))
        ascendancy = build_section.get("@ascendClassName", "None")

        # Extract passive tree nodes
        tree_section = pob_root.get("Tree", {})
        spec = tree_section.get("Spec", {})
        nodes_str = spec.get("@nodes", "")

        # Count allocated nodes
        allocated_points = 0
        if nodes_str:
            node_ids = [n.strip() for n in nodes_str.split(",") if n.strip()]
            allocated_points = len(node_ids)

        # Calculate unallocated points (level-1 total, minus allocated)
        # In PoE2: Level 1 = 0 points, each level gives 1 point
        total_points = level - 1
        unallocated_points = max(0, total_points - allocated_points)

        return {
            "filename": xml_path.name,
            "character_class": character_class,
            "level": level,
            "ascendancy": ascendancy,
            "allocated_points": allocated_points,
            "unallocated_points": unallocated_points,
            "total_points_available": total_points,
            "build_name": build_section.get("@buildName", ""),
            "tree_version": build_section.get("@targetVersion", "0_1")
        }

    except Exception as e:
        print(f"Error parsing {xml_path.name}: {e}")
        return None


def generate_corpus_manifest():
    """Generate corpus manifest from all parity builds."""

    # Paths
    project_root = Path(__file__).parent.parent
    parity_builds_dir = project_root / "tests" / "fixtures" / "parity_builds"
    output_dir = project_root / "tests" / "fixtures" / "optimization_corpus"
    output_file = output_dir / "corpus_manifest.json"

    print(f"Scanning builds in: {parity_builds_dir}")
    print(f"Output will be written to: {output_file}\n")

    # Find all XML files
    xml_files = sorted(parity_builds_dir.glob("*.xml"))
    print(f"Found {len(xml_files)} XML build files\n")

    # Extract metadata from each build
    builds = []
    for xml_file in xml_files:
        print(f"Processing: {xml_file.name}...")
        metadata = extract_build_metadata(xml_file)

        if metadata:
            # Generate build_id from filename
            build_id = xml_file.stem  # filename without extension
            metadata["build_id"] = build_id
            builds.append(metadata)
            print(f"  [OK] {metadata['character_class']} Level {metadata['level']} - "
                  f"{metadata['allocated_points']} allocated, {metadata['unallocated_points']} free")
        else:
            print(f"  [FAIL] Failed to parse")

    # Calculate summary statistics
    class_counts = {}
    level_ranges = {"1-30": 0, "31-60": 0, "61-90": 0, "91-100": 0}
    ascendancy_counts = {}

    for build in builds:
        # Count classes
        char_class = build['character_class']
        class_counts[char_class] = class_counts.get(char_class, 0) + 1

        # Count level ranges
        level = build['level']
        if level <= 30:
            level_ranges["1-30"] += 1
        elif level <= 60:
            level_ranges["31-60"] += 1
        elif level <= 90:
            level_ranges["61-90"] += 1
        else:
            level_ranges["91-100"] += 1

        # Count ascendancies
        asc = build['ascendancy']
        if asc and asc != "None":
            ascendancy_counts[asc] = ascendancy_counts.get(asc, 0) + 1

    # Create manifest
    manifest = {
        "version": "1.0",
        "created": "2025-11-01",
        "description": "Inventory of all parity builds from tests/fixtures/parity_builds/",
        "purpose": "Epic 2 validation corpus - baseline stats will be added by Task 5",
        "source_directory": "tests/fixtures/parity_builds/",
        "total_builds": len(builds),
        "summary": {
            "class_distribution": class_counts,
            "level_distribution": level_ranges,
            "ascendancy_distribution": ascendancy_counts,
            "builds_with_unallocated_points": sum(1 for b in builds if b['unallocated_points'] > 0)
        },
        "builds": builds
    }

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write manifest
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Corpus Manifest Generated Successfully!")
    print(f"{'='*60}")
    print(f"Total builds: {len(builds)}")
    print(f"\nClass Distribution:")
    for char_class, count in sorted(class_counts.items()):
        print(f"  {char_class}: {count}")
    print(f"\nLevel Distribution:")
    for range_name, count in sorted(level_ranges.items()):
        print(f"  {range_name}: {count}")
    print(f"\nBuilds with unallocated points: {manifest['summary']['builds_with_unallocated_points']}")
    print(f"\nOutput saved to: {output_file}")


if __name__ == "__main__":
    generate_corpus_manifest()
